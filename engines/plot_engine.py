import io
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
import seaborn as sns
import dearpygui.dearpygui as dpg
import state
import theme_manager as tm

def get_plot_config():
    return {
        "Histogram": {
            "draw_func": lambda data, col, iid, parent, save_name: draw_hist(data, col, iid, parent, save_name),
            "controls": [
                {"type": "slider_int", "label": "Bins", "key": "bins", "default": 20, "min": 5, "max": 100},
                {"type": "checkbox", "label": "KDE", "key": "kde", "default": True},
                {"type": "combo", "label": "Color", "key": "color", "default": "skyblue", "items": ["skyblue", "salmon", "lightgreen", "gold", "orchid"]}
            ],
            "requires_refresh_on_keys": ["query", "color", "kde"],
            "is_for_numeric": True
        },
        "Boxplot": {
            "draw_func": lambda data, col, iid, parent, save_name: draw_box(data, col, iid, parent, save_name),
            "controls": [
                {"type": "checkbox", "label": "Compare Mode", "key": "compare_mode", "default": False},
                {"type": "combo", "label": "Split By", "key": "split_by", "default": "None", 
                "items": ["None"] + [c for c in state.df_global.columns if not pd.api.types.is_numeric_dtype(state.df_global[c])]},
                {"type": "combo", "label": "Palette", "key": "palette", "default": "Set2", "items": ["Set2", "Paired", "Accent", "Pastel1", "Dark2", "viridis", "rocket"]}
            ],
            "requires_refresh_on_keys": ["compare_mode", "query", "comp_queries", "palette", "split_by"], 
            "extra_ui": lambda col, iid, refresh_cb: render_boxplot_ui(col, iid, refresh_cb),
            "is_for_numeric": True
        },
        "Bar Chart (Top N)": {
            "draw_func": lambda data, col, iid, parent, save_name: draw_bar(data, col, iid, parent, save_name),
            "controls": [
                {"type": "slider_int", "label": "Top N", "key": "topn", "default": 10, "min": 1, "max": 50},
                {"type": "combo", "label": "Palette", "key": "palette", "default": "magma", "items": ["magma", "viridis", "rocket", "mako", "crest"]}
            ],
            "requires_refresh_on_keys": ["query", "palette"],
            "is_for_categorical": True
        }
    }

_textures = {}

def get_state(col, iid, key, default):
    return state.explore_sessions.get(state.active_session, {}).get(col, {}).get(iid, {}).get(key, default)

def save_state(col, iid, data_dict):
    sess = state.active_session
    if not sess: return
    state.explore_sessions.setdefault(sess, {}).setdefault(col, {}).setdefault(iid, {})
    state.explore_sessions[sess][col][iid].update(data_dict)

def _on_add_sub_q(sender, app_data, user_data):
    col, iid, input_tag, error_tag, refresh_cb = user_data
    val = dpg.get_value(input_tag)
    base_query = get_state(col, iid, "query", "")    
    parts = [q for q in [base_query, val] if q and q.strip()]
    final_q = " and ".join(f"({q})" for q in parts)
    try:
        test_data = state.df_global.query(final_q) if final_q else state.df_global
        if test_data.empty:
            dpg.set_value(error_tag, "Filter Error: Query returned no data")
            dpg.show_item(error_tag)
            return 
    except Exception as e:
        dpg.set_value(error_tag, f"Filter Error: {str(e)}")
        dpg.show_item(error_tag)
        return

    dpg.hide_item(error_tag)
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

def _on_auto_split(sender, app_data, user_data):
    col, iid, refresh_cb = user_data
    split_col = get_state(col, iid, "split_by", "None")
    if split_col == "None": return
    
    base_query = get_state(col, iid, "query", "")
    data = state.df_global.query(base_query) if base_query else state.df_global
    unique_vals = data[split_col].dropna().unique().tolist()
    
    new_queries = [f"`{split_col}` == '{v}'" for v in unique_vals]
    save_state(col, iid, {"comp_queries": new_queries})
    refresh_cb()

def render_boxplot_ui(col, iid, refresh_cb):
    if not get_state(col, iid, "compare_mode", False):
        return

    with dpg.group(indent=20):
        split_col = get_state(col, iid, "split_by", "None")
        if split_col != "None":
            dpg.bind_item_theme(dpg.add_button(label=f"Auto-Split by {split_col}", 
                               callback=_on_auto_split, user_data=(col, iid, refresh_cb)), tm.SECONDARY)
            
        dpg.add_text("Sub-plot Refinements:", color=(100, 200, 255))
        comp_queries = get_state(col, iid, "comp_queries", [""])
        
        for idx, q in enumerate(comp_queries):
            with dpg.group(horizontal=True):
                dpg.add_text(f"- {q if q.strip() else 'Base Only'}")
                dpg.bind_item_theme(dpg.add_button(label="Remove", small=True, 
                               callback=_on_remove_sub_q, 
                               user_data=(col, iid, idx, refresh_cb)), tm.DANGER)
        
        comp_in = dpg.generate_uuid()
        err_out = dpg.add_text("", color=(255, 100, 100), show=False)
        with dpg.group(horizontal=True):
            dpg.add_input_text(hint="Add refinement...", tag=comp_in, width=150)
            dpg.bind_item_theme(dpg.add_button(label="Add", 
                           callback=_on_add_sub_q, 
                           user_data=(col, iid, comp_in, err_out, refresh_cb)), tm.PRIMARY)

def draw_box(data, col, iid, parent, save_name=None):
    fig = Figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(111)
    compare_mode = get_state(col, iid, "compare_mode", False)
    comp_queries = get_state(col, iid, "comp_queries", [])
    base_query = get_state(col, iid, "query", "")
    palette_name = get_state(col, iid, "palette", "Set2")

    if compare_mode and comp_queries:
        plot_data = {}
        for sub_q in comp_queries:
            parts = [q for q in [base_query, sub_q] if q and q.strip()]
            final_q = " and ".join(f"({q})" for q in parts)
            label = sub_q if sub_q.strip() else "Base"
            
            subset = state.df_global.query(final_q)[col].dropna() if final_q else state.df_global[col].dropna()
            if subset.empty:
                raise ValueError(f"Sub-query '{label}' returned no data.")
            plot_data[label] = subset
        
        combined_df = pd.concat([pd.Series(v.values, name=k) for k, v in plot_data.items()], axis=1)
        sns.boxplot(data=combined_df, ax=ax, palette=palette_name, orient="h")
    else:
        sns.boxplot(x=data, ax=ax, palette=palette_name)
    
    fig.tight_layout()
    return render_to_dpg(fig, iid, parent, save_name)

def render_to_dpg(fig, iid, parent, save_name=None):
    buf = io.BytesIO()
    fig.savefig(buf, format='rgba', dpi=80)
    buf.seek(0)
    img_data = np.frombuffer(buf.getvalue(), dtype=np.uint8) / 255.0
    if save_name:
        session = state.saved_plots.setdefault(state.active_session, {})        
        column_plots = session.setdefault(state.current_column, [])        
        column_plots.append({"name": save_name, "data": img_data})
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
    return img_data

def draw_hist(data, col, iid, parent, save_name=None):
    fig = Figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(111)
    color = get_state(col, iid, "color", "skyblue")
    kde = get_state(col, iid, "kde", True)
    bins = get_state(col, iid, "bins", 20)
    sns.histplot(data, bins=bins, kde=kde, color=color, ax=ax)
    return render_to_dpg(fig, iid, parent, save_name)

def draw_bar(data, col, iid, parent, save_name=None):
    fig = Figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(111)
    topn = get_state(col, iid, "topn", 10)
    palette = get_state(col, iid, "palette", "magma")
    counts = data.value_counts().head(topn)
    sns.barplot(x=counts.values, y=counts.index.astype(str), palette=palette, ax=ax)
    fig.tight_layout()
    return render_to_dpg(fig, iid, parent, save_name)