from pydantic import BaseModel


class Scrape(BaseModel):
    url: str
    text: str
