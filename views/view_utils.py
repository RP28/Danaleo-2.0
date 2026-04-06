import dearpygui.dearpygui as dpg
import theme_manager as tm

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