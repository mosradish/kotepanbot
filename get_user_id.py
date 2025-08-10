# get_user_id.py
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

def get_user_id(username: str) -> str:
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    while True:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 429:
            reset_time = int(resp.headers.get("x-rate-limit-reset", 0))
            sleep_seconds = max(reset_time - int(time.time()), 0) + 1
            print(f"Rate limit exceeded on get_user_id. Sleeping for {sleep_seconds} seconds...")
            time.sleep(sleep_seconds)
            continue
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["id"]
