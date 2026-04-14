import dearpygui.dearpygui as dpg

def _create_theme(color):
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_Button, color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (color[0]+20, color[1]+20, color[2]+20, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (color[0]-15, color[1]-15, color[2]-15, 255))
    return theme

def _get_no_spacer_theme():
    with dpg.theme() as no_spacing_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 0, 0)
    return no_spacing_theme

PRIMARY = _create_theme((55, 55, 60, 255))
SECONDARY = _create_theme((70, 70, 75, 255))
DANGER = _create_theme((120, 30, 30, 255))
NO_SPACE = _get_no_spacer_theme()