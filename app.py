# app.py
import os
import pymysql
import requests
from dotenv import load_dotenv

from discord import send_discord_embed  # 追加

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TARGET_USERNAME = "kotehanx01"
START_TIME = "2025-08-01T00:00:00Z"

HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def already_fetched(conn, tweet_id):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM fetched_tweets WHERE tweet_id=%s", (tweet_id,))
        return cur.fetchone() is not None

def mark_fetched(conn, tweet_id):
    with conn.cursor() as cur:
        cur.execute("INSERT IGNORE INTO fetched_tweets (tweet_id) VALUES (%s)", (tweet_id,))
    conn.commit()

def get_user_id(username):
    global TARGET_USERNAME
    TARGET_USERNAME = username
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()["data"]["id"]

def get_tweets_since(user_id, start_time, conn):
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        "max_results": 100,
        "start_time": start_time,
        "exclude": "",
        "tweet.fields": "created_at,text"
    }
    tweets = []
    next_token = None

    while True:
        if next_token:
            params["pagination_token"] = next_token
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        for tweet in data.get("data", []):
            if not already_fetched(conn, tweet["id"]):
                tweet["author_username"] = TARGET_USERNAME
                tweets.append(tweet)
                mark_fetched(conn, tweet["id"])
                send_discord_embed(tweet, TARGET_USERNAME)  # Discord通知
        next_token = data.get("meta", {}).get("next_token")
        if not next_token:
            break
    return tweets

def get_replies_to_user(username, start_time, conn):
    url = "https://api.twitter.com/2/tweets/search/recent"
    query = f"to:{username}"
    params = {
        "query": query,
        "max_results": 100,
        "start_time": start_time,
        "tweet.fields": "in_reply_to_user_id,author_id,created_at,text"
    }
    replies = []
    next_token = None

    while True:
        if next_token:
            params["next_token"] = next_token
        resp = requests.get(url, headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        for tweet in data.get("data", []):
            if not already_fetched(conn, tweet["id"]):
                tweet["author_username"] = "reply_user"
                replies.append(tweet)
                mark_fetched(conn, tweet["id"])
                send_discord_embed(tweet, username)  # Discord通知
        next_token = data.get("meta", {}).get("next_token")
        if not next_token:
            break
    return replies

if __name__ == "__main__":
    conn = get_db_connection()
    user_id = get_user_id(TARGET_USERNAME)

    tweets = get_tweets_since(user_id, START_TIME, conn)
    print(f"新規ツイート {len(tweets)} 件")

    replies = get_replies_to_user(TARGET_USERNAME, START_TIME, conn)
    print(f"新規返信 {len(replies)} 件")

    conn.close()
