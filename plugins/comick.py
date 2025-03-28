
#THis Code is made by Wizard Bots on telegram
# t.me/Wizard_Bots

import json
from typing import List, AsyncIterable
from urllib.parse import urlparse, urljoin, quote, quote_plus

from bs4 import BeautifulSoup
from plugins.client import MangaClient, MangaCard, MangaChapter, LastChapter

import cloudscraper
import asyncio 

search_query = dict()
hid_query = dict()

class ComickClient(MangaClient):
    test_url = urlparse("https://comick.cc")
    base_url = "https://api.comick"
    domains = [".fun", ".io"]
    
    pre_headers = {
        "Accept": "application/json",
        "Referer": "https://comick.cc",
        "User-Agent": "Tachiyomi Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36",
    }

    def __init__(self, *args, name="Comick", **kwargs):
        super().__init__(*args, name=name, headers=self.pre_headers, **kwargs)

    
    def mangas_from_page(self, results):
        raise
    
    def chapters_from_page(self, datas: bytes, slug: str, manga: MangaCard = None):
        texts = []
        chapters = []
        for data in datas["chapters"]:
            if data["chap"]:
                if (f"Chapter {data['chap']}") in texts:
                    continue 
                
                if (f"Chapter {data['chap']}") not in texts:
                    text = f'Chapter {data["chap"]}'
                    link = f"https://comick.io/comic/{slug}/{data['hid']}-chapter-{data['chap']}-en"
            texts.append(text)
            chapters.append(MangaChapter(self, text, link, manga, []))
        return chapters

    def updates_from_page(self, content):
        bs = BeautifulSoup(content, "html.parser")

        container = bs.find("ul", {"class": "homeupdate"})

        manga_items = container.find_all("li")

        urls = dict()

        for manga_item in manga_items[:20]:
            manga_url = manga_item.findNext("a").get("href")

            if manga_url in urls:
                continue

            chapter_url = manga_item.findNext("dl").findNext("a").get("href")

            urls[manga_url] = chapter_url

        return urls
        
    async def pictures_from_chapters(self, url):
        data = await ComickClient().get_curl(url)
        bs = BeautifulSoup(data, "html.parser")
        container = bs.find("script", {"id": "__NEXT_DATA__"})
        
        con = container.string.strip()
        con = json.loads(con)
        
        images = con["props"]["pageProps"]["chapter"]["md_images"]
        images_url = [f"https://meo.comick.pictures/{image['b2key']}" for image in images]
        
        return images_url
        
    async def get_curl(self, url):
        """ This Make For Comick Pictures """
        scraper = cloudscraper.create_scraper()
        response = await asyncio.to_thread(scraper.get, url, headers=self.pre_headers)
        if response.status_code == 200:
            return response.text 
            
    async def comic_search(self, query):
        scraper = cloudscraper.create_scraper()
        for domain in self.domains:
            # Use asyncio.to_thread to make the synchronous cloudscraper request asynchronous
            url = f"{self.base_url}{domain}/v1.0/search/?type=comic&page=1&limit=8&q={query}&t=false"
            response = await asyncio.to_thread(scraper.get, url, headers=self.pre_headers)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 10:
                    data = data[:8]
                return data
        
    async def search(self, query: str = "", page: int = 1) -> List[MangaCard]:
        if query.lower in search_query:
            names, url, images = search_query[query.lower]
            mangas = [MangaCard(self, *tup) for tup in zip(names, url, images)]
            return mangas

        results = await ComickClient().comic_search(query)
        names = []
        url = []
        images = []
        for result in range(len(results)):
            names.append(results[result]["title"])
            
            slug = results[result]["slug"]
            hid = results[result]["hid"]
            hid_query[slug] = hid
            url.append(f"https://comick.io/comic/{slug}")
            
            file_key = results[result]["md_covers"][0]["b2key"]
            images.append(f"https://meo.comick.pictures/{file_key}")
            
        search_query[query.lower] = (names, url, images)
        mangas = [MangaCard(self, *tup) for tup in zip(names, url, images)]
        
        return mangas

    async def get_chapters(self, manga_card: MangaCard, page: int = 1) -> List[MangaChapter]:
        url = str(manga_card.url)
        slug = url.split("/")[4]
        
        if slug in hid_query:
            hid = hid_query[slug]
        else:
            hid = await ComickClient().get_hid(slug)
        
        datas = await ComickClient().get_comics(hid=hid, page=page)
        
        return self.chapters_from_page(datas, slug, manga_card)
        
    async def iter_chapters(self, manga_url: str, manga_name) -> AsyncIterable[MangaChapter]:
        manga_card = MangaCard(self, manga_name, manga_url, '')

        request_url = f'{manga_card.url}'

        content = await self.get_url(request_url)

        for chapter in self.chapters_from_page(content, manga_card):
            yield chapter
            
    async def get_comics(self, hid: str, page: int):
        scraper = cloudscraper.create_scraper()
        for domain in self.domains:
            url = f"{self.base_url}{domain}/comic/{hid}/chapters?lang=en&page={str(page)}"
            response = await asyncio.to_thread(scraper.get, url, headers=self.pre_headers)
            if response.status_code == 200:
                data = response.json()
                return data
        
    async def get_hid(self, slug: str):
        scraper = cloudscraper.create_scraper()
        for domain in self.domains:
            url = f"{self.base_url}{domain}/comic/{slug}?lang=en"
            response = await asyncio.to_thread(scraper.get, url, headers=self.pre_headers)
            if response.status_code == 200:
                data = response.json()
                hid = data["comic"]["hid"]
                hid_query[slug] = hid
                return hid
                
    async def contains_url(self, url: str):
        return url.startswith(self.test_url.geturl())
    
    async def get_lastest(url):
        scraper = cloudscraper.create_scraper()
        slug = url.split("/")[4]
        link = f"https://api.comick.fun/comic/{slug}?lang=en"
        if slug in hid_query:
            hid = hid_query[slug]
        else:
            response = await asyncio.to_thread(scraper.get, link, headers=pre_headers)
            if response.status_code == 200:
                data = response.json()
                hid = data["comic"]["hid"]
                hid_query[slug] = hid
        
        link = f"https://api.comick.fun/comic/{hid}/chapters?lang=en&page=1"
        response = await asyncio.to_thread(scraper.get, link, headers=pre_headers)
        if response.status_code == 200:
            datas = response.json()
            manga_url = [f"https://comick.io/comic/{slug}/{data['hid']}-chapter-{data['chap']}-en" for data in datas["chapters"]]
            if manga_url[0] != url:
                return True, manga_url[0]
            else:
                return None, None
    
    async def check_updated_urls(self, last_chapters: List[LastChapter]):
        updated = []
        not_updated = []
        
        for lc in last_chapters:
            up, url = await get_lastest(lc)
            if up:
                updated.append(url)
            else:
                not_updated.append(lc)
        
        return updated, not_updated
