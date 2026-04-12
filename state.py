import pandas as pd

df_global: pd.DataFrame | None = None
sessions: dict[str, dict] = {}  
current_time: int | None = None
active_session: str | None = None
current_column: str | None = None
explore_sessions: dict[str, list] = {}
saved_plots: dict[str, dict] = {}
plots_to_be_exported: dict[int, list] = {}
df_path: str | None = None