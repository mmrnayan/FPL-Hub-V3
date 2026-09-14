#!/usr/bin/env python
# coding: utf-8

# In[1]:


from sqlalchemy import create_engine, text
import urllib.parse
import pandas as pd
import os, glob
import requests


# In[2]:


params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=fpl_fantasy;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)


# In[3]:


#connection to sql server + test to see if connection works
engine  = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

with engine.connect() as conn:
    result = conn.execute(text("SELECT @@VERSION;"))
    print(result.scalar())


# In[4]:


def combine_upload_tosql(folderpath: str, tablename: str, engine):
    """
    Reads ALL CSV files in the folder and uploads them to SQL.
    Stacks multiple files into one table.
    """
    # Get all CSV files
    files = sorted(glob.glob(os.path.join(folderpath, "*.csv")))
    
    if not files:
        print(f"⚠️ No CSV files found in {folderpath}")
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
            print(f"   ❌ Error with {os.path.basename(path)}: {e}")
    
    print(f"✅ Finished loading {tablename} from {len(files)} files")


# In[ ]:


teampath = r"C:\Users\JesseOnu\fpl sql rework\teams"
teams = combine_upload_tosql(teampath, "stg_team", engine)
teams


# In[5]:


playerpath = r"C:\Users\JesseOnu\fpl sql rework\players"
players = combine_upload_tosql(playerpath, "stg_player", engine)
players


# In[5]:


scorepath = r"C:\Users\JesseOnu\fpl sql rework\playerscores"
playerscore = combine_upload_tosql(scorepath, "stg_player_scores", engine)
playerscore


# In[6]:


fixturepath = r"C:\Users\JesseOnu\fpl sql rework\fixtures"
fixture = combine_upload_tosql(fixturepath, "stg_fixtures", engine)
fixture


# In[7]:


fantasypath = r"C:\Users\JesseOnu\fpl sql rework\fantasygw"
fantasy = combine_upload_tosql(fantasypath, "stg_fantasy_gw", engine)
fantasy


# In[8]:


gwpath = r"C:\Users\JesseOnu\fpl sql rework\gws"
gw = combine_upload_tosql(gwpath, "stg_player_gameweek", engine)
gw


# In[ ]:




