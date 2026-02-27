import asyncio

from clustering import Clustering
from scraper import Scraper


# mostly for demo testing
async def main():
    k = Scraper(urls=["https://www.livemint.com/rss/companies"])
    s = await k()
    t = Clustering(s)
    t()


asyncio.run(main())
