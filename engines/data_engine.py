import state
from views import view_main

def get_data_config():
    return {
        "Filter": {
            "parameters": [
                {"type": "input_text", "label": "Query", "key": "query", "default": ""}
            ],
            "display_error": True,
            "operation_func": _apply_filter,
            "is_for_numeric": True,
            "is_for_categorical": True
        },
        "Replace": {
            "parameters": [
                {"type": "input_text", "label": "Old Value", "key": "old_value", "default": ""},
                {"type": "input_text", "label": "New Value", "key": "new_value", "default": ""}
             ],
            "display_error": False,
            "operation_func": _apply_replace,
            "is_for_numeric": True,
            "is_for_categorical": True
        }
    }

def _apply_filter(user_inputs):
    query = user_inputs.get("query", "")
    session = state.active_session
    if query:
        state.df_global = state.df_global.query(query)  
        state.current_time += 1
        state.sessions[session]["data"] = state.df_global.copy()
        state.sessions[session]["operations"].append({
            "type": "filter", 
            "query": query, 
            "time": state.current_time
        })
    view_main.slide_back()
    view_main.build_list()
    

def _apply_replace(user_inputs):
    old_value = user_inputs.get("old_value", "")
    new_value = user_inputs.get("new_value", "")
    session = state.active_session
    col = state.current_column
    if old_value:
        state.df_global[col] = state.df_global[col].replace(old_value, new_value)
        state.current_time += 1
        state.sessions[session]["data"] = state.df_global.copy()
        state.sessions[session]["operations"].append({
            "type": "replace", 
            "old_value": old_value,
            "new_value": new_value,
            "time": state.current_time
        })
    view_main.slide_back()
    view_main.build_list()