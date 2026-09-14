#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import os
import glob


# In[2]:


season = 2627
# 1. LOAD AND COMBINE ALL GW FILES
# -----------------------------------------------
# Finds every CSV in your GW folder and stacks them into one table

folder = r"C:\Users\JesseOnu\fpl sql rework\gws"
#all_files = glob(os.path.join(folder, "*.csv"))
# Only get files that START with the season and end with .csv
all_files = glob.glob(os.path.join(folder, f"{season}*.csv"))

# Optional: sort the files (recommended)
all_files = sorted(all_files)

print(f"Found {len(all_files)} files for season {season}:")
#for file in all_files:
    #print("   ", os.path.basename(file))


# In[ ]:





# In[3]:


#all_files = glob(os.path.join(folder, "*.csv"))
df = pd.concat([pd.read_csv(f) for f in all_files], ignore_index=True)

# -----------------------------------------------
# 2. FILTER TO PLAYERS WITH MINUTES > 0
# -----------------------------------------------
# Removes players who never played - stops them distorting percentiles
df = df[df["minutes"] > 0].copy()

# -----------------------------------------------
# 3. MINUTES SCORE (max-based, not percentile)
# -----------------------------------------------
# Max possible mins = highest gameweek number * 90
# Each player gets a % of that, scaled to 1-10
max_gw = df["gameweek"].max()
max_possible_mins = max_gw * 90

# Sum each player's total minutes across all GWs up to each GW
# We calculate cumulative minutes per player per GW
df = df.sort_values(["player_code", "gameweek"])
df["cumulative_mins"] = df.groupby("player_code")["minutes"].cumsum()
df["mins_score"] = (df["cumulative_mins"] / max_possible_mins * 9 + 1).clip(1, 10)

# -----------------------------------------------
# 4. PERCENTILE SCORES (within position, cumulative)
# -----------------------------------------------
# For each metric, we:
#   a) Calculate each player's cumulative total up to that GW
#   b) Rank them within their position at that GW snapshot
#   c) Convert rank to a 1-10 score

# Metrics where MORE = BETTER
positive_metrics = {
    "goals_scored": "goals_score",
    "assists":      "assists_score",
    "xG":           "xg_score",
    "xGI":          "xgi_score",
    "clean_sheets": "cs_score",
    "bonus":        "bonus_score",
}

# Metrics where LESS = BETTER (we invert the percentile)
negative_metrics = {
    "goals_conceded": "goals_conceded_score",
    "xGC":            "xgc_score",
}

def percentile_score(series, invert=False):
    """
    Takes a series of cumulative values.
    Returns a 1-10 score based on percentile rank.
    If invert=True, lower values get higher scores.
    """
    pct = series.rank(pct=True)   # gives each value a 0-1 percentile rank
    if invert:
        pct = 1 - pct             # flip so lower = better becomes higher score
    return (pct * 9 + 1).clip(1, 10)

# Calculate cumulative totals and percentile scores for each metric
for col, score_col in {**positive_metrics, **negative_metrics}.items():
    invert = col in negative_metrics
    
    # Cumulative total per player up to each GW
    cum_col = f"cum_{col}"
    df[cum_col] = df.groupby("player_code")[col].cumsum()
    
    # Percentile rank within position at each GW snapshot
    df[score_col] = (
        df.groupby(["gameweek", "position_id"])[cum_col]
        .transform(lambda x: percentile_score(x, invert=invert))
    )

# -----------------------------------------------
# 4.5. POSITION-ADJUST ATTACKING SCORES
# -----------------------------------------------
# xGI/xG/assists are weak or meaningless signals for GKs and less
# important for DEFs than MID/FWD. Rather than change the composite
# weights (section 5), we scale these score columns down by position
# BEFORE composite_score is calculated, so section 5 stays untouched.
#
# position_id convention assumed: 1=GK, 2=DEF, 3=MID, 4=FWD
# Multiplier of 1.0 = no change, lower = drastically reduced

position_multiplier = {
    "xgi_score":     {1: 0.1, 2: 0.4, 3: 1.0, 4: 1.0},
    "xg_score":      {1: 0.1, 2: 0.4, 3: 1.0, 4: 1.0},
    "assists_score": {1: 0.3, 2: 0.6, 3: 1.0, 4: 1.0},
}

def apply_position_adjustment(df, score_col, multiplier_dict):
    multiplier = df["position_id"].map(multiplier_dict)
    adjusted = df[score_col] * multiplier
    return adjusted.clip(1, 10)

for score_col, mult_dict in position_multiplier.items():
    df[score_col] = apply_position_adjustment(df, score_col, mult_dict)

# -----------------------------------------------
# 5. COMPOSITE SCORE (weighted average)
# -----------------------------------------------
# You can adjust these weights per position later
# For now, sensible defaults - same for all positions
# All weights should add up to 1
weights = {
    "mins_score":           0.1,
    "goals_score":          0.29,
    "assists_score":        0.10,
    "xg_score":             0.10,
    "xgi_score":            0.35,
    "cs_score":             0.10,
    "bonus_score":          0.05,
    "goals_conceded_score": 0.05,
    "xgc_score":            0.05,
}
df["composite_score"] = sum(
    df[score] * weight for score, weight in weights.items()
)

# -----------------------------------------------
# 6. SELECT OUTPUT COLUMNS
# -----------------------------------------------
# One row per player per GW with all scores
output_cols = [
    "player_code",
    "web_name",
    "fixture_id",
    "position_id",
    "gameweek",
    "minutes",
    "mins_score",
    "goals_score",
    "assists_score",
    "xg_score",
    "xgi_score",
    "cs_score",
    "bonus_score",
    "goals_conceded_score",
    "xgc_score",
    "composite_score",
]
output = df[output_cols].sort_values(["gameweek", "composite_score"], ascending=[True, False])
output['season'] = season


# In[4]:


output["fixture_id"] = output["fixture_id"].astype("Int64")


# In[5]:


output.head(5)


# In[6]:


# -----------------------------------------------
# 7. SAVE OUTPUT
# -----------------------------------------------
output_path = rf"C:\Users\JesseOnu\fpl sql rework\playerscores\{season}player_scores.csv"

output.to_csv(output_path, index=False)

print(f"Done! {len(output)} rows saved to {output_path}")
print(output.head(10))


# In[7]:


df2 =  pd.concat([pd.read_csv(f) for f in all_files], ignore_index=True)




