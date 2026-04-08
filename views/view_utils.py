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
def show_session_graph():
    if dpg.does_item_exist("session_graph_win"):
        dpg.delete_item("session_graph_win")
    
    max_time = max((op["time"] for s in state.sessions.values() for op in s.get("operations", [])), default=0)
    infinity_x = max(3000, (max_time * const.SESSION_TREE_X_SCALE) + 500) 
    
    session_y_map = {name: i for i, name in enumerate(state.sessions.keys())}
    total_content_height = (len(state.sessions) * const.SESSION_TREE_Y_SCALE) + (const.SESSION_TREE_MARGIN_Y * 2)
    with dpg.window(label="Session Graph", tag="session_graph_win", width=825, height=525):
        with dpg.child_window(label="GraphScrollRegion", horizontal_scrollbar=True):            
            with dpg.drawlist(width=infinity_x + 100, height=total_content_height):
                
                for name, info in state.sessions.items():
                    y_pos = const.SESSION_TREE_MARGIN_Y + (session_y_map[name] * const.SESSION_TREE_Y_SCALE)
                    ops = info.get("operations", [])
                    parent = info.get("parent")
                    
                    if parent in state.sessions and ops:
                        start_time = ops[0]["time"]
                        p_y_pos = const.SESSION_TREE_MARGIN_Y + (session_y_map[parent] * const.SESSION_TREE_Y_SCALE)
                        p1 = (const.SESSION_TREE_MARGIN_X + (start_time - 1) * const.SESSION_TREE_X_SCALE, p_y_pos)
                        p4 = (const.SESSION_TREE_MARGIN_X + start_time * const.SESSION_TREE_X_SCALE, y_pos)
                        p2 = (p1[0] + const.SESSION_TREE_X_SCALE * 0.6, p1[1])
                        p3 = (p4[0] - const.SESSION_TREE_X_SCALE * 0.6, p4[1])
                        dpg.draw_bezier_cubic(p1, p2, p3, p4, color=(150, 150, 150, 150), thickness=2)

                    for i in range(len(ops)):
                        curr_op = ops[i]
                        px = const.SESSION_TREE_MARGIN_X + (curr_op["time"] * const.SESSION_TREE_X_SCALE)
                        py = y_pos
                        if i < len(ops) - 1:
                            next_op = ops[i+1]
                            nx = const.SESSION_TREE_MARGIN_X + (next_op["time"] * const.SESSION_TREE_X_SCALE)
                            dpg.draw_line((px, py), (nx, py), color=(200, 200, 200, 255), thickness=2)
                        else:
                            dpg.draw_line((px, py), (infinity_x, py), color=(100, 100, 100, 100), thickness=2)
                        dpg.draw_circle((px, py), 6, fill=(50, 150, 255, 255), color=(255, 255, 255, 255))                        
                        dpg.draw_text((px - 15, py + 10), _get_node_text(curr_op, name), size=13)

def _get_node_text(info, name):
    match info["type"]:
        case "created session":
            return f"Created {name}"
        case "filter":
            return f"Queried {info['query']}"
        case "drop_col":
            return f"Dropped {info['column']}"
        case _:
            return info["type"]