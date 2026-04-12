import dearpygui.dearpygui as dpg
import pandas as pd
import state
import pickle

def _on_upload(sender, app_data):
    from views import view_main     
    path = list(app_data['selections'].values())[0]
    state.df_path = path
    try:
        state.df_global = pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)
        state.active_session = "Base Session"
        state.current_time = 0
        state.sessions = {
            "Base Session": {
                "data": state.df_global.copy(),
                "parent": None,
                "operations": [{
                    "type": "created session",
                    "time": state.current_time
                }]
            }
        }

        dpg.hide_item("upload_win")
        dpg.show_item("main_window")
        dpg.set_primary_window("main_window", True)
        view_main.build_list()
    except Exception as e:
        print(f"Log: Error loading file: {e}")

def _load_explorations(sender, app_data):
    from views import view_main
    selected_path = app_data['file_path_name']
    required_keys = [
        "sessions", "current_time", "active_session", 
        "current_column", "explore_sessions", "saved_plots", 
        "df_global", "plots_to_be_exported", "df_path"
    ]
    try: 
        with open(selected_path, 'rb') as f:
            loaded_data = pickle.load(f)
            for key in required_keys:
                if key not in loaded_data:
                    raise KeyError(f"Missing key in loaded data: {key}")
                
            state.sessions = loaded_data["sessions"]
            state.current_time = loaded_data["current_time"]
            state.active_session = loaded_data["active_session"]
            state.current_column = loaded_data["current_column"]
            state.explore_sessions = loaded_data["explore_sessions"]
            state.saved_plots = loaded_data["saved_plots"]
            state.df_global = loaded_data["df_global"]
            state.plots_to_be_exported = loaded_data["plots_to_be_exported"]
            state.df_path = loaded_data["df_path"]

    except KeyError as ke:
        print(f"Log: Key error loading explorations: {ke}")

    except Exception as e:
        print(f"Log: Error loading explorations: {e}")

    dpg.hide_item("upload_win")
    dpg.show_item("main_window")
    dpg.set_primary_window("main_window", True)
    view_main.build_list()

def main():
    dpg.create_context()
    import theme_manager as tm

    with dpg.file_dialog(show=False, callback=_on_upload, tag="f_diag", width=500, height=300):
        dpg.add_file_extension(".csv")
        dpg.add_file_extension(".xlsx")

    with dpg.file_dialog(show=False, callback=_load_explorations, tag="load_explorations", width=600, height=400):
        dpg.add_file_extension(".pkl")

    with dpg.window(tag="upload_win", label="Upload"):
        dpg.add_text("Select a Data File")
        dpg.bind_item_theme(
            dpg.add_button(label="Browse", callback=lambda: dpg.show_item("f_diag")), 
            tm.PRIMARY
        )
        dpg.bind_item_theme(
            dpg.add_button(label="Load Exploration", callback=lambda: dpg.show_item("load_explorations")), 
            tm.PRIMARY
        )

    with dpg.window(tag="main_window", label="Explorer", show=False, no_scrollbar=True):
        pass

    dpg.create_viewport(title="Danaleo", width=1100, height=700)
    dpg.setup_dearpygui()
    dpg.set_primary_window("upload_win", True)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()