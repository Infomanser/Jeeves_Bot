# services/news_api.py
import feedparser
import html
import asyncio
from concurrent.futures import ThreadPoolExecutor
from config import RSS_FEEDS


executor = ThreadPoolExecutor()

def _parse_feed_sync(url: str, limit: int = 2) -> list:
    """Синхронна функція парсингу одного фіда"""
    try:
        feed = feedparser.parse(url)
        entries = []
        # Беремо перші `limit` записів
        for entry in feed.entries[:limit]:
            title = html.escape(entry.get('title', 'Без назви'))
            link = entry.get('link', '')
            # Назва джерела (наприклад, "DOU.ua")
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

    # Запускаємо парсинг усіх фідів паралельно
    tasks = [
        loop.run_in_executor(executor, _parse_feed_sync, url)
        for url in RSS_FEEDS
    ]
    
    results = await asyncio.gather(*tasks)

    # Збираємо все в купу
    for news_items in results:
        all_news.extend(news_items)

    if not all_news:
        return "📭 Новин не знайдено або помилка з'єднання."

    # Можна обрізати, якщо новин занадто багато (ліміт повідомлення Telegram)
    final_text = "🗞 <b>Свіжа преса:</b>\n\n" + "\n".join(all_news[:15])
    return final_text
