import asyncio
from urllib.parse import urlparse

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from feedparser import FeedParserDict
from protego import Protego
from readability import Document

from models import Scrape


class Scraper:
    def __init__(self, urls: list[str]):
        self.urls = urls

    async def get_links(self):
        parsers: list[FeedParserDict] = [feedparser.parse(url) for url in self.urls]
        res_urls: list[str] = [
            str(j.get("link") if j.get("link") != "None" else None)
            for i in range(0, len(parsers))
            for j in parsers[i].entries
        ]

        return res_urls

    async def Scraping(
        self, session: aiohttp.ClientSession, link: str, userAgent: str = "*"
    ) -> Scrape:
        try:
            header = {"User-Agent": userAgent}
            async with session.get(
                link, headers=header, timeout=aiohttp.ClientTimeout(5)
            ) as res:
                doc = Document(await res.text())
                if res.status != 200:
                    raise ValueError(f"HTML Error: {res.status}")
                if len(doc.content() or "") > 30:
                    soup = BeautifulSoup(doc.summary(), "html.parser")
                    return Scrape(
                        text=soup.get_text(separator="\n", strip=True), url=link
                    )
                else:
                    raise ValueError("len of scraped content is insufficient")
        except aiohttp.ClientError as e:
            print("Scraping error:", e)
            return Scrape(text="", url=link)

    async def validate(
        self, session: aiohttp.ClientSession, link: str, userAgent: str = "*"
    ):
        robotUrl = f"{urlparse(link).scheme}://{urlparse(link).netloc}/robots.txt"
        try:
            async with session.get(robotUrl) as res:
                if res.status == 404:
                    return link
                elif res.status == 200:
                    robots = Protego.parse(await res.text())
                    if robots.can_fetch(userAgent, link):
                        return link
                return False
        except aiohttp.ClientError as e:
            print("Validation error:", e)
            return False

    async def __call__(self):
        async with aiohttp.ClientSession() as session:
            urls = await self.get_links()
            links = [self.validate(session, link) for link in urls]
            allowed_links: list[str] = [
                link for link in await asyncio.gather(*links) if link
            ]
            scraped_res = await asyncio.gather(
                *[self.Scraping(session, link) for link in allowed_links]
            )
            return scraped_res
