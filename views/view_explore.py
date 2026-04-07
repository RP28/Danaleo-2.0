import dearpygui.dearpygui as dpg
import state
import plot_engine as engine
import theme_manager as tm
import pandas as pd

def _on_control_change(sender, app_data, user_data):
    col, iid, ptype, key = user_data
    engine.save_state(col, iid, {key: app_data})
    
    config = engine.PLOT_CONFIG.get(ptype, {})
    if key in config.get("requires_refresh_on_keys", []):
        add_plot(ptype, col, iid)
    else:
        refresh_plot(ptype, col, iid)

def add_plot(ptype, col, iid=None):
    is_new = iid is None
    iid = iid or dpg.generate_uuid()
    config = engine.PLOT_CONFIG[ptype]
    
    if is_new:
        engine.save_state(col, iid, {"type": ptype, "query": "", "comp_queries": [""]})
    
    if not dpg.does_item_exist(iid):
        dpg.add_collapsing_header(label=f"{ptype}: {col}", parent="plot_stack", tag=iid, default_open=True)
    
    dpg.delete_item(iid, children_only=True)

    with dpg.group(parent=iid):
        if config.get("controls"):
            with dpg.group(horizontal=True):
                for ctrl in config["controls"]:
                    val = engine.get_state(col, iid, ctrl["key"], ctrl["default"])
                    u_data = (col, iid, ptype, ctrl["key"])
                    
                    if ctrl["type"] == "checkbox":
                        dpg.add_checkbox(label=ctrl["label"], default_value=val, callback=_on_control_change, user_data=u_data)
                    elif ctrl["type"] == "slider_int":
                        dpg.add_slider_int(label=ctrl["label"], default_value=val, min_value=ctrl["min"], max_value=ctrl["max"], 
                                           width=100, callback=_on_control_change, user_data=u_data)
                    elif ctrl["type"] == "combo":
                        dpg.add_combo(items=ctrl["items"], label=ctrl["label"], default_value=val, 
                                      width=100, callback=_on_control_change, user_data=u_data)

        with dpg.group(horizontal=True):
            q_tag = dpg.generate_uuid()
            dpg.add_input_text(hint="Base Filter...", tag=q_tag, width=150, default_value=engine.get_state(col, iid, "query", ""))
            dpg.bind_item_theme(
                dpg.add_button(label="Apply", callback=lambda: _on_control_change(None, dpg.get_value(q_tag), (col, iid, ptype, "query"))), 
                tm.PRIMARY)

        if "extra_ui" in config:
            config["extra_ui"](col, iid, lambda: add_plot(ptype, col, iid))

        dpg.add_group(tag=f"cont_{iid}")
        dpg.bind_item_theme(dpg.add_button(label="Delete plot", callback=lambda: dpg.delete_item(iid)), tm.DANGER)
        refresh_plot(ptype, col, iid)

def refresh_plot(ptype, col, iid):
    config = engine.PLOT_CONFIG.get(ptype)
    query = engine.get_state(col, iid, "query", "")
    cont_tag = f"cont_{iid}"    
    try:
        data = state.df_global.query(query)[col].dropna() if query else state.df_global[col].dropna()
        config["draw_func"](data, col, iid, cont_tag)
    except Exception as e:
        if dpg.does_item_exist(cont_tag):
            dpg.delete_item(cont_tag, children_only=True)
            dpg.add_text(f"Filter Error: {e}", parent=cont_tag, color=(255, 100, 100))

def open_view(column_name):
    if dpg.does_item_exist("explore_window"): 
        dpg.delete_item("explore_window")
    
    with dpg.child_window(tag="explore_window", parent="content_area", width=-1, border=True):
        col_data = state.df_global[column_name]
        
        opts = []
        if pd.api.types.is_numeric_dtype(col_data):
            opts = [k for k, v in engine.PLOT_CONFIG.items() if v.get("numeric_only")]
        else:
            opts = [k for k, v in engine.PLOT_CONFIG.items() if v.get("categorical_only")]
        
        with dpg.group(horizontal=True):
            dpg.add_combo(opts, tag="sel_plot", width=150, default_value=opts[0])
            dpg.bind_item_theme(dpg.add_button(label="Add Plot", 
                           callback=lambda: add_plot(dpg.get_value("sel_plot"), column_name)), 
                           tm.PRIMARY)

        dpg.add_group(tag="plot_stack")
        
        sessions_data = state.EXPLORE_SESSIONS.get(state.active_session, {}).get(column_name, {})
        for iid, data in sessions_data.items():
            if data.get("type") in engine.PLOT_CONFIG:
                add_plot(data["type"], column_name, iid)