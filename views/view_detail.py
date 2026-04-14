import dearpygui.dearpygui as dpg
import state
import theme_manager as tm
from views import view_explore, view_main
from views.view_utils import confirm_action, show_plot_zoom
import constants as const
import json
import engines.data_engine as engine
import pandas as pd

def open_view(col):
    state.current_column = col
    if dpg.does_item_exist("col_detail"): dpg.delete_item("col_detail")
    
    with dpg.child_window(tag="col_detail", parent="content_area", width=300, border=True):
        dpg.add_text(f"Column: {col}", color=(180, 220, 255))
        dpg.add_text(f"Type: {state.df_global[col].dtype}")

        with dpg.collapsing_header(label="Basic Stats", default_open=False):
            stats = state.df_global[col].describe(include="all").to_dict()
            for stat_name, stat_value in stats.items():
                dpg.add_text(f"{stat_name}: {stat_value}")

        with dpg.collapsing_header(label="Sample Data", default_open=False):
            dpg.add_input_text(label="Total values", 
                               on_enter=True, 
                               callback=_load_unique_values_sample, 
                               default_value="10",
                               width=50)
            dpg.add_group(tag="column_unique_values_sample")
            _load_unique_values_sample(None, "10")
        
        dpg.add_separator()
        ops = []
        if pd.api.types.is_numeric_dtype(state.df_global[col]):
            ops = [k for k,v in engine.get_data_config().items() if v["is_for_numeric"]]
        else:
            ops = [k for k,v in engine.get_data_config().items() if v["is_for_categorical"]]
        ops = ops + ["None"]
        dpg.add_combo(label="Operations", items=ops, width=150, default_value="None", callback=_render_operation_ui)
        dpg.add_group(tag="operation_params", horizontal=False)
        
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.bind_item_theme(dpg.add_button(label="Explore", callback=lambda: view_explore.open_explore(col)), tm.PRIMARY)
            dpg.bind_item_theme(dpg.add_button(label="Drop", callback=lambda: confirm_action("Drop", f"Delete {col}?", drop_col, col)), tm.DANGER)
        
        dpg.add_spacer(height=5)
        dpg.bind_item_theme(dpg.add_button(label="Back", width=-1, callback=lambda: view_main.slide_back()), tm.SECONDARY)

        saved_plt_infos = state.saved_plots.get(state.active_session, {}).get(col, {})
        export_plt_infos = state.plots_to_be_exported.items()
        if (len(saved_plt_infos) != 0 or len(export_plt_infos) != 0):
            dpg.add_separator()
            with dpg.child_window(label="Saved plots", width=-1, height=-1, border=True):
                
                if len(saved_plt_infos) != 0:
                    dpg.add_text("Saved Plots", color=(100, 200, 255))
                    for plt_info in saved_plt_infos:
                        dpg.add_button(label=plt_info["name"], 
                                    width=const.BUTTON_WIDTH, 
                                    callback=lambda s, a, u: show_plot_zoom(u), 
                                    user_data=plt_info["data"])
                dpg.add_separator()
                plts_to_be_saved = []
                for _, plt_infos in export_plt_infos:
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

def _load_unique_values_sample(sender, app_data):
    if app_data.isdigit():    
        if dpg.does_item_exist("column_unique_values_sample"):
            dpg.delete_item("column_unique_values_sample", children_only=True)
        sample_data = state.df_global[state.current_column].dropna().unique()[:int(app_data)]
        for val in sample_data:
            dpg.add_input_text(default_value=f" - {val}", 
                               readonly=True, 
                               no_spaces=False, 
                               parent="column_unique_values_sample")


def _render_operation_ui(sender, app_data):
    op_type = str(app_data)
    if op_type == "None":
        if dpg.does_item_exist("col_operation_window"):
            dpg.delete_item("col_operation_window")
    else:
        config = engine.get_data_config().get(op_type)

        if dpg.does_item_exist("operation_params"):
            dpg.delete_item("operation_params", children_only=True)
        
        with dpg.child_window(tag="col_operation_window", parent="operation_params", width=-1, height=80, border=True):
            err_tag = None
            param_tags = {}

            for param in config["parameters"]:
                tag_id = f"operation_{param['key']}"
                if param["type"] == "input_text":
                    dpg.add_input_text(label=param["label"], tag=tag_id, width=150)
                    dpg.set_item_height("col_operation_window", 65)
                    param_tags[param["key"]] = tag_id
                elif param["type"] == "checkbox":
                    dpg.add_checkbox(label=param["label"], tag=tag_id)
                    dpg.set_item_height("col_operation_window", 110)
                    param_tags[param["key"]] = tag_id
                    
            if config.get("display_error"):
                err_tag = f"{tag_id}_error"
                dpg.add_group(tag=err_tag)

            def run_op(params):
                try:
                    config["operation_func"](params)                
                except Exception as e:
                    if dpg.does_item_exist(err_tag):
                        dpg.delete_item(err_tag, children_only=True)
                        dpg.set_item_height("col_operation_window", dpg.get_item_height("col_operation_window") + 25)
                        dpg.add_text(f"Error: {str(e)}", 
                                    parent=err_tag, 
                                    color=(255, 100, 100), 
                                    wrap=240)

            dpg.bind_item_theme(
                dpg.add_button(
                    label="Apply", 
                    width=-1, 
                    callback=lambda: confirm_action(
                        op_type,
                        f"Apply {op_type} operation?",
                        run_op,
                        {key: dpg.get_value(tag) for key, tag in param_tags.items()}
                    )), tm.PRIMARY)

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