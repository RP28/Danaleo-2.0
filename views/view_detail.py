import dearpygui.dearpygui as dpg
import state
import theme_manager as tm
from views import view_explore, view_main
from views.view_utils import confirm_action

def open_view(col):
    state.current_column = col
    if dpg.does_item_exist("col_detail"): dpg.delete_item("col_detail")
    
    with dpg.child_window(tag="col_detail", parent="content_area", width=250, border=True):
        dpg.add_text(f"Column: {col}", color=(180, 220, 255))
        dpg.add_text(f"Type: {state.df_global[col].dtype}")
        
        dpg.add_separator()
        dpg.add_input_text(tag="filter_query", hint="Filter query...", width=-1)
        dpg.bind_item_theme(dpg.add_button(label="Apply Filter", width=-1, 
                                           callback=lambda: confirm_action("Filter", "Filter dataset?", apply_filter)), tm.SECONDARY)
        
        dpg.add_separator()
        with dpg.group(horizontal=True):
            dpg.bind_item_theme(dpg.add_button(label="Explore", callback=lambda: view_explore.open_view(col)), tm.PRIMARY)
            dpg.bind_item_theme(dpg.add_button(label="Drop", callback=lambda: confirm_action("Drop", f"Delete {col}?", drop_col, col)), tm.DANGER)
        
        dpg.add_spacer(height=5)
        dpg.bind_item_theme(dpg.add_button(label="Back", width=-1, callback=lambda: view_main.slide_back()), tm.SECONDARY)

def apply_filter(data):
    query = dpg.get_value("filter_query")
    if query:
        try:
            state.df_global = state.df_global.query(query)  
            view_main.slide_back()
            view_main.build_list()            
        except Exception as e:
            print(f"Filter Error: {e}")

def drop_col(col):
    state.df_global = state.df_global.drop(columns=[col])
    view_main.slide_back()
    view_main.build_list()