# reddit-ai-digest

Read-only Reddit fetcher for a personal AI-news digest, operated by u/softaverse.

- 1 request every 3 hours (8/day): top posts of the day across r/LocalLLaMA, r/ClaudeAI, r/OpenAI, r/ChatGPTCoding, r/AI_Agents
- Application-only OAuth, read-only: never posts, comments, votes or messages
- Keeps title, link, rank, score, comment count, self-text; no usernames, comments or profile data
- Private use only; summarized with an LLM into a daily list linking back to each thread; not resold, not published, not used for model training

See `reddit_trending.py`. Run: `REDDIT_CLIENT_ID=... REDDIT_CLIENT_SECRET=... python reddit_trending.py`
