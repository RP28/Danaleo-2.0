import state
import nbformat as nbf

def export_to_ipynb(full_path):
    operations_to_export = _get_operations_to_export()
    nb = nbf.v4.new_notebook()
    cells = []
    name = full_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    _add_primary_cells(cells, name)

    for item in operations_to_export:
        if isinstance(item, tuple):
            _add_session_operation(cells, item)
        else:
            _add_plot_operation(cells, item)

    nb.cells = cells
    with open(f"{name}.ipynb", 'w') as f:
        nbf.write(nb, f)

def _get_operations_to_export():
    till_time = 0
    required_session_set = set()
    for k, v in state.plots_to_be_exported.items():
        if k > till_time:
            till_time = k
        session = v[0]["session"]
        required_session_set.add(session)
        if session != "Base Session":
            parent = state.sessions[session]["parent"]
            while parent:
                required_session_set.add(parent)
                parent = state.sessions[parent]["parent"]
    
    till_time += 1
    state_sessions_by_time = {op["time"]: (k, op) 
                              for k,v in state.sessions.items() 
                              if k in required_session_set 
                              for op in v["operations"] 
                              if op["time"] <= till_time}
    
    operations_to_export = []
    for t in range(till_time):
        if t in state_sessions_by_time:
            operations_to_export.append(state_sessions_by_time[t])
        if t in state.plots_to_be_exported:
            for plt_data in state.plots_to_be_exported[t]:
                operations_to_export.append(plt_data)
    
    return operations_to_export

def _add_primary_cells(cells, name):
    cells.append(nbf.v4.new_markdown_cell(f"# Exported Data Exploration: {name}"))
    cells.append(nbf.v4.new_markdown_cell(f"## Loading Data"))
    cells.append(nbf.v4.new_code_cell('''
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns'''))
    cells.append(nbf.v4.new_code_cell(f'''
df = pd.read_csv("{state.df_path}")
df.head()'''))

def _add_session_operation(cells, session_operation):
    session_name, op = session_operation
    data = "df" if session_name == "Base Session" else f"df_{session_name.replace(" ", "_")}"
    match op["type"]:
        case "created session":
            if session_name == "Base Session":
                return
            else:
                parent_data = "df" if state.sessions[session_name]["parent"] == "Base Session" else f"df_{state.sessions[session_name]['parent']}"
                cells.append(nbf.v4.new_code_cell(f'''
df_{session_name} = {parent_data}.copy()'''))
        case "filter":
            cells.append(nbf.v4.new_code_cell(f'''
{data} = {data}.query("{op['query']}")'''))
        case "drop_col":
            cells.append(nbf.v4.new_code_cell(f'''
{data} = {data}.drop(columns=["{op['column']}"])'''))
        case "replace":
            cells.append(nbf.v4.new_code_cell(f'''
{data}["{state.current_column}"] = {data}["{state.current_column}"].replace("{op['old_value']}", "{op['new_value']}")'''))
                
def _add_plot_operation(cells, plot_data):
    data = "df" if plot_data["session"] == "Base Session" else f"df_{plot_data["session"].replace(" ", "_")}"
    code = '''
fig, ax = plt.subplots(figsize=(6.4, 4.8))'''
    match plot_data["type"]:
        case "Histogram":
            if plot_data["query"]:
                code += f'''
sns.histplot({data}.query("{plot_data['query']}")["{plot_data['column']}"].dropna(), bins={plot_data['bins']}, kde={plot_data['kde']}, color="{plot_data['color']}", ax=ax)'''
            else:
                code += f'''
sns.histplot({data}["{plot_data['column']}"].dropna(), bins={plot_data['bins']}, kde={plot_data['kde']}, color="{plot_data['color']}", ax=ax)'''
        case "Boxplot":
            if plot_data["query"]:
                code += f'''
data = {data}.query("{plot_data['query']}")'''
                if plot_data["comp_queries"]:
                    code += f'''
sub_queries = {plot_data['comp_queries']}
plot_data = {{}}
for sub_q in sub_queries:
    plot_data[sub_q if sub_q.strip() else "Base"] = data.query(sub_q)["{plot_data['column']}"].dropna()
combined_df = pd.concat([pd.Series(v.values, name=k) for k, v in plot_data.items()], axis=1)
sns.boxplot(data=combined_df, ax=ax, palette="{plot_data['palette']}", orient="h")'''
                else:
                    code += f'''
sns.boxplot(x=data["{plot_data['column']}"].dropna(), ax=ax, palette="{plot_data['palette']}")'''
            else:
                if plot_data["comp_queries"]:
                    code += f'''
plot_data = {{}}
sub_queries = {plot_data['comp_queries']}
for sub_q in sub_queries:
    plot_data[sub_q if sub_q.strip() else "Base"] = {data}.query(sub_q)["{plot_data['column']}"].dropna()
combined_df = pd.concat([pd.Series(v.values, name=k) for k, v in plot_data.items()], axis=1)
sns.boxplot(data=combined_df, ax=ax, palette="{plot_data['palette']}", orient="h")'''
                else:
                    code += f'''
sns.boxplot(x={data}["{plot_data['column']}"].dropna(), ax=ax, palette="{plot_data['palette']}")'''
        case "Bar Chart (Top N)":
            if plot_data["query"]:
                code += f'''
{data} = {data}.query("{plot_data['query']}")'''
            code += f'''
counts = {data}["{plot_data['column']}"].value_counts().head({plot_data['topn']})
sns.barplot(x=counts.values, y=counts.index, palette="{plot_data['palette']}", ax=ax)'''
    code += "\nplt.show()"
    cells.append(nbf.v4.new_code_cell(code))