#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import requests
import os


# Run this next season 
# 

# In[2]:


#url for all calls
base_url = "https://fantasy.premierleague.com/api/"
#folder where data will be saved
season = 2627
folder = rf"C:\Users\JesseOnu\fpl sql rework\players\{season}playerid" 
output = f"{folder}.csv"


# In[3]:


#call api
response = requests.get(base_url + "bootstrap-static/")


# In[4]:


#convert to json
data = response.json()


# In[5]:


print(type(data))
print(type(response))
print(response.status_code)


# In[6]:


#displaying availabl fields
print(data["elements"][0].keys())


# In[7]:


#keeping necesarry fields
df = pd.DataFrame(data["elements"])

df = df[["id", "code", "first_name", "second_name", "web_name", "photo", "element_type"]]
df['season'] = season


# In[8]:


df.head()


# In[9]:


#replace 'jpg' with 'png' as images dont work with jpg
df['photo'] = df['photo'].str.replace('jpg', 'png', regex = False)


# In[10]:


#add prefix to photo
seasonshort = 25
df['photo'] = f"https://resources.premierleague.com/premierleague{seasonshort}/photos/players/110x140/" + df['photo']
df.head(1)


# In[11]:


seasonshort


# In[12]:


df.iloc[0]['photo']


# In[13]:


#making sure theres no blank webnames
(df['web_name']=='').sum()


# In[14]:


#check for no duplicates
df['id'].duplicated().sum()


# In[15]:


df.to_csv(output, index = False)


# ## Changing 2526 to old photos

# In[18]:


season1 = 2526
folder1 = rf"C:\Users\JesseOnu\fpl sql rework\players\{season1}playerid" 
output2 = f"{folder1}.csv"
df2 = pd.read_csv(r"C:\Users\JesseOnu\fpl sql rework\players\2526playerid.csv")



# In[19]:


df2['photo'][0]


# In[22]:


df2['photos'] = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p" + df2['code'].astype(str) + ".png"
df2['photos'][0]


# In[23]:


df2 = df2.drop(columns=['photo'])


# In[26]:


df2 =df2.rename(columns ={'photos':'photo'})
df2


# In[27]:


df2.to_csv(output2, index = False)


# In[ ]:




