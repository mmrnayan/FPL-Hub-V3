
from sqlalchemy import create_engine, text
import urllib.parse
import pandas as pd
import os, glob
import requests
from datetime import datetime


params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=fpl_fantasy;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)


#connection to sql server + test to see if connection works
engine  = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

with engine.connect() as conn:
    result = conn.execute(text("SELECT @@VERSION;"))
    print(result.scalar())

def combine_upload_tosql(folderpath: str, tablename: str, engine):
    """
    Reads ALL CSV files in the folder and uploads them to SQL.
    Stacks multiple files into one table.
    """
    # Get all CSV files
    files = sorted(glob.glob(os.path.join(folderpath, "*.csv")))
    
    if not files:
        print(f"[WARNING] No CSV files found in {folderpath}")
        return
    
    print(f"Found {len(files)} CSV files for table '{tablename}'")
    
    for i, path in enumerate(files):
        try:
            df = pd.read_csv(path, dtype=str, keep_default_na=False)
            
            # Replace on first file (i==0), append on all others
            mode = "replace" if i == 0 else "append"
            
            df.to_sql(name=tablename, 
                      con=engine, 
                      schema="dbo",
                      if_exists=mode,
                      index=False)
            
            print(f"   Uploaded: {os.path.basename(path)} ({len(df):,} rows)")
            
        except Exception as e:
            print(f"   [ERROR] Error with {os.path.basename(path)}: {e}")
    
    print(f"[SUCCESS] Finished loading {tablename} from {len(files)} files")


teampath = r"C:\Users\JesseOnu\fpl sql rework\teams"
teams = combine_upload_tosql(teampath, "stg_team", engine)
teams


playerpath = r"C:\Users\JesseOnu\fpl sql rework\players"
players = combine_upload_tosql(playerpath, "stg_player", engine)
players


scorepath = r"C:\Users\JesseOnu\fpl sql rework\playerscores"
playerscore = combine_upload_tosql(scorepath, "stg_player_scores", engine)
playerscore



fixturepath = r"C:\Users\JesseOnu\fpl sql rework\fixtures"
fixture = combine_upload_tosql(fixturepath, "stg_fixtures", engine)
fixture



fantasypath = r"C:\Users\JesseOnu\fpl sql rework\fantasygw"
fantasy = combine_upload_tosql(fantasypath, "stg_fantasy_gw", engine)
fantasy




gwpath = r"C:\Users\JesseOnu\fpl sql rework\gws"
gw = combine_upload_tosql(gwpath, "stg_player_gameweek", engine)
gw

playerclass = r"C:/Users/JesseOnu/fpl sql rework/player_classes"
class_ = combine_upload_tosql(playerclass, "stg_player_class", engine)
class_


# Create metadata folder if it doesn't exist
metadata_folder = r"C:\Users\JesseOnu\fpl sql rework\metadata"
os.makedirs(metadata_folder, exist_ok=True)

# Create metadata CSV
refresh_time = datetime.now()
metadata_df = pd.DataFrame({
    'last_refresh': [refresh_time]
})

# Save to CSV
metadata_df.to_csv(os.path.join(metadata_folder, "refresh_metadata.csv"), index=False)

# Upload using your normal function
metadata = combine_upload_tosql(metadata_folder, "stg_refresh_metadata", engine)
print(f"Recorded refresh time: {refresh_time}")
