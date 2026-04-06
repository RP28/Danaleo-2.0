import dearpygui.dearpygui as dpg

def create_theme(color):
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (color[0]+20, color[1]+20, color[2]+20, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (color[0]-15, color[1]-15, color[2]-15, 255))
    return theme

PRIMARY = create_theme((55, 55, 60, 255))
SECONDARY = create_theme((70, 70, 75, 255))
DANGER = create_theme((120, 30, 30, 255))