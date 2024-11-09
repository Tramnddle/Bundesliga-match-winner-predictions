import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
from google.cloud import storage
from google.oauth2 import service_account
from google.cloud import dns
from io import StringIO
import os
import json
import boto3
from loguru import logger

def get_secret(secret_name):
    client = boto3.client("secretsmanager")
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = get_secret_value_response["SecretString"]
    return json.loads(secret)

def upload_log_to_s3(log_file_path, bucket_name, s3_key):
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(log_file_path, bucket_name, s3_key)
        logger.info(f"Log file {log_file_path} uploaded to S3 bucket {bucket_name} with key {s3_key}")
    except Exception as e:
        logger.error(f"Failed to upload log file to S3: {e}")

def upload_to_s3(data, bucket_name, s3_key):
    s3_client = boto3.client('s3')
    try:
        s3_client.put_object(Body=data, Bucket=bucket_name, Key=s3_key)
        logger.info(f"Data successfully uploaded to S3 bucket {bucket_name} with key {s3_key}")
    except Exception as e:
        logger.error(f"Failed to upload data to S3: {e}")

def main():
    log_file_path = "/tmp/script_{time}.log"
    logger.add(log_file_path, rotation="1 day")

    logger.info("Script started")

    Today = datetime.date(2024, 6, 1)
    Today_str = Today.strftime("%Y-%m-%d")
    
    try:
        # Send a GET request to the URL
        url = "https://fbref.com/en/comps/20/Bundesliga-Stats"
        response = requests.get(url)
        response.raise_for_status()
        logger.info("Successfully fetched the main URL")
    except requests.RequestException as e:
        logger.error(f"Error fetching the main URL: {e}")
        return

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all h1 tags
    h1_tags = soup.find_all("h1")
    
    # Iterate through the h1 tags to find the desired line
    for h1_tag in h1_tags:
        if "Bundesliga Stats" in h1_tag.text:
            line = h1_tag.text.strip()
            break
    
    year = line.split("-")[1].split()[0]
    all_matches = []
    
    try:
        standings_url = "https://fbref.com/en/comps/20/Bundesliga-Stats"
        data = requests.get(standings_url)
        data.raise_for_status()
        soup = BeautifulSoup(data.text, features ='lxml')
        standings_table = soup.select('table.stats_table')[0]
        logger.info("Successfully fetched standings data")
    except requests.RequestException as e:
        logger.error(f"Error fetching standings data: {e}")
        return
    
    links = [l.get("href") for l in standings_table.find_all('a')]
    links = [l for l in links if '/squads/' in l]
    team_urls = [f"https://fbref.com{l}" for l in links]
        
    previous_season = soup.select("a.prev")[0].get("href")
    standings_url = f"https://fbref.com{previous_season}"
    
    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        
        try:
            data = requests.get(team_url)
            data.raise_for_status()
            logger.info(f"Successfully fetched data for team: {team_name}")
        except requests.RequestException as e:
            logger.error(f"Error fetching data for team {team_name}: {e}")
            continue
        
        html_data = StringIO(data.text)
        Scores_Fixtures = pd.read_html(html_data, match="Scores & Fixtures")[0]
        Scores_Fixtures = Scores_Fixtures[['Date','Time','Comp','Round','Day','Venue','GF','GA','Opponent','Poss']]
        Scores_Fixtures = Scores_Fixtures[(Scores_Fixtures['Date'] <= Today_str) & (Scores_Fixtures['Date'] > (Today - datetime.timedelta(days=90)).strftime("%Y-%m-%d"))]
        
        soup = BeautifulSoup(data.text, features ='lxml')
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/shooting/' in l]
        
        try:
            data = requests.get(f"https://fbref.com{links[0]}")
            data.raise_for_status()
            logger.info(f"Successfully fetched shooting data for team: {team_name}")
        except requests.RequestException as e:
            logger.error(f"Error fetching shooting data for team {team_name}: {e}")
            continue
        
        html_data = StringIO(data.text)
        shooting = pd.read_html(html_data, match="Shooting")[0]
        shooting.columns = shooting.columns.droplevel()
        shooting = shooting[(shooting['Date']<= Today_str) & (shooting['Date']> (Today- datetime.timedelta(days=90)).strftime("%Y-%m-%d"))]
        
        soup = BeautifulSoup(data.text, features ='lxml')
        links = soup.find_all('a')
        links = [l.get("href") for l in links]
        links = [l for l in links if l and 'all_comps/keeper/' in l]
        
        try:
            data = requests.get(f"https://fbref.com{links[0]}")
            data.raise_for_status()
            logger.info(f"Successfully fetched goalkeeping data for team: {team_name}")
        except requests.RequestException as e:
            logger.error(f"Error fetching goalkeeping data for team {team_name}: {e}")
            continue
        
        html_data = StringIO(data.text)
        goalkeeping = pd.read_html(html_data, match="Goalkeeping")[0]
        goalkeeping.columns = goalkeeping.columns.droplevel()
        goalkeeping = goalkeeping[(goalkeeping['Date']<= Today_str) & (goalkeeping['Date']> (Today- datetime.timedelta(days=90)).strftime("%Y-%m-%d"))]
        
        try:
            team_data = Scores_Fixtures.merge(shooting[['Date','Sh']], on = ['Date'])
            team_data = team_data.merge(goalkeeping[['Date','Save%']], on = ['Date'])
        except ValueError as e:
            logger.error(f"Error merging data for team {team_name}: {e}")
            continue
        
        team_data = team_data[team_data["Comp"] == "Bundesliga"]
        team_data["Season"] = year
        team_data["Team"] = team_name
        all_matches.append(team_data)
        time.sleep(20)
    
    if not all_matches:
        logger.error("No match data collected")
        return
    
    match_df = pd.concat(all_matches)
    match_df.columns = [c.lower() for c in match_df.columns]
    
    match_df[['gf', 'ga','poss','sh','save%']] = match_df[['gf', 'ga','poss','sh','save%']].astype(float)
    match_df['season'] = match_df['season'].astype(int)
    
    # Retrieve credentials from Secrets Manager
    secret = get_secret("GOOGLE_APPLICATION_CREDENTIALS")
    credentials_json = secret["key"]
    
    # Save the credentials to a temporary file
    credentials_path = "/tmp/key.json"
    with open(credentials_path, "w") as f:
        f.write(credentials_json)
    
    # Load the Google Cloud credentials from the temporary file
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    
    # Set the Google Cloud project ID
    project_id = secret["project_id"]
    
    # Use the credentials and project ID to create the DNS and Storage clients
    client = dns.Client(project=project_id, credentials=credentials)
    client = storage.Client()
    
    # Use the Storage client to download the CSV file
    bucket = client.get_bucket("bundesliga_0410")
    blob = bucket.blob("matches.csv")
    blob.download_to_filename("/tmp/matches.csv")
    
    # Read the CSV file into a DataFrame
    df = pd.read_csv("/tmp/matches.csv")
    
    df[['gf', 'ga','poss','sh','save%']] = df[['gf', 'ga','poss','sh','save%']].astype(float)
    df['season'] = df['season'].astype(int)
    df = df.drop('index', axis =1)
    
    df_combined = pd.concat([df, match_df]).drop_duplicates().reset_index()
    
    updated_df = df_combined.to_csv(index=False)
    
    # Upload updated data to Google Cloud Storage
    filename_in_bucket = bucket.blob('matches.csv')
    filename_in_bucket.upload_from_string(updated_df)
    
    # Upload updated data to S3
    upload_to_s3(updated_df, "bundesliga0410", "matches.csv")
    
    logger.info("Data uploaded successfully to Google Cloud Storage and S3")

    # Upload log file to S3
    formatted_log_file_path = log_file_path.replace("{time}", datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    upload_log_to_s3(formatted_log_file_path, "bundesliga0410", "script.log")

    return "Data uploaded successfully to Google Cloud Storage and S3", 200, {"Content-Type": "text/plain"}

if __name__ == "__main__":
    main()
