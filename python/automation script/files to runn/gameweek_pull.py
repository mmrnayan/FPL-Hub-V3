import pandas as pd
import os
import requests
import time


BASE_URL = "https://fantasy.premierleague.com/api/"
 

response = requests.get(BASE_URL + "bootstrap-static/")
data = response.json()
season = 2627
 

#CHECKING WHAT DATA RETURNS
data.keys()
 
#CHECKING ELEMENTS OUTPUT
print(data["elements"][0].keys())
 

#CHECKING WHAT EVENT ENDPOINTS RETURNS
data["events"][0]
 

test = requests.get(BASE_URL + f"element-summary/1/").json()
print(test["history"][0].keys())
 

current_gw = None
for event in data["events"]:
    if event["is_current"]:
        current_gw = event["id"]
        break

user_input = input(f"Press Enter for current GW ({current_gw}) or type a GW number: ").strip()
gw = int(user_input) if user_input else current_gw
print(f"Downloading GW{gw}...")

# ── SECTION 3 ── Players + Teams from bootstrap
players = {}
for player in data["elements"]:
    players[player["id"]] = {
        "name": f"{player['first_name']} {player['second_name']}",
        "web_name": player["web_name"],
        "team_id": player["team"],
        "position_id": player["element_type"],
        "code": player["code"],
        "now_cost": player["now_cost"] / 10,
        "status": player.get("status"),
        "news": player.get("news"),
        "corners_and_indirect_freekicks_order": player.get("corners_and_indirect_freekicks_order"),
        "direct_freekicks_order": player.get("direct_freekicks_order"),
        "penalties_order": player.get("penalties_order"),
        "selected_by_percent": player.get("selected_by_percent")
    }

teams = {}
for team in data["teams"]:
    teams[team["id"]] = team["name"]

# ── SECTION 4 ── Fixtures + Live GW data
response = requests.get(BASE_URL + "fixtures/")
fixtures_data = response.json()

response1 = requests.get(BASE_URL + f"event/{gw}/live/")
live_data = response1.json()

# Filter fixtures to this gameweek, keyed by fixture ID
fixtures = {}
for fixture in fixtures_data:
    if fixture["event"] == gw:
        fixtures[fixture["id"]] = {
            "home_team_id": fixture["team_h"],
            "away_team_id": fixture["team_a"],
            "home_score": fixture["team_h_score"],
            "away_score": fixture["team_a_score"],
            "kickoff_time": fixture["kickoff_time"]
        }

# ── SECTION 5 ── Helper function to build a row
def build_row(player_id, player, gw, fixture_id, fixtures, stats, in_dreamteam=None):
    opponent_id = None
    team_score = None
    opponent_score = None
    kickoff_time = None
    h_a = None

    if fixture_id and fixture_id in fixtures:
        fixture = fixtures[fixture_id]
        kickoff_time = fixture["kickoff_time"]

        if player["team_id"] == fixture["home_team_id"]:
            opponent_id = fixture["away_team_id"]
            team_score = fixture["home_score"]
            opponent_score = fixture["away_score"]
            h_a = "Home"
        else:
            opponent_id = fixture["home_team_id"]
            team_score = fixture["away_score"]
            opponent_score = fixture["home_score"]
            h_a = "Away"

    return {
        "player_id": player_id,
        "player_code": player.get("code"),
        "gameweek": gw,
        "fixture_id": fixture_id,
        "name": player.get("name"),
        "web_name": player.get("web_name"),
        "position_id": player.get("position_id"),
        "selected_by_percent": player.get("selected_by_percent"),
        "value": player.get("now_cost"),
        "team_id": player.get("team_id"),
        "opponent_id": opponent_id,
        "h_a": h_a,
        "kickoff_time": kickoff_time,
        "team_score": team_score,
        "opponent_score": opponent_score,
        "minutes": stats.get("minutes", 0),
        "goals_scored": stats.get("goals_scored", 0),
        "assists": stats.get("assists", 0),
        "clean_sheets": stats.get("clean_sheets", 0),
        "goals_conceded": stats.get("goals_conceded", 0),
        "yellow_cards": stats.get("yellow_cards", 0),
        "red_cards": stats.get("red_cards", 0),
        "bonus": stats.get("bonus", 0),
        "bps": stats.get("bps", 0),
        "total_points": stats.get("total_points", 0),
        "xG": stats.get("expected_goals", 0),
        "xA": stats.get("expected_assists", 0),
        "xGI": stats.get("expected_goal_involvements", 0),
        "xGC": stats.get("expected_goals_conceded", 0),
        "DefCon": stats.get("defensive_contribution", 0),
        "ict_index": stats.get("ict_index", 0),
        "influence": stats.get("influence", 0),
        "creativity": stats.get("creativity", 0),
        "threat": stats.get("threat", 0),
        "in_dreamteam": in_dreamteam,
        "status": player.get("status"),
        "news": player.get("news"),
        "corners_indirect_freekicks_order": player.get("corners_and_indirect_freekicks_order"),
        "direct_freekicks_order": player.get("direct_freekicks_order"),
        "penalties_order": player.get("penalties_order"),
    }

# ── SECTION 6 ── Main loop
rows = []

for element in live_data["elements"]:
    player_id = element["id"]
    stats = element["stats"]
    player = players.get(player_id, {})
    explains = element.get("explain", [])

    if len(explains) > 1:
        # ── Double GW ── call element-summary for per-fixture stats
        summary_response = requests.get(BASE_URL + f"element-summary/{player_id}/")
        summary_data = summary_response.json()

        # Get only fixtures that belong to this gameweek
        for game in summary_data["history"]:
            if game["round"] == gw:
                fixture_id = game["fixture"]

                per_fixture_stats = {
                    "minutes": game.get("minutes", 0),
                    "goals_scored": game.get("goals_scored", 0),
                    "assists": game.get("assists", 0),
                    "clean_sheets": game.get("clean_sheets", 0),
                    "goals_conceded": game.get("goals_conceded", 0),
                    "yellow_cards": game.get("yellow_cards", 0),
                    "red_cards": game.get("red_cards", 0),
                    "bonus": game.get("bonus", 0),
                    "bps": game.get("bps", 0),
                    "total_points": game.get("total_points", 0),
                    "expected_goals": game.get("expected_goals", 0),
                    "expected_assists": game.get("expected_assists", 0),
                    "expected_goal_involvements": game.get("expected_goal_involvements", 0),
                    "expected_goals_conceded": game.get("expected_goals_conceded", 0),
                    "defensive_contribution": game.get("defensive_contribution", 0),
                    "ict_index": game.get("ict_index", 0),
                    "influence": game.get("influence", 0),
                    "creativity": game.get("creativity", 0),
                    "threat": game.get("threat", 0),
                }

                row = build_row(player_id, player, gw, fixture_id, fixtures, per_fixture_stats, in_dreamteam=None)
                rows.append(row)

    else:
        # ── Single GW ── use live data as normal
        fixture_id = None
        if explains:
            fixture_id = explains[0].get("fixture")

        row = build_row(player_id, player, gw, fixture_id, fixtures, stats, in_dreamteam=stats.get("in_dreamteam", False))
        rows.append(row)
 
df = pd.DataFrame(rows)
df['season'] = season
df.head(2)
 

#folder where data will be saved       
folder = r"C:\Users\JesseOnu\fpl sql rework\gws" 
filename = os.path.join(folder, f"{season}gw{gw}.csv")
df.to_csv(filename, index= False)

 


