import os
import pymysql
import snscrape.modules.twitter as sntwitter
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from discord import send_discord_embed  # 既存の関数を利用

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

TARGET_USERNAME = "kotehanx01"

# cron用：直近1時間分だけ取得
START_TIME = datetime.now(timezone.utc) - timedelta(hours=1)

# === DB接続関連 ===
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

# === ツイート取得 ===
def get_tweets_since(username, start_time, conn):
    tweets = []
    query = f"from:{username} since:{start_time.strftime('%Y-%m-%d')}"
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i > 200:  # 無限取得防止
            break
        if not already_fetched(conn, str(tweet.id)):
            tweet_data = {
                "id": str(tweet.id),
                "text": tweet.content,
                "created_at": tweet.date.isoformat(),
                "author_username": username
            }
            # 画像がある場合
            if tweet.media:
                for m in tweet.media:
                    if isinstance(m, sntwitter.Photo):
                        tweet_data["media_url"] = m.fullUrl
                        break

            tweets.append(tweet_data)
            mark_fetched(conn, str(tweet.id))
            send_discord_embed(tweet_data, username)
    return tweets

# === リプライ取得 ===
def get_replies_to_user(username, start_time, conn):
    replies = []
    query = f"to:{username} since:{start_time.strftime('%Y-%m-%d')}"
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i > 200:
            break
        if not already_fetched(conn, str(tweet.id)):
            tweet_data = {
                "id": str(tweet.id),
                "text": tweet.content,
                "created_at": tweet.date.isoformat(),
                "author_username": tweet.user.username
            }
            replies.append(tweet_data)
            mark_fetched(conn, str(tweet.id))
            send_discord_embed(tweet_data, username)
    return replies

# === メイン処理 ===
if __name__ == "__main__":
    conn = get_db_connection()

    tweets = get_tweets_since(TARGET_USERNAME, START_TIME, conn)
    print(f"新規ツイート {len(tweets)} 件")

    replies = get_replies_to_user(TARGET_USERNAME, START_TIME, conn)
    print(f"新規返信 {len(replies)} 件")

    conn.close()
