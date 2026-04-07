import dearpygui.dearpygui as dpg
import pandas as pd
import state

def on_upload(sender, app_data):
    from views import view_main     
    path = list(app_data['selections'].values())[0]
    try:
        state.df_global = pd.read_csv(path) if path.endswith('.csv') else pd.read_excel(path)
        state.sessions = {
            "Base Session": state.df_global.copy()
        }
        state.active_session = "Base Session"

        dpg.hide_item("upload_win")
        dpg.show_item("main_window")
        dpg.set_primary_window("main_window", True)
        view_main.build_list()
    except Exception as e:
        print(f"Log: Error loading file: {e}")

def main():
    dpg.create_context()
    import theme_manager as tm

    with dpg.file_dialog(show=False, callback=on_upload, tag="f_diag", width=500, height=300):
        dpg.add_file_extension(".csv")
        dpg.add_file_extension(".xlsx")

    with dpg.window(tag="upload_win", label="Upload"):
        dpg.add_text("Select a Data File")
        dpg.bind_item_theme(
            dpg.add_button(label="Browse", callback=lambda: dpg.show_item("f_diag")), 
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