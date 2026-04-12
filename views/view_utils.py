import dearpygui.dearpygui as dpg
import theme_manager as tm
import state
import constants as const

def confirm_action(title, message, callback, user_data=None):
    if dpg.does_item_exist("confirm_modal"): dpg.delete_item("confirm_modal")
    
    with dpg.window(label=title, tag="confirm_modal", modal=True, show=True, pos=[400, 300], width=300, no_title_bar=False):
        dpg.add_text(message, wrap=280)
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.bind_item_theme(dpg.add_button(label="Confirm", width=120, 
                                               callback=lambda: (callback(user_data), dpg.delete_item("confirm_modal"))), tm.DANGER)
            dpg.bind_item_theme(dpg.add_button(label="Cancel", width=120, 
                                               callback=lambda: dpg.delete_item("confirm_modal")), tm.SECONDARY)

def input_modal(title, message, callback, user_data, current_names=[]):
    if dpg.does_item_exist("input_modal"): dpg.delete_item("input_modal")
    
    with dpg.window(label=title, tag="input_modal", modal=True, pos=[400, 300], width=300):
        dpg.add_text(message)
        name_input = dpg.add_input_text(hint="Enter name here...")        
        dpg.add_text("", tag="modal_error_msg", color=(255, 100, 100))
        dpg.add_spacer(height=10)
        with dpg.group(horizontal=True):
            dpg.add_button(label="Save", width=120, 
                        callback=lambda: _validate_input_name(callback, dpg.get_value(name_input), user_data, current_names))
            dpg.add_button(label="Cancel", width=120, 
                        callback=lambda: dpg.delete_item("input_modal"))

def _validate_input_name(callback, name_input, user_data, current_names):
    name_input = name_input.strip()
    if not name_input:
        dpg.set_value("modal_error_msg", "Name cannot be empty.")
        return 
    if name_input in current_names:
        dpg.set_value("modal_error_msg", "Name already exists.")
        return 
    callback(name_input, *user_data)
    if dpg.does_item_exist("input_modal"):
        dpg.delete_item("input_modal")

def show_plot_zoom(img_data):
    if dpg.does_item_exist("zoom_window"):dpg.delete_item("zoom_window")
    if not dpg.does_item_exist("main_texture_registry"):
        dpg.add_texture_registry(tag="main_texture_registry")
    texture_tag = dpg.generate_uuid()    
    dpg.add_static_texture(
        width=512, 
        height=384, 
        default_value=img_data, 
        tag=texture_tag, 
        parent="main_texture_registry"
    )    
    with dpg.window(label="Plot Zoom", tag="zoom_window", modal=True, show=True, pos=[200, 150], width=550, height=420):
        dpg.add_image(texture_tag)

def show_session_graph():
    if dpg.does_item_exist("session_graph_win"):
        dpg.delete_item("session_graph_win")    
        
    node_positions = {} 
    session_y_map = {name: i for i, name in enumerate(state.sessions.keys())}
    total_content_height = (len(state.sessions) * const.SESSION_TREE_Y_SCALE) + (const.SESSION_TREE_MARGIN_Y * 2)    
    max_x_reached = 3000
    
    with dpg.window(label="Session Graph", tag="session_graph_win", width=825, height=525):
        with dpg.child_window(label="GraphScrollRegion", horizontal_scrollbar=True):                        
            for name, info in state.sessions.items():
                y_pos = const.SESSION_TREE_MARGIN_Y + (session_y_map[name] * const.SESSION_TREE_Y_SCALE)
                ops = info.get("operations", [])                
                current_x = const.SESSION_TREE_MARGIN_X
                
                for i, curr_op in enumerate(ops):
                    time_x = const.SESSION_TREE_MARGIN_X + (curr_op["time"] * const.SESSION_TREE_X_SCALE)
                    px = max(current_x, time_x)
                    node_positions[(name, i)] = (px, y_pos)                    
                    label = _get_node_text(curr_op, name)
                    text_size = dpg.get_text_size(label)                   
                    current_x = px + text_size[0] + 40 
                    max_x_reached = max(max_x_reached, current_x)

            infinity_x = max_x_reached + 200

            with dpg.drawlist(width=infinity_x + 100, height=total_content_height):
                for name, info in state.sessions.items():
                    y_pos = const.SESSION_TREE_MARGIN_Y + (session_y_map[name] * const.SESSION_TREE_Y_SCALE)
                    ops = info.get("operations", [])
                    parent = info.get("parent")
                    if parent in state.sessions and ops:
                        p_y_pos = const.SESSION_TREE_MARGIN_Y + (session_y_map[parent] * const.SESSION_TREE_Y_SCALE)                        
                        parent_ops = state.sessions[parent].get("operations", [])
                        parent_idx = 0
                        for idx, p_op in enumerate(parent_ops):
                            if p_op["time"] < ops[0]["time"]:
                                parent_idx = idx
                        p1 = node_positions.get((parent, parent_idx), (const.SESSION_TREE_MARGIN_X, p_y_pos))
                        p4 = node_positions[(name, 0)]
                        p2 = (p1[0] + (p4[0] - p1[0]) * 0.5, p1[1])
                        p3 = (p1[0] + (p4[0] - p1[0]) * 0.5, p4[1])
                        dpg.draw_bezier_cubic(p1, p2, p3, p4, color=(150, 150, 150, 150), thickness=2)

                    for i in range(len(ops)):
                        px, py = node_positions[(name, i)]                        
                        if i < len(ops) - 1:
                            nx, ny = node_positions[(name, i+1)]
                            dpg.draw_line((px, py), (nx, py), color=(200, 200, 200, 255), thickness=2)
                        else:
                            dpg.draw_line((px, py), (infinity_x, py), color=(100, 100, 100, 100), thickness=2)
                        dpg.draw_circle((px, py), 6, fill=(50, 150, 255, 255), color=(255, 255, 255, 255))                        
                        dpg.draw_text((px - 15, py + 10), _get_node_text(ops[i], name), size=13)                    

def _get_node_text(info, name):
    match info["type"]:
        case "created session":
            return f"Created {name}"
        case "filter":
            return f"Queried {info['query']}"
        case "replace":
            return f"Replaced {info['old_value']} with {info['new_value']}"
        case "drop_col":
            return f"Dropped {info['column']}"
        case _:
            return info["type"]