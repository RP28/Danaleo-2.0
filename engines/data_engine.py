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
                {"type": "input_text", "label": "Old Value(s)", "key": "old_value", "default": ""},
                {"type": "input_text", "label": "New Value(s)", "key": "new_value", "default": ""},
                {"type": "checkbox", "label": "Multiple Replace (use commas)", "key": "is_multiple", "default": False}
            ],
            "display_error": True, 
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
    old_values = user_inputs.get("old_value", "")
    new_values = user_inputs.get("new_value", "")
    is_multiple = user_inputs.get("is_multiple", False)
    session = state.active_session
    col = state.current_column

    if is_multiple:
        old_values = [x.strip() for x in old_values.split(",")]
        new_values = [x.strip() for x in new_values.split(",")]
        if len(old_values) != len(new_values):
            raise ValueError("Old values and New values must have the same count.")
        state.df_global[col] = state.df_global[col].replace(old_values, new_values)
    else:
        state.df_global[col] = state.df_global[col].replace(old_values, new_values)

    state.current_time += 1
    state.sessions[session]["data"] = state.df_global.copy()
    state.sessions[session]["operations"].append({
        "type": "replace", 
        "old_value": old_values,
        "new_value": new_values,
        "is_multiple": is_multiple,
        "time": state.current_time,
        "column": col
    })
    view_main.slide_back()
    view_main.build_list()