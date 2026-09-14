#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd
season = 2627
def get_teams_data():
    """
    Fetches Premier League teams from FPL API and transforms it 
    exactly like your updated Power Query M code.
    """
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Extract teams list
        teams = data.get('teams', [])
        
        # Convert to DataFrame
        df = pd.DataFrame(teams)
        
        # Select only the columns we need
        df = df[['id', 'name', 'short_name', 'code']].copy()
        
        # Rename columns to match your M code
        df.rename(columns={
            'id': 'team_id',
            'name': 'team_name',
            'short_name': 'team_short_name',
            'code': 'team_code'
        }, inplace=True)
        
        # Add badge URL
        df['badge_url'] = df['team_code'].apply(
            lambda x: f"https://resources.premierleague.com/premierleague/badges/70/t{x}.png"
        )
        
        # Set proper data types
        df['team_id'] = df['team_id'].astype('Int64')
        df['team_code'] = df['team_code'].astype('Int64')
        
        # Final column order
        df = df[['team_id', 'team_name', 'team_short_name', 'team_code', 'badge_url']]
        
        print(f"✅ Successfully loaded {len(df)} teams.")
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# ================ RUN IT ================
if __name__ == "__main__":
    teams_df = get_teams_data()
    teams_df['season'] = season
    if teams_df is not None:
        print("\nPreview:")
        print(teams_df.head())
        
        # Save to CSV
        teams_df.to_csv(rf"C:\Users\JesseOnu\fpl sql rework\teams\{season}teams.csv", index=False)
        print("\n💾 Saved to 'teams.csv'")


# In[2]:


folder = r"C:\Users\JesseOnu\fpl sql rework\gws" 

