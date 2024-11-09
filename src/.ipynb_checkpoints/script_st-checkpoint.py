import subprocess

# Install required packages from requirements.txt
subprocess.call("pip install -r requirements.txt", shell=True)

import numpy as np
import pandas as pd
import streamlit as st
from st_files_connection import FilesConnection
import gcsfs
import os
import lightgbm as lgb


secrets = st.secrets["connections_gcs"]
secret_value = os.environ.get('connections_gcs')

# Create a GCS connection
conn = st.experimental_connection('gcs', type=FilesConnection)

# Read a file from the cloud storage
df = conn.read("gs://bundesliga_0410/matches.csv", input_format="csv")
Teamlist = conn.read("gs://bundesliga_0410/Teamlist.csv", input_format="csv")

st.title('Bundesliga match score prediction')

# Create a dropdown menu
user_inputs_A = st.selectbox('Home Team', Teamlist['opponent'].tolist())
user_inputs_B = st.selectbox('Guess Team', Teamlist['opponent'].tolist())

#df=df.drop(['Unnamed: 0','Unnamed: 0.1'], axis = 1)

user_inputs_date = st.date_input('Select a date')
venue = ['Home','Away']
user_inputs_venue = st.selectbox('Select a venue',venue)
user_inputs_round = 'Matchweek ' + str(st.number_input("Enter the matchweek", min_value =1, max_value=34, step=1, format="%d"))
user_inputs_season = st.number_input('Enter the season', min_value=2014, max_value=2050, step = 1 )
user_inputs_time = str(st.time_input('Select match time'))

# rename and match the teams name of home team and opponent team columns
Team_name = {
    'Arminia':'Arminia',
    'Augsburg':'Augsburg',
    'Bayer Leverkusen': 'Bayer Leverkusen',
    'Bayern Munich':'Bayern Munich',
    'Bochum':'Bochum',
    'Darmstadt 98':'Darmstadt 98',
    'Dortmund':'Dortmund',
    'Eintracht Frankfurt': 'Eintracht Frankfurt',
    'Freiburg': 'Freiburg',
    'Greuther Furth': 'Greuther Fürth',
    'Heidenheim': 'Heidenheim',
    'Hertha BSC': 'Hertha BSC',
    'Hoffenheim': 'Hoffenheim',
    'Koln': 'Köln',
    'Mainz 05':'Mainz 05',
    'Monchengladbach': 'Monchengladbach',
    'RB Leipzig':'RB Leipzig',
    'Schalke 04': 'Schalke 04',
    'Stuttgart': 'Stuttgart',
    'Union Berlin': 'Union Berlin',
    'Werder Bremen': 'Werder Bremen',
    'Wolfsburg': 'Wolfsburg',
    'Dusseldorf': 'Düsseldorf',
    'Hamburger SV': 'Hamburger SV',
    'Paderborn 07': 'Paderborn 07',
    'Hannover 96': 'Hannover 96',
    'Nurnberg': 'Nürnberg',
    'Ingolstadt 04':'Ingolstadt 04',
    'Eintracht Braunschweig': 'Eintracht Braunschweig'
}
Opponent_name = {
    'Arminia':'Arminia',
    'Augsburg':'Augsburg',
    'Leverkusen': 'Bayer Leverkusen',
    'Bayern Munich':'Bayern Munich',
    'Bochum':'Bochum',
    'Darmstadt 98':'Darmstadt 98',
    'Dortmund':'Dortmund',
    'Eint Frankfurt': 'Eintracht Frankfurt',
    'Freiburg': 'Freiburg',
    'Greuther Fürth': 'Greuther Fürth',
    'Heidenheim': 'Heidenheim',
    'Hertha BSC': 'Hertha BSC',
    'Hoffenheim': 'Hoffenheim',
    'Köln': 'Köln',
    'Mainz 05':'Mainz 05',
    "M'Gladbach": 'Monchengladbach',
    'RB Leipzig':'RB Leipzig',
    'Schalke 04': 'Schalke 04',
    'Stuttgart': 'Stuttgart',
    'Union Berlin': 'Union Berlin',
    'Werder Bremen': 'Werder Bremen',
    'Wolfsburg': 'Wolfsburg',
    'Düsseldorf': 'Düsseldorf',
    'Hamburger SV': 'Hamburger SV',
    'Paderborn 07': 'Paderborn 07',
    'Hannover 96': 'Hannover 96',
    'Nürnberg': 'Nürnberg',
    'Ingolstadt 04':'Ingolstadt 04',
    'Braunschweig': 'Eintracht Braunschweig'
}

