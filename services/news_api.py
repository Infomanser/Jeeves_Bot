# services/news_api.py
import feedparser
import html
import asyncio
import sqlite3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from config import RSS_FEEDS


executor = ThreadPoolExecutor()

def _parse_feed_sync(url: str, limit: int = 2) -> list:
    """Синхронна функція парсингу одного фіда"""
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries[:limit]:
            title = html.escape(entry.get('title', 'Без назви'))
            link = entry.get('link', '')
            source_title = feed.feed.get('title', 'Джерело')
            entries.append(f"🔹 <a href='{link}'>{title}</a> <i>({source_title})</i>")
        return entries
    except:
        return []

async def get_fresh_news() -> str:
    if not RSS_FEEDS:
        return "⚠️ У налаштуваннях (.env) немає RSS-стрічок."

    loop = asyncio.get_running_loop()
    all_news = []

    tasks = [
        loop.run_in_executor(executor, _parse_feed_sync, url)
        for url in RSS_FEEDS
    ]
    
    results = await asyncio.gather(*tasks)

    for news_items in results:
        all_news.extend(news_items)

    if not all_news:
        return "📭 Новин не знайдено або помилка з'єднання."

    final_text = "🗞 <b>Свіжа преса:</b>\n\n" + "\n".join(all_news[:15])
    return final_text
