from pydantic import BaseModel
from pydantic.types import UUID4


class Scrape(BaseModel):
    id: UUID4
    url: str
    text: str
    headline: str
