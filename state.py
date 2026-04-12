import pandas as pd

df_global: pd.DataFrame | None = None
sessions = {}  
current_time = None
active_session = None
current_column = None
explore_sessions = {}
saved_plots = {}
plots_to_be_exported = {}
df_path = None