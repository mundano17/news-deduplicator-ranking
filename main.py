import asyncio

from clustering import Clustering
from scraper import Scraper


# mostly for demo testing
async def main():
    k = Scraper(
        urls=[
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            "https://www.politico.com/rss/politics08.xml",
        ]
    )
    s = await k()
    t = Clustering(s)
    t()


asyncio.run(main())
