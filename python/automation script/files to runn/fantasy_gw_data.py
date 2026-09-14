
import requests
import pandas as pd
from datetime import datetime

season= 2627
def get_gameweeks_data():
    """
    Fetches Gameweek (Events) data from FPL API - exactly like your M code.
    """
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Extract events
        events = data.get('events', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(events)
        
        # Select and rename columns to match your Power Query
        columns_to_keep = {
            'id': 'gameweek_id',
            'name': 'gameweek_name',
            'deadline_time': 'deadline_time',
            'average_entry_score': 'average_score',
            'highest_score': 'highest_score',
            'most_selected': 'most_selected',
            'most_transferred_in': 'most_transferred_in',
            'most_captained': 'most_captained',
            'most_vice_captained': 'most_vice_captained',
            'top_element': 'top_element',
            'transfers_made': 'transfers_made',
            'finished': 'finished',
            'is_current': 'is_current',
            'is_previous': 'is_previous'
        }
        
        df = df[list(columns_to_keep.keys())].copy()
        df.rename(columns=columns_to_keep, inplace=True)
        
        # Convert data types
        df['gameweek_id'] = df['gameweek_id'].astype('Int64')
        df['average_score'] = df['average_score'].astype('Int64')
        df['highest_score'] = df['highest_score'].astype('Int64')
        df['most_selected'] = df['most_selected'].astype('Int64')
        df['most_transferred_in'] = df['most_transferred_in'].astype('Int64')
        df['most_captained'] = df['most_captained'].astype('Int64')
        df['most_vice_captained'] = df['most_vice_captained'].astype('Int64')
        df['top_element'] = df['top_element'].astype('Int64')
        df['transfers_made'] = df['transfers_made'].astype('Int64')
        
        # Convert deadline_time to proper datetime
        df['deadline_time'] = pd.to_datetime(df['deadline_time'])
        
        # Add a few useful columns
        df['season'] = season          # ← You can populate this later
        df['is_next'] = False           # Useful flag
        
        print(f" Successfully loaded {len(df)} gameweeks.")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f" API request failed: {e}")
        return None
    except Exception as e:
        print(f" Error: {e}")
        return None


# ====================== RUN ======================
if __name__ == "__main__":
    gw_df = get_gameweeks_data()
    
    if gw_df is not None:
        print("\nPreview of Gameweeks:")
        print(gw_df[['gameweek_id', 'gameweek_name', 'deadline_time', 'is_current', 'finished']].head(10))
        
        # Save to CSV
        gw_df.to_csv(rf"C:\Users\JesseOnu\fpl sql rework\fantasygw\{season}fantasygw.csv", index=False)
        print("\n Saved to 'fantasy_gw_data'")





