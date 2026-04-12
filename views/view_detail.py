import dearpygui.dearpygui as dpg
import state
import theme_manager as tm
from views import view_explore, view_main
from views.view_utils import confirm_action, show_plot_zoom
import constants as const
import json

def open_view(col):
    state.current_column = col
    if dpg.does_item_exist("col_detail"): dpg.delete_item("col_detail")
    
    with dpg.child_window(tag="col_detail", parent="content_area", width=250, border=True):
        dpg.add_text(f"Column: {col}", color=(180, 220, 255))
        dpg.add_text(f"Type: {state.df_global[col].dtype}")

        with dpg.collapsing_header(label="Basic Stats", default_open=False):
            stats = state.df_global[col].describe(include="all").to_dict()
            for stat_name, stat_value in stats.items():
                dpg.add_text(f"{stat_name}: {stat_value}")

        with dpg.collapsing_header(label="Sample Data", default_open=False):
            sample_data = state.df_global[col].dropna().unique()[:10]
            for val in sample_data:
                dpg.add_text(f" - {val}")
        
        dpg.add_separator()
        dpg.add_input_text(tag="filter_query", hint="Filter query (e.g. col > 10)", width=-1)
        dpg.add_text("", tag="query_error_text", color=(255, 100, 100), wrap=240)
        dpg.bind_item_theme(dpg.add_button(label="Apply Filter", width=-1, 
                                           callback=lambda: confirm_action("Filter", "Filter dataset?", apply_filter)), tm.SECONDARY)
        
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.bind_item_theme(dpg.add_button(label="Explore", callback=lambda: view_explore.open_explore(col)), tm.PRIMARY)
            dpg.bind_item_theme(dpg.add_button(label="Drop", callback=lambda: confirm_action("Drop", f"Delete {col}?", drop_col, col)), tm.DANGER)
        
        dpg.add_spacer(height=5)
        dpg.bind_item_theme(dpg.add_button(label="Back", width=-1, callback=lambda: view_main.slide_back()), tm.SECONDARY)

        dpg.add_separator()
        with dpg.child_window(label="Saved plots", width=-1, height=-1, border=True):
            plt_infos = state.saved_plots.get(state.active_session, {}).get(col, {})
            if len(plt_infos) != 0:
                dpg.add_text("Saved Plots", color=(100, 200, 255))
                for plt_info in plt_infos:
                    dpg.add_button(label=plt_info["name"], 
                                   width=const.BUTTON_WIDTH, 
                                   callback=lambda s, a, u: show_plot_zoom(u), 
                                   user_data=plt_info["data"])
            dpg.add_separator()
            plts_to_be_saved = []
            for _, plt_infos in state.plots_to_be_exported.items():
                for plt_info in plt_infos:
                    if plt_info["column"] == col and plt_info["session"] == state.active_session:
                        if plt_info["type"] == "Histogram":
                            plts_to_be_saved.append({
                                "name": plt_info["name"],
                                "type": plt_info["type"],
                                "session": plt_info["session"],
                                "query": plt_info["query"],
                                "bins": plt_info["bins"],
                                "kde": plt_info["kde"]
                            })
                        elif plt_info["type"] == "Boxplot":
                            plts_to_be_saved.append({
                                "name": plt_info["name"],
                                "type": plt_info["type"],
                                "session": plt_info["session"],
                                "query": plt_info["query"],
                                "comp_queries": plt_info["comp_queries"]
                            })
                        elif plt_info["type"] == "Bar Chart (Top N)":
                            plts_to_be_saved.append({
                                "name": plt_info["name"],
                                "type": plt_info["type"],
                                "session": plt_info["session"],
                                "query": plt_info["query"],
                                "topn": plt_info["topn"]
                            })
            if plts_to_be_saved:
                dpg.add_text("Plots to be exported:", color=(255, 200, 100))
                for plt_info in plts_to_be_saved:
                    with dpg.collapsing_header(label=plt_info["name"], default_open=False):
                        dpg.add_text(json.dumps(plt_info, indent=4))
                        dpg.bind_item_theme(
                            dpg.add_button(
                                label="Remove", 
                                callback=lambda s, a, u: _remove_plt_to_be_exported(u, col),
                                user_data={
                                    "name": plt_info["name"],
                                    "column": col,
                                    "session": plt_info["session"]
                                }), tm.DANGER)

def _remove_plt_to_be_exported(target_info, col):
    found = False    
    for time_key in list(state.plots_to_be_exported.keys()):
        plt_list = state.plots_to_be_exported[time_key]        
        for i, info in enumerate(plt_list):
            if (info["name"] == target_info["name"] and 
                info["column"] == target_info["column"] and 
                info["session"] == target_info["session"]):
                plt_list.pop(i)
                found = True                
                if not plt_list:
                    del state.plots_to_be_exported[time_key]
                break  
        if found:
            break

    open_view(col)
    if dpg.does_item_exist("explore_window"):
        view_explore.open_explore(col)

def apply_filter(data):
    query = dpg.get_value("filter_query")
    if dpg.does_item_exist("query_error_text"):
        dpg.set_value("query_error_text", "")
    if query:
        try:
            state.df_global = state.df_global.query(query)  
            state.current_time += 1
            state.sessions[state.active_session]["data"] = state.df_global.copy()
            state.sessions[state.active_session]["operations"].append({
                "type": "filter", 
                "query": query, 
                "time": state.current_time
            })
            view_main.slide_back()
            view_main.build_list()            
        except Exception as e:
            error_msg = f"Filter Error: {str(e)}"
            if dpg.does_item_exist("query_error_text"):
                dpg.set_value("query_error_text", error_msg)

def drop_col(col):
    state.df_global = state.df_global.drop(columns=[col])
    state.current_time += 1
    state.sessions[state.active_session]["data"] = state.df_global.copy()
    state.sessions[state.active_session]["operations"].append({
        "type": "drop_col", 
        "column": col, 
        "time": state.current_time
    })
    view_main.slide_back()
    view_main.build_list()