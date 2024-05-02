import httpx
from bs4 import BeautifulSoup

async def get_link_info(link):
    async with httpx.AsyncClient() as client:
        response = await client.get(link)
        data = response.text
        soup = BeautifulSoup(data, 'html.parser')
        title = soup.title.string if soup.title else None
        tags = [tag.name for tag in soup.find_all()]
        return {
            'title': title,
            'tags': tags
        }