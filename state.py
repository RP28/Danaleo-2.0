import pandas as pd

df_global: pd.DataFrame | None = None
sessions = {}  
active_session = None
current_column = None
EXPLORE_SESSIONS = {}

BUTTON_WIDTH, BUTTON_HEIGHT, SPACING = 220, 32, 8
LEFT_X, PANEL_X, DETAIL_WIDTH = 10, 260, 200