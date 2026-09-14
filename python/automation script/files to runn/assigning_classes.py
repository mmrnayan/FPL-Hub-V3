import pandas as pd
import numpy as np
import pickle
import os
from sklearn.metrics.pairwise import euclidean_distances

# Load training model
with open('C:/Users/JesseOnu/fpl sql rework/fpl classifications/fpl_classification_training.pkl', 'rb') as f:
    training_output = pickle.load(f)

centroids_dict = training_output['centroids']
scaler = training_output['scaler']
position_config = training_output['position_config']
archetype_names = training_output['archetype_names']

# Step 1: Load and merge all files
folder = "C:/Users/JesseOnu/fpl sql rework/gws"
cols_to_keep = ['player_code', 'gameweek', 'web_name', 'position_id',
       'minutes', 'goals_scored', 'assists', 'xG', 'xA', 'xGI', 'DefCon', 'season']

def load_all_data(path):
    files = os.listdir(path)
    dataframes = []
    for f in files:
        filepath = os.path.join(path, f)
        df = pd.read_csv(filepath, usecols=cols_to_keep)
        dataframes.append(df)
    return pd.concat(dataframes, ignore_index=True).reset_index(drop=True)

df_all = load_all_data(folder)

# Step 2: Get distinct seasons and split into separate dfs
seasons = sorted(df_all['season'].unique())
season_dfs = {season: df_all[df_all['season'] == season].copy() for season in seasons}

# Step 3: For each season, aggregate, calculate stats, normalize, and classify
results = []

for season, df_season in season_dfs.items():
    print(f"\nProcessing Season {season}...")
    
    # Aggregate by player
    stats = df_season.groupby(['player_code', 'web_name']).agg({
        'minutes': 'sum',
        'goals_scored': 'sum',
        'assists': 'sum',
        'xG': 'sum',
        'xA': 'sum',
        'xGI': 'sum',
        'DefCon': 'sum',
        'position_id': 'max'
    }).reset_index()
    
    # Calculate per-90 stats
    stats['xGp90'] = (90 * stats['xG'] / stats['minutes']).fillna(0).round(2)
    stats['xAp90'] = (90 * stats['xA'] / stats['minutes']).fillna(0).round(2)
    stats['defconp90'] = (90 * stats['DefCon'] / stats['minutes']).fillna(0).round(2)
    stats['xgisafe'] = stats['xGI'].apply(lambda x: x if x > 0 else 0.001)
    stats['xasafe'] = stats['xA'].apply(lambda x: x if x > 0 else 0.001)
    stats['xgi_performance_pct'] = ((stats['goals_scored'] + stats['assists'] - stats['xgisafe']) / stats['xgisafe']).round(2).clip(-1.0, 1.0)
    stats['xa_performance_pct'] = ((stats['assists'] - stats['xasafe']) / stats['xasafe']).round(2).clip(-1.0, 1.0)
    max_min = stats['minutes'].max()
    stats['min_perc'] = stats['minutes']/max_min
    stats = stats[stats['min_perc']>= 0.25]
    # Normalize using saved scaler
    all_features = ['xGp90', 'xAp90', 'defconp90', 'xgi_performance_pct', 'xa_performance_pct']
    stats_normalized = stats.copy()
    stats_normalized[all_features] = scaler.transform(stats[all_features])
    
    # Classify for each position
    stats['archetype'] = None
    
    for position_id in [4, 3, 2]:
        position_mask = stats['position_id'] == position_id
        position_stats = stats[position_mask].copy()
        position_normalized = stats_normalized[position_mask].copy()
        
        features = position_config[position_id]['features']
        centroids = centroids_dict[position_id]
        
        # Assign to nearest centroid
        distances = euclidean_distances(position_normalized[features], centroids)
        cluster_assignments = distances.argmin(axis=1)
        
        # Map to archetype names
        archetypes = [archetype_names[position_id][cluster] for cluster in cluster_assignments]
        
        stats.loc[position_mask, 'archetype'] = archetypes
    
    # Add season column back
    stats['season'] = season
    results.append(stats)

# Step 4: Combine all seasons
final_df = pd.concat(results, ignore_index=True)
final_df.to_csv('C:/Users/JesseOnu/fpl sql rework/player_classes/fpl_player_classifications_all_seasons.csv', index=False)