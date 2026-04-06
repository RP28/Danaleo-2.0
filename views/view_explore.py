import dearpygui.dearpygui as dpg
import state
import plot_engine as engine
import theme_manager as tm
import pandas as pd

def _update_and_refresh(sender, app_data, user_data):
    col, iid, ptype, key = user_data
    engine.save_state(col, iid, {key: app_data})
    refresh_plot(ptype, col, iid)

def open_view(column_name):
    if dpg.does_item_exist("explore_window"): dpg.delete_item("explore_window")
    
    with dpg.child_window(tag="explore_window", parent="content_area", width=-1, border=True):
        col_data = state.df_global[column_name]
        all_plots = list(engine.PLOT_CONFIG.keys())
        opts = [p for p in all_plots if p != "Bar Chart (Top N)"] if pd.api.types.is_numeric_dtype(col_data) else ["Bar Chart (Top N)"]
        
        with dpg.group(horizontal=True):
            dpg.add_combo(opts, tag="sel_plot", width=150, default_value=opts[0])
            dpg.bind_item_theme(dpg.add_button(label="Add Plot", callback=lambda: add_plot(dpg.get_value("sel_plot"), column_name)), tm.PRIMARY)

        dpg.add_group(tag="plot_stack")
        
        sessions_data = state.EXPLORE_SESSIONS.get(state.active_session, {}).get(column_name, {})
        for iid, data in sessions_data.items():
            if data.get("type") in engine.PLOT_CONFIG:
                add_plot(data["type"], column_name, iid)

def add_plot(ptype, col, iid=None):
    is_new = iid is None
    iid = iid or dpg.generate_uuid()
    config = engine.PLOT_CONFIG[ptype]
    
    if is_new:
        engine.save_state(col, iid, {"type": ptype})
    
    with dpg.collapsing_header(label=f"{ptype}: {col}", parent="plot_stack", tag=iid, default_open=True):
        if config["controls"]:
            with dpg.group(horizontal=True):
                for ctrl in config["controls"]:
                    ctrl_tag = f"ctrl_{iid}_{ctrl['key']}"
                    current_val = engine.get_state(col, iid, ctrl["key"], ctrl["default"])
                    u_data = (col, iid, ptype, ctrl["key"])
                    
                    if ctrl["type"] == "slider_int":
                        dpg.add_slider_int(label=ctrl["label"], default_value=current_val, tag=ctrl_tag,
                                           min_value=ctrl["min"], max_value=ctrl["max"], width=110,
                                           callback=_update_and_refresh, user_data=u_data)
                    
                    elif ctrl["type"] == "checkbox":
                        dpg.add_checkbox(label=ctrl["label"], default_value=current_val, tag=ctrl_tag,
                                         callback=_update_and_refresh, user_data=u_data)
                    
                    elif ctrl["type"] == "combo":
                        dpg.add_combo(items=ctrl["items"], label=ctrl["label"], default_value=current_val, tag=ctrl_tag, width=100,
                                      callback=_update_and_refresh, user_data=u_data)

        with dpg.group(horizontal=True):
            query_tag = f"q_{iid}"
            dpg.add_input_text(hint="Filter...", tag=query_tag, width=150,
                               default_value=engine.get_state(col, iid, "query", ""))
            dpg.add_button(label="Apply", 
                           callback=lambda s, a, u: _update_and_refresh(s, dpg.get_value(query_tag), u),
                           user_data=(col, iid, ptype, "query"))
        
        dpg.add_group(tag=f"cont_{iid}")
        dpg.bind_item_theme(dpg.add_button(label="Delete", callback=lambda: dpg.delete_item(iid)), tm.DANGER)
        refresh_plot(ptype, col, iid)

def refresh_plot(ptype, col, iid):
    query = engine.get_state(col, iid, "query", "")
    config = engine.PLOT_CONFIG.get(ptype)
    
    try:
        working_df = state.df_global
        data = working_df.query(query)[col].dropna() if query else working_df[col].dropna()
        config["draw_func"](data, col, iid, f"cont_{iid}")
    except Exception as e:
        if dpg.does_item_exist(f"cont_{iid}"):
            dpg.delete_item(f"cont_{iid}", children_only=True)
            dpg.add_text(f"Error: {e}", parent=f"cont_{iid}", color=(255, 100, 100))