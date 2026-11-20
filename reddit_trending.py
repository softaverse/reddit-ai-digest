"""Read-only Reddit fetcher for a personal AI-news digest (u/softaverse).

What it does
- Runs every 3 hours on my own server (8 runs/day).
- Each run makes ONE request: the day's top posts across 5 public subreddits
  (a multireddit), using an application-only OAuth token (no user login).
- Keeps only post title, permalink, rank, score, comment count, created time
  and self-text. It never reads or stores usernames, comments or profiles.
- It never posts, comments, votes or sends messages.

What happens to the data
- Stored in a private database used only by me, merged with Hacker News and
  GitHub Trending signals, and summarized with an LLM (Anthropic Claude API)
  into a private daily list of trending AI topics that links back to each thread.
- Not resold, not published as a dataset, not used to train any model.
"""

import os
import time
from dataclasses import dataclass

import httpx

SUBREDDITS = ["LocalLLaMA", "ClaudeAI", "OpenAI", "ChatGPTCoding", "AI_Agents"]
TOP_N = 50
USER_AGENT = "server:softaverse-ai-digest:v1.0 (by /u/softaverse)"
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API = "https://oauth.reddit.com"


@dataclass
class Post:
    rank: int
    title: str
    permalink: str
    score: int
    comments: int
    created_utc: float
    selftext: str


def get_token(http: httpx.Client) -> str:
    """Application-only OAuth (client_credentials): read access to public data, no user account."""
    resp = http.post(
        TOKEN_URL,
        auth=(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"]),
        data={"grant_type": "client_credentials"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_top_today(http: httpx.Client, token: str) -> list[Post]:
    resp = http.get(
        f"{API}/r/{'+'.join(SUBREDDITS)}/top",
        params={"t": "day", "limit": TOP_N, "raw_json": 1},
        headers={"Authorization": f"bearer {token}"},
    )
    if resp.status_code == 429:  # respect Reddit's rate limit: wait and retry once
        time.sleep(float(resp.headers.get("x-ratelimit-reset", 60)) + 1)
        resp = http.get(resp.request.url, headers=resp.request.headers)
    resp.raise_for_status()

    posts = []
    for rank, child in enumerate(resp.json()["data"]["children"], 1):
        d = child["data"]
        posts.append(Post(
            rank=rank,
            title=d["title"],
            permalink="https://www.reddit.com" + d["permalink"],
            score=d["score"],
            comments=d["num_comments"],
            created_utc=d["created_utc"],
            selftext=d.get("selftext", ""),
            # deliberately not kept: author, comments, user data
        ))
    return posts


if __name__ == "__main__":
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30) as http:
        for p in fetch_top_today(http, get_token(http)):
            print(f"#{p.rank:>2}  {p.score:>5}↑ {p.comments:>4}💬  {p.title}  {p.permalink}")
