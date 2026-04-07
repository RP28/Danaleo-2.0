import io
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
import seaborn as sns
import dearpygui.dearpygui as dpg
import state
import theme_manager as tm

# --- Centralized Registry ---
PLOT_CONFIG = {
    "Histogram": {
        "draw_func": lambda data, col, iid, parent: draw_hist(data, col, iid, parent),
        "controls": [
            {"type": "slider_int", "label": "Bins", "key": "bins", "default": 20, "min": 5, "max": 100},
            {"type": "checkbox", "label": "KDE", "key": "kde", "default": True},
            {"type": "combo", "label": "Color", "key": "color", "default": "skyblue", "items": ["skyblue", "salmon", "lightgreen"]}
        ],
        "requires_refresh_on_keys": ["query"]
    },
    "Boxplot": {
        "draw_func": lambda data, col, iid, parent: draw_box(data, col, iid, parent),
        "controls": [
            {"type": "checkbox", "label": "Compare Mode", "key": "compare_mode", "default": False}
        ],
        "requires_refresh_on_keys": ["compare_mode", "query", "comp_queries"],
        "extra_ui": lambda col, iid, refresh_cb: render_boxplot_ui(col, iid, refresh_cb)
    },
    "Bar Chart (Top N)": {
        "draw_func": lambda data, col, iid, parent: draw_bar(data, col, iid, parent),
        "controls": [
            {"type": "slider_int", "label": "Top N", "key": "topn", "default": 10, "min": 1, "max": 50},
            {"type": "combo", "label": "Palette", "key": "palette", "default": "magma", "items": ["magma", "viridis", "rocket"]}
        ],
        "requires_refresh_on_keys": ["query"]
    }
}

_textures = {}

def get_state(col, iid, key, default):
    return state.EXPLORE_SESSIONS.get(state.active_session, {}).get(col, {}).get(iid, {}).get(key, default)

def save_state(col, iid, data_dict):
    sess = state.active_session
    if not sess: return
    state.EXPLORE_SESSIONS.setdefault(sess, {}).setdefault(col, {}).setdefault(iid, {})
    state.EXPLORE_SESSIONS[sess][col][iid].update(data_dict)

def _on_add_sub_q(sender, app_data, user_data):
    col, iid, input_tag, refresh_cb = user_data
    val = dpg.get_value(input_tag)
    queries = get_state(col, iid, "comp_queries", [])
    queries.append(val)
    save_state(col, iid, {"comp_queries": queries})
    refresh_cb()

def _on_remove_sub_q(sender, app_data, user_data):
    col, iid, index, refresh_cb = user_data
    queries = get_state(col, iid, "comp_queries", [])
    if 0 <= index < len(queries):
        queries.pop(index)
        save_state(col, iid, {"comp_queries": queries})
    refresh_cb()

def render_boxplot_ui(col, iid, refresh_cb):
    if not get_state(col, iid, "compare_mode", False):
        return

    with dpg.group(indent=20):
        dpg.add_text("Sub-plot Refinements:", color=(100, 200, 255))
        comp_queries = get_state(col, iid, "comp_queries", [""])
        
        for idx, q in enumerate(comp_queries):
            with dpg.group(horizontal=True):
                dpg.add_text(f"- {q if q.strip() else 'Base Only'}")
                dpg.bind_item_theme(dpg.add_button(label="Remove", small=True, 
                               callback=_on_remove_sub_q, 
                               user_data=(col, iid, idx, refresh_cb)), tm.DANGER)
        
        comp_in = dpg.generate_uuid()
        with dpg.group(horizontal=True):
            dpg.add_input_text(hint="Add refinement...", tag=comp_in, width=150)
            dpg.add_button(label="Add", 
                           callback=_on_add_sub_q, 
                           user_data=(col, iid, comp_in, refresh_cb))

def draw_box(data, col, iid, parent):
    fig = Figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(111)
    compare_mode = get_state(col, iid, "compare_mode", False)
    comp_queries = get_state(col, iid, "comp_queries", [])
    base_query = get_state(col, iid, "query", "")

    if compare_mode and comp_queries:
        plot_data = {}
        for sub_q in comp_queries:
            parts = [q for q in [base_query, sub_q] if q and q.strip()]
            final_q = " and ".join(f"({q})" for q in parts)
            label = sub_q if sub_q.strip() else "Base"
            try:
                subset = state.df_global.query(final_q)[col].dropna() if final_q else state.df_global[col].dropna()
                if not subset.empty: plot_data[label] = subset
            except: continue
        
        if plot_data:
            combined_df = pd.concat([pd.Series(v.values, name=k) for k, v in plot_data.items()], axis=1)
            sns.boxplot(data=combined_df, ax=ax, palette="Set2")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    else:
        sns.boxplot(x=data, color="salmon", ax=ax)
    
    fig.tight_layout()
    render_to_dpg(fig, iid, parent)

def render_to_dpg(fig, iid, parent):
    buf = io.BytesIO()
    fig.savefig(buf, format='rgba', dpi=80)
    buf.seek(0)
    img_data = np.frombuffer(buf.getvalue(), dtype=np.uint8) / 255.0
    if iid in _textures and dpg.does_item_exist(_textures[iid]):
        dpg.delete_item(_textures[iid])
    tex_tag = dpg.generate_uuid()
    _textures[iid] = tex_tag
    if not dpg.does_item_exist("main_texture_registry"):
        dpg.add_texture_registry(tag="main_texture_registry")
    dpg.add_static_texture(width=512, height=384, default_value=img_data, tag=tex_tag, parent="main_texture_registry")
    if dpg.does_item_exist(parent):
        dpg.delete_item(parent, children_only=True)
        dpg.add_image(tex_tag, width=350, height=260, parent=parent)    
    buf.close()

def draw_hist(data, col, iid, parent):
    fig = Figure(figsize=(6.4, 4.8)); ax = fig.add_subplot(111)
    sns.histplot(data, bins=get_state(col, iid, "bins", 20), kde=get_state(col, iid, "kde", True), ax=ax)
    render_to_dpg(fig, iid, parent)

def draw_bar(data, col, iid, parent):
    fig = Figure(figsize=(6.4, 4.8)); ax = fig.add_subplot(111)
    counts = data.value_counts().head(get_state(col, iid, "topn", 10))
    sns.barplot(x=counts.values, y=counts.index.astype(str), ax=ax)
    fig.tight_layout(); render_to_dpg(fig, iid, parent)