df['team'] = df['team'].map(Team_name)
df['opponent'] = df['opponent'].map(Opponent_name)

# Add new match to the dataframe:
Data_input = {'date':user_inputs_date,
              'time':user_inputs_time,
              'comp':'Bundesliga',
              'round':user_inputs_round,
              'day':None,
              'venue':user_inputs_venue,
              'gf': None,
              'ga': None,
              'opponent':user_inputs_B,
              'poss': None,
              'sh':None,
              'save%':None,
              'season':user_inputs_season,
              'team':user_inputs_A
              }
df = df.drop('index', axis=1)

df.loc[len(df.index)] = [user_inputs_date,user_inputs_time,'Bundesliga',user_inputs_round,None,user_inputs_venue,None, None, user_inputs_B,None,None,None,user_inputs_season,user_inputs_A]
# Determine the second venue option
second_venue_option = 'Home' if user_inputs_venue == 'Away' else 'Away'
df.loc[len(df.index)] = [user_inputs_date,user_inputs_time,'Bundesliga',user_inputs_round,None,second_venue_option,None, None, user_inputs_A,None,None,None,user_inputs_season,user_inputs_B]
df["date"] = pd.to_datetime(df["date"])
df['time'] = df['time'].astype(str)

# Convert categorical variables into numerical variables
df["venue_code"] = df["venue"].astype("category").cat.codes
df["team_code"] = df["team"].astype("category").cat.codes
df["opp_code"] = df["opponent"].astype("category").cat.codes
df["time"].fillna("", inplace=True)
df["hour"] = df["time"].str.extract(r'(\d+):').fillna("-1")
df["hour"] = df["hour"].astype("int")
df["day_code"] = df["date"].dt.dayofweek
df['round']=df['round'].apply(lambda x: x.replace('Matchweek', '')).astype('int')

# average goal per season and team
average_goal_st= df.groupby(['team', 'season'])[['gf','ga']].mean().reset_index()
df = pd.merge(df, average_goal_st, on = ["team","season"])
df[['gf','ga','average_ga_st','average_gf_st']] = df[['gf_x','ga_x','ga_y', 'gf_y']].rename(columns=
                                {'gf_x': 'gf','ga_x':'ga', 'ga_y':'average_ga_st', 'gf_y': 'average_gf_st'})
df = df.drop(['gf_x','ga_x','gf_y','ga_y'], axis = 1)

# average goal per season
average_goal_s = df.groupby('season')['gf'].mean().reset_index()
df = pd.merge(df, average_goal_s, on = "season")
df[['gf','average_gf_s']] = df[['gf_x','gf_y']].rename(columns={'gf_x': 'gf', 'gf_y': 'average_gf_s'})
df = df.drop(['gf_x','gf_y'], axis = 1)


# average goal per team
average_goal_t = df.groupby('team')[['gf','ga']].mean().reset_index()
df = pd.merge(df, average_goal_t, on = "team")
df[['gf','ga','average_gf_t','average_ga_t']] = df[['gf_x','ga_x','ga_y','gf_y']].rename(columns={'gf_x': 'gf','ga_x':'ga','ga_y':'average_ga_t', 'gf_y': 'average_gf_t'})
df = df.drop(['gf_x','ga_x','gf_y','ga_y'], axis = 1)

# average goal per season per round
average_goal_sr = df.groupby(['season', 'round'])['gf'].mean().reset_index()
df = pd.merge(df, average_goal_sr, on=["season", "round"])
df[['gf','average_gf_sr']] = df[['gf_x','gf_y']].rename(columns={'gf_x': 'gf', 'gf_y': 'average_gf_sr'})
df = df.drop(['gf_x','gf_y'], axis = 1)

# average goal per round
average_goal_r = df.groupby('round')['gf'].mean().reset_index()
df = pd.merge(df, average_goal_r, on = "round")
df[['gf','average_gf_r']] = df[['gf_x','gf_y']].rename(columns={'gf_x': 'gf', 'gf_y': 'average_gf_r'})
df = df.drop(['gf_x','gf_y'], axis = 1)

# average goal per season per venue
average_goal_sv = df.groupby(['season','venue'])['gf'].mean().reset_index()
df = pd.merge(df, average_goal_sv, on = ["season","venue"])
df[['gf','average_gf_sv']] = df[['gf_x','gf_y']].rename(columns={'gf_x': 'gf', 'gf_y': 'average_gf_sv'})
df = df.drop(['gf_x','gf_y'], axis = 1)

