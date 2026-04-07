import dearpygui.dearpygui as dpg
import state
import plot_engine as engine
import theme_manager as tm
import pandas as pd

def _update_and_refresh(sender, app_data, user_data):
    col, iid, ptype, key = user_data
    engine.save_state(col, iid, {key: app_data})
    if key in ["compare_mode", "query"]:
        add_plot(ptype, col, iid)
    else:
        refresh_plot(ptype, col, iid)

def _add_comp_query(sender, app_data, user_data):
    col, iid, ptype, input_tag = user_data
    query = dpg.get_value(input_tag)
    current_queries = engine.get_state(col, iid, "comp_queries", [])
    current_queries.append(query)
    engine.save_state(col, iid, {"comp_queries": current_queries})
    add_plot(ptype, col, iid)

def _remove_comp_query(sender, app_data, user_data):
    col, iid, ptype, index = user_data
    current_queries = engine.get_state(col, iid, "comp_queries", [])
    if 0 <= index < len(current_queries):
        current_queries.pop(index)
        engine.save_state(col, iid, {"comp_queries": current_queries})
    add_plot(ptype, col, iid)

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
        engine.save_state(col, iid, {"type": ptype, "comp_queries": [""], "query": ""})
    
    if not dpg.does_item_exist(iid):
        dpg.add_collapsing_header(label=f"{ptype}: {col}", parent="plot_stack", tag=iid, default_open=True)
    dpg.delete_item(iid, children_only=True)

    with dpg.group(parent=iid):
        # Base Controls
        if config["controls"]:
            with dpg.group(horizontal=True):
                for ctrl in config["controls"]:
                    val = engine.get_state(col, iid, ctrl["key"], ctrl["default"])
                    if ctrl["type"] == "checkbox":
                        dpg.add_checkbox(label=ctrl["label"], default_value=val, callback=_update_and_refresh, user_data=(col, iid, ptype, ctrl["key"]))

        # Global Base Filter (Applies to all sub-plots if in compare mode)
        with dpg.group(horizontal=True):
            query_tag = dpg.generate_uuid()
            dpg.add_input_text(hint="Global Filter (Base)...", tag=query_tag, width=200, default_value=engine.get_state(col, iid, "query", ""))
            dpg.add_button(label="Apply Global", callback=lambda s, a, u: _update_and_refresh(s, dpg.get_value(query_tag), u), user_data=(col, iid, ptype, "query"))

        # Comparison Sub-plots
        if ptype == "Boxplot" and engine.get_state(col, iid, "compare_mode", False):
            with dpg.group(indent=20):
                dpg.add_text("Sub-plot Refinements (Relative to Base):", color=(100, 200, 255))
                comp_queries = engine.get_state(col, iid, "comp_queries", [])
                for idx, q in enumerate(comp_queries):
                    with dpg.group(horizontal=True):
                        display_text = q if q.strip() else "Base Filter Only"
                        dpg.add_text(f"- {display_text}")
                        dpg.bind_item_theme(dpg.add_button(label="Remove", small=True, callback=_remove_comp_query, user_data=(col, iid, ptype, idx)), tm.DANGER)
                
                comp_in = dpg.generate_uuid()
                with dpg.group(horizontal=True):
                    dpg.add_input_text(hint="Refine further...", tag=comp_in, width=180)
                    dpg.add_button(label="Add Sub-plot", callback=_add_comp_query, user_data=(col, iid, ptype, comp_in))

        dpg.add_group(tag=f"cont_{iid}")
        dpg.bind_item_theme(dpg.add_button(label="Delete Plot", callback=lambda: dpg.delete_item(iid)), tm.DANGER)
        refresh_plot(ptype, col, iid)

def refresh_plot(ptype, col, iid):
    config = engine.PLOT_CONFIG.get(ptype)
    query = engine.get_state(col, iid, "query", "")
    try:
        data = state.df_global.query(query)[col].dropna() if query else state.df_global[col].dropna()
        config["draw_func"](data, col, iid, f"cont_{iid}")
    except Exception as e:
        if dpg.does_item_exist(f"cont_{iid}"):
            dpg.delete_item(f"cont_{iid}", children_only=True)
            dpg.add_text(f"Error: {e}", parent=f"cont_{iid}", color=(255, 100, 100))