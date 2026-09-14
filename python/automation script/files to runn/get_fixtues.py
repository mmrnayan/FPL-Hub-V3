#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import pandas as pd

resp = requests.get("https://fantasy.premierleague.com/api/fixtures/")
fixtures_raw = resp.json()
season = 2627
df = pd.DataFrame(fixtures_raw, dtype=str)
df['season'] = season
df.to_csv(rf"C:\Users\JesseOnu\fpl sql rework\fixtures\{season}fixtures.csv", index=False)