# average goal per round per team
average_goal_rt = df.groupby(['round','team'])['gf'].mean().reset_index()
df = pd.merge(df, average_goal_rt, on = ["round","team"])
df[['gf','average_gf_rt']] = df[['gf_x','gf_y']].rename(columns={'gf_x': 'gf', 'gf_y': 'average_gf_rt'})
df = df.drop(['gf_x','gf_y'], axis = 1)

# average goal per hour
average_goal_h = df.groupby('hour')['gf'].mean().reset_index()
df = pd.merge(df, average_goal_h, on='hour')
df[['gf','average_gf_h']] = df[['gf_x','gf_y']].rename(columns={'gf_x': 'gf', 'gf_y': 'average_gf_h'})
df = df.drop(['gf_x','gf_y'], axis = 1)

df['total_t'] = df['average_ga_t'] + df['average_gf_t']
df['total_st'] = df['average_ga_st'] + df['average_gf_st']

df['total_goal'] = df['gf'] + df['ga']

df_A = df[df['team']==user_inputs_A]

# average of the last 3 games
def rolling_averages(group, cols_1, cols_2, new_cols_1, new_cols_2):
    group = group.sort_values("date")
    rolling_stats = group[cols_1].rolling(3, closed='left').mean()
    previous_stats = group[cols_2].rolling(1, closed='left').mean()
    group[new_cols_1] = rolling_stats
    group[new_cols_2] = previous_stats
    #group = group.dropna(subset=new_cols)
    return group

cols_1 = ["gf",'ga','poss','sh', 'save%', 'total_goal']
new_cols_1 = [f"{c}_rolling" for c in cols_1] 

cols_2 = []
new_cols_2 = [f"{c}_last_game" for c in cols_2]
group = df_A

matches_rolling_A = rolling_averages(group, cols_1, cols_2, new_cols_1, new_cols_2)
matches_rolling = df.groupby('team').apply(lambda x: rolling_averages(x, cols_1, cols_2, new_cols_1, new_cols_2))
matches_rolling.index = matches_rolling.index.droplevel()

import random
import numpy as np

def generate_random_t(x):
    lower_bound = max(0, x - 2)  # Ensure the lower bound is non-negative
    upper_bound = x + 4
    if lower_bound < upper_bound:  # Ensure valid range
        return np.random.randint(lower_bound, upper_bound)
    else:
        return lower_bound  # Or handle the error condition as appropriate

matches_rolling['random_t'] = matches_rolling['total_t'].apply(generate_random_t)
matches_rolling['total_goal_rolling'].fillna(0, inplace=True)
matches_rolling['random_total_goal'] = matches_rolling['total_goal_rolling'].apply(generate_random_t)


 # Head 2 head performance  
home_team = user_inputs_A
away_team = user_inputs_B
date = pd.to_datetime(user_inputs_date)
        
# Filter the DataFrame for historical matches between the specified home and away teams
historical_matches_1 = matches_rolling[(matches_rolling['team'] == away_team) & (matches_rolling['opponent'] == home_team)] # historical matches stats of opponent team
historical_matches_2 = matches_rolling[(matches_rolling['team'] == home_team) & (matches_rolling['opponent'] == away_team)] # historical matches stats of home team

        # Exclude the current match by filtering based on the date
historical_matches_1 = historical_matches_1[historical_matches_1['date'] < date]
historical_matches_2 = historical_matches_2[historical_matches_2['date'] < date]

        # Select opponent's last match
last_match = historical_matches_1.sort_values(by='date', ascending=False).iloc[0]

cols = ['gf', 'sh', 'save%','poss']
opp_cols = ['save%_rolling','sh_rolling', 'gf_rolling']       
        
        # Select relevant columns for historical data
historical_data_1 = historical_matches_1[cols]
historical_data_2 = historical_matches_2[cols]
        
        # Optionally, you can aggregate the historical data (e.g., take the mean)
historical_data_1 = historical_data_1.mean()
historical_data_2 = historical_data_2.mean()
        
new_cols_1 = [f'{c}_hist_opp' for c in cols]
new_cols_2 = [f'{c}_hist_home' for c in cols]
new_cols_3 = [f'{c}_opp' for c in opp_cols]

match_AB = pd.DataFrame(matches_rolling[(matches_rolling['team']==user_inputs_A)&(matches_rolling['opponent']==user_inputs_B)&(matches_rolling['date']==date)])
match_AB[new_cols_1] = historical_data_1
match_AB[new_cols_2] = historical_data_2
match_AB[new_cols_3] = last_match[opp_cols]

match_AB = match_AB[['date','round', 'gf_rolling','ga_rolling','sh_rolling', 'save%_rolling', 'poss_rolling',
                        'average_gf_s', 'average_gf_sr',  'average_gf_r', 'average_gf_t','average_ga_t','average_gf_st','average_ga_st',
                        'average_gf_rt','average_gf_sv', 'average_gf_h', 'total_t', 'total_st', 'random_t','random_total_goal',
                        'save%_rolling_opp', 'gf_rolling_opp',
                        'gf_hist_opp',  'poss_hist_opp', 'save%_hist_opp', 
                        'gf_hist_home', 'poss_hist_home', 
                        'venue_code','team_code', 'opp_code', 'day_code']]
match_AB = match_AB.set_index('date', inplace=False)


match_BA = pd.DataFrame(matches_rolling[(matches_rolling['team']==user_inputs_B)&(matches_rolling['opponent']==user_inputs_A)&(matches_rolling['date']==date)])
match_BA[['save%_rolling_opp', 'gf_rolling_opp', 'gf_hist_opp', 'poss_hist_opp', 'gf_hist_home', 'poss_hist_home']] = match_AB[['save%_rolling', 'gf_rolling', 'gf_hist_home', 'poss_hist_home', 'gf_hist_opp', 'poss_hist_opp']].iloc[0]
#match_BA['save%_rolling_opp'] = match_AB['save%_rolling'][0]
#match_BA['gf_rolling_opp'] = match_AB['gf_rolling'][0]
#match_BA['gf_hist_opp'] = historical_data_2['gf']
#match_BA['poss_hist_opp'] = historical_data_2['poss']
#match_BA['gf_hist_home'] = historical_data_1['gf']
#match_BA['poss_hist_home'] = historical_data_1['poss']
match_BA['save%_hist_opp']= historical_data_2['save%']
match_BA = match_BA[['date','round', 'gf_rolling','ga_rolling','sh_rolling', 'save%_rolling', 'poss_rolling',
                        'average_gf_s', 'average_gf_sr',  'average_gf_r', 'average_gf_t','average_ga_t','average_gf_st','average_ga_st',
                        'average_gf_rt','average_gf_sv', 'average_gf_h', 'total_t', 'total_st', 'random_t','random_total_goal',
                        'save%_rolling_opp', 'gf_rolling_opp',
                        'gf_hist_opp',  'poss_hist_opp', 'save%_hist_opp', 
                        'gf_hist_home', 'poss_hist_home', 
                        'venue_code','team_code', 'opp_code', 'day_code']]
match_BA = match_BA.set_index('date', inplace=False)

from google.cloud import storage

# Initialize Google Cloud Storage client
client = storage.Client()

# Define your Google Cloud Storage bucket name and model file path
bucket_name = 'lgbm_model'
model_blob_name = 'lgbm.txt'  # Path within the bucket
# Get the bucket
bucket = client.get_bucket(bucket_name)

# Download the model file from Google Cloud Storage
blob = bucket.blob(model_blob_name)
local_model_file = 'lgbm.txt'
blob.download_to_filename(local_model_file)

# Load the LightGBM model
model = lgb.Booster(model_file='lgbm.txt')

# Predict gf A:
Predicted_gf_A = round(model.predict(match_AB)[0],2)
# Predict gf B:
Predicted_gf_B = round(model.predict(match_BA)[0],2)

match_AB_show = df[['date','time','comp','venue','round','season','team','opponent']][(df['team']==user_inputs_A)&(df['opponent']==user_inputs_B)&(df['date']==date)]

st.dataframe(match_AB_show)

# Display the text only when needed
if st.button("Show Predictions"):
    st.write(f'Predicted goal for {user_inputs_A} : {Predicted_gf_A}');
    st.write(f'Predicted goal for {user_inputs_B} : {Predicted_gf_B}')

# import image in GCS
from PIL import Image
import io

image_blob_name1 = 'Subject.png' 
image_blob_name2 = 'Subject (2).png'
blob_image1=bucket.blob(image_blob_name1)
blob_image2=bucket.blob(image_blob_name2)
image_bytes1 = blob_image1.download_as_string()
image_bytes2 = blob_image2.download_as_string()
image_yes = Image.open(io.BytesIO(image_bytes2))
image_no = Image.open(io.BytesIO(image_bytes1))

st.write('Have you said happy birthday to Vollie?')
if st.button("Yes"):
    st.image(image_yes,caption="❤️18.03❤️", use_column_width=True)
    
if st.button("Not yet"):   
    st.image(image_no,caption="Let's go party", use_column_width=True);
   