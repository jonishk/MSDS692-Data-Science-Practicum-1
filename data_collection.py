import praw
import pandas as pd
import os
import time
from datetime import datetime

import sys
sys.stdout.reconfigure(line_buffering=True)

# --------- SETUP ----------
reddit = praw.Reddit(
    client_id="qL6M97vuwERUMPfq3f53XQ",
    client_secret="XsJsBSfZj3jZNccXiJG77CtDanDojg",
    user_agent="MSDS 692 Scrape"
)

# Subreddit categories provided by the business
subreddit_categories = {
    "Law": [
        "legaltech", "LawFirm", "Law", "LegalAdvice", 
        "LegalAdviceUK", "LegalAdviceCanada", "Paralegal", 
        "LawSchool", "LegalNews"
    ],
    "Construction": [
        "Construction", "Contractors", "HomeImprovement", "DIY", 
        "DIYChatRoom", "Electrical", "Plumbing", "HVAC", "AskEngineers"
    ],
    "Tech": [
        "sysadmin", "msp", "talesfromtechsupport", "iiiiiiitttttttttttt",
        "techsupportgore", "ITCareerQuestions", "netsec", "cybersecurity",
        "technology", "tech", "gadgets", "apple", "linux"
    ]
}

POST_LIMIT = 100     # posts per subreddit
COMMENT_LIMIT = 15   # cap comments per post
SLEEP_TIME = 8       # wait between subreddit fetches
output_file = "reddit_data.csv"
# log_file = "scrape_log.txt"

# Load existing data (if any)
if os.path.exists(output_file):
    df_existing = pd.read_csv(output_file, parse_dates=["created_utc"])
else:
    df_existing = pd.DataFrame(columns=[
        "id", "category", "subreddit", "title", "content", "author", 
        "score", "num_comments", "created_utc", "edited", "type", "parent_id"
    ])

# Helper: get last scrape time per subreddit
last_times = (
    df_existing.groupby("subreddit")["created_utc"].max().to_dict()
    if not df_existing.empty else {}
)

def fetch_subreddit_posts(subreddit_name, category, limit=100, last_time=None):
    subreddit = reddit.subreddit(subreddit_name)
    posts_data = []

    for post in subreddit.new(limit=limit):
        post_time = datetime.utcfromtimestamp(post.created_utc)

        # Skip if this post is older/equal to last scraped one
        if last_time and post_time <= last_time:
            continue

        # Post row
        post_data = {
            "id": post.id,
            "category": category,
            "subreddit": subreddit_name,
            "title": post.title,
            "content": post.selftext,
            "author": str(post.author),
            "score": post.score,
            "num_comments": post.num_comments,
            "created_utc": post_time,
            "edited": post.edited if post.edited else False,
            "type": "post",
            "parent_id": None,
        }
        posts_data.append(post_data)

        # Comments rows
        post.comments.replace_more(limit=0)
        for comment in post.comments.list()[:COMMENT_LIMIT]:
            comment_time = datetime.utcfromtimestamp(comment.created_utc)

            # Skip old comments
            if last_time and comment_time <= last_time:
                continue

            comment_data = {
                "id": comment.id,
                "category": category,
                "subreddit": subreddit_name,
                "title": None,
                "content": comment.body,
                "author": str(comment.author),
                "score": comment.score,
                "num_comments": None,
                "created_utc": comment_time,
                "edited": comment.edited if comment.edited else False,
                "type": "comment",
                "parent_id": comment.parent_id,
            }
            posts_data.append(comment_data)

    return posts_data


# --------- MAIN SCRIPT ----------
all_data = []
for category, subreddits in subreddit_categories.items():
    for sub in subreddits:
        try:
            print(f"Fetching data from r/{sub} (Category: {category})...")

            last_time = last_times.get(sub)  # last scraped time for this subreddit
            all_data.extend(fetch_subreddit_posts(sub, category, POST_LIMIT, last_time))

            time.sleep(SLEEP_TIME)
        except Exception as e:
            print(f"Skipping r/{sub}: {e}")
            time.sleep(SLEEP_TIME)

# Convert to DataFrame
df_new = pd.DataFrame(all_data)

# Combine with existing data
df_combined = pd.concat([df_existing, df_new], ignore_index=True)
df_combined = df_combined.drop_duplicates(subset=["id"], keep="last")

# Save updated dataset
df_combined.to_csv(output_file, index=False)

# Logging
new_rows_added = len(df_new)
# log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Added {new_rows_added} new rows. Total dataset size: {len(df_combined)}\n"

# with open(log_file, "a") as f:
#     f.write(log_entry)
# data_collection.py
import sys, time, os

LOG_PATH = "scrape_log.txt"

def log(message):
    print(message, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(message + "\n")

log(" Starting data collection...")

for i in range(10):  # simulate 10 progress updates
    time.sleep(30)   # simulate a long task
    log(f"Progress: {(i+1)*10}% complete")

log(" Data collection finished successfully!")


print(f"Data collection complete! {new_rows_added} new rows added. Total = {len(df_combined)}")
# print(f"Log entry written to {log_file}")
