import os
import time
import requests
import urllib3
import snscrape.modules.twitter as sntwitter
from dotenv import load_dotenv
import pymysql
import json

# SSL 警告を非表示にする
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TARGET_USERNAME = "kotehanx01"
START_TIME = "2025-08-01"

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
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

def send_discord_embed(tweet):
    tweet_text = tweet.get("content", "")
    if len(tweet_text) > 400:
        tweet_text = tweet_text[:397] + "..."

    embed = {
        "embeds": [
            {
                "title": f"📢 @{TARGET_USERNAME} さんの新しいツイート",
                "url": f"https://twitter.com/{TARGET_USERNAME}/status/{tweet['id']}",
                "description": tweet_text,
                "color": 0x1DA1F2,
                "footer": {"text": "Twitter → Discord 自動通知"},
                "timestamp": tweet.get("date").isoformat()
            }
        ]
    }

    headers = {"Content-Type": "application/json"}
    # verify=False を使う
    resp = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(embed), headers=headers, verify=False)
    resp.raise_for_status()

def get_tweets_since(username, start_time, conn):
    query = f"from:{username} since:{start_time}"
    tweets = []

    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        if not already_fetched(conn, str(tweet.id)):
            tweets.append({
                "id": str(tweet.id),
                "content": tweet.content,
                "date": tweet.date
            })
            mark_fetched(conn, str(tweet.id))
            send_discord_embed({
                "id": str(tweet.id),
                "content": tweet.content,
                "date": tweet.date
            })

    return tweets

if __name__ == "__main__":
    conn = get_db_connection()
    tweets = get_tweets_since(TARGET_USERNAME, START_TIME, conn)
    print(f"新規ツイート {len(tweets)} 件")
    conn.close()
