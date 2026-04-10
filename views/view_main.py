import pickle
import dearpygui.dearpygui as dpg
import state
import theme_manager as tm
import animation
from views import view_utils
import constants as const

anim = animation.AnimationState()

if not dpg.does_item_exist("save_explorations"):
    with dpg.file_dialog(label="Save As", show=False, callback=lambda s, a: _save_explorations(s, a), 
        tag="save_explorations", width=600, height=400):
        dpg.add_file_extension(".pkl")

def build_list():
    if dpg.does_item_exist("main_layout"): dpg.delete_item("main_layout")
    
    with dpg.group(parent="main_window", tag="main_layout"):
        with dpg.group(horizontal=False):
            dpg.add_text(f"Total records: {len(state.df_global)}")
            with dpg.group(horizontal=True):
                dpg.add_combo(list(state.sessions.keys()), tag="session_sel", width=150, default_value=state.active_session)
                dpg.bind_item_theme(dpg.add_button(label="Load", callback=lambda: switch_session(dpg.get_value("session_sel"))), tm.PRIMARY)
                dpg.add_input_text(tag="new_session_name", hint="Session Name...", width=120)
                dpg.bind_item_theme(dpg.add_button(label="Create Session", callback=save_session), tm.PRIMARY)
                dpg.bind_item_theme(dpg.add_button(label="Session Timeline", callback=view_utils.show_session_graph), tm.SECONDARY)
            dpg.bind_item_theme(dpg.add_button(label="Save Explorations", callback=lambda: dpg.show_item("save_explorations")), tm.SECONDARY)

        dpg.add_separator()
        
        with dpg.group(horizontal=True, tag="content_area"):
            vw = dpg.get_viewport_width()
            initial_indent = (vw - const.BUTTON_WIDTH) // 2
            dpg.add_spacer(width=initial_indent, tag="sliding_spacer") 
            
            with dpg.child_window(tag="col_list", width=const.BUTTON_WIDTH + 30, border=True):
                for col in state.df_global.columns:
                    dpg.bind_item_theme(
                        dpg.add_button(label=col, width=const.BUTTON_WIDTH, 
                                       callback=lambda s, a, u: slide_to_detail(u), user_data=col), 
                        tm.PRIMARY
                    )

def slide_to_detail(col):
    from views import view_detail
    animation.animate_width("sliding_spacer", 0, anim)
    if dpg.does_item_exist("col_detail"): dpg.delete_item("col_detail")
    if dpg.does_item_exist("explore_window"): dpg.delete_item("explore_window")
    view_detail.open_view(col)

def slide_back():
    close_all_subviews()
    vw = dpg.get_viewport_width()
    target_indent = (vw - const.BUTTON_WIDTH) // 2
    animation.animate_width("sliding_spacer", target_indent, anim)

def switch_session(name):
    state.active_session = name
    state.df_global = state.sessions[name]["data"].copy()
    close_all_subviews()
    build_list()

def save_session():
    name = dpg.get_value("new_session_name")
    if name and name.strip():
        state.current_time += 1
        state.sessions[name] = {
            "data": state.df_global.copy(),
            "parent": state.active_session,
            "operations": [{
                "type": "created session",
                "time": state.current_time
            }]
        }
        state.active_session = name
        close_all_subviews() 
        build_list()

def close_all_subviews():
    if dpg.does_item_exist("col_detail"): dpg.delete_item("col_detail")
    if dpg.does_item_exist("explore_window"): dpg.delete_item("explore_window")

def _save_explorations(sender, app_data):
    selected_path = app_data['file_path_name']

    save_data = {
        "sessions": state.sessions,
        "current_time": state.current_time,
        "active_session": state.active_session,
        "current_column": state.current_column,
        "explore_sessions": state.explore_sessions,
        "saved_plots": state.saved_plots,
        "df_global": state.df_global
    }

    with open(selected_path, 'wb') as f: 
        pickle.dump(save_data, f)