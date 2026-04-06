import io
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
import seaborn as sns
import dearpygui.dearpygui as dpg
import state

# --- Centralized Registry ---
PLOT_CONFIG = {
    "Histogram": {
        "draw_func": lambda data, col, iid, parent: draw_hist(data, col, iid, parent),
        "controls": [
            {"type": "slider_int", "label": "Bins", "key": "bins", "default": 20, "min": 5, "max": 100},
            {"type": "checkbox", "label": "KDE", "key": "kde", "default": True},
            {"type": "combo", "label": "Color", "key": "color", "default": "skyblue", "items": ["skyblue", "salmon", "lightgreen"]}
        ]
    },
    "Boxplot": {
        "draw_func": lambda data, col, iid, parent: draw_box(data, col, iid, parent),
        "controls": []
    },
    "Bar Chart (Top N)": {
        "draw_func": lambda data, col, iid, parent: draw_bar(data, col, iid, parent),
        "controls": [
            {"type": "slider_int", "label": "Top N", "key": "topn", "default": 10, "min": 1, "max": 50},
            {"type": "combo", "label": "Palette", "key": "palette", "default": "magma", "items": ["magma", "viridis", "rocket"]}
        ]
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
        
    dpg.add_static_texture(width=512, height=384, default_value=img_data, 
                           tag=tex_tag, parent="main_texture_registry")
    
    if dpg.does_item_exist(parent):
        dpg.delete_item(parent, children_only=True)
        dpg.add_image(tex_tag, width=350, height=260, parent=parent)    
    buf.close()

def draw_hist(data, col, iid, parent):
    fig = Figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(111)
    sns.histplot(data, 
                 bins=get_state(col, iid, "bins", 20), 
                 kde=get_state(col, iid, "kde", True), 
                 color=get_state(col, iid, "color", "skyblue"),
                 ax=ax)
    render_to_dpg(fig, iid, parent)

def draw_box(data, col, iid, parent):
    fig = Figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(111)
    sns.boxplot(x=data, color="salmon", ax=ax)
    render_to_dpg(fig, iid, parent)

def draw_bar(data, col, iid, parent):
    fig = Figure(figsize=(6.4, 4.8))
    ax = fig.add_subplot(111)
    counts = data.value_counts().head(get_state(col, iid, "topn", 10))
    sns.barplot(x=counts.values, y=counts.index.astype(str), 
                palette=get_state(col, iid, "palette", "magma"), ax=ax)
    fig.tight_layout()
    render_to_dpg(fig, iid, parent)