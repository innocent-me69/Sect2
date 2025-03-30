
import re
from typing import List, AsyncIterable
from urllib.parse import urlparse, urljoin, quote, quote_plus

from bs4 import BeautifulSoup

import cloudscraper
import asyncio 
import json
from plugins.client import MangaClient, MangaCard, MangaChapter, LastChapter

pre_headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 14; zh-cn; 2211133C Build/UKQ1.230804.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.118 Mobile Safari/537.36 XiaoMi/MiuiBrowser/18.5.40902'
    }

search_query = dict()

async def comic_search(url):
    scraper = cloudscraper.create_scraper()

    response = await asyncio.to_thread(scraper.get, url, headers=pre_headers)
    if response.status_code == 200:
        # data = response.json()
        # if len(data) > 10:
        #     data = data[:8]
        return response 
    else:
        print(f"Error: {response.status_code}")
        return None
        

class mangamob(MangaClient):
    base_url = urlparse("https://www.mangamob.com/")
    image_cdn = "https://cdn.mangageko.com/avatar/288x412"
    search_url = urljoin(base_url.geturl(), "browse-comics/")
    search_param = "search"
    update_url = base_url.geturl()

    pre_headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; U; Android 14; zh-cn; 2211133C Build/UKQ1.230804.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.5414.118 Mobile Safari/537.36 XiaoMi/MiuiBrowser/18.5.40902'
    }

    def __init__(self, *args, name="mangamob", **kwargs):
        super().__init__(*args, name=name, headers=self.pre_headers, **kwargs)


    def get_manga_id(self, page: bytes):
        bs = BeautifulSoup(page, "html.parser")

        script_tags = bs.find_all("script")
        for script in script_tags:
            if script.string:
                match = re.search(r"manga_id:\s*(\d+)", script.string)
                if match:
                    return match.group(1)

        return None

    async def comic_search(url):
        scraper = cloudscraper.create_scraper()

        response = await asyncio.to_thread(scraper.get, url, headers=pre_headers)
        if response.status_code == 200:
            # data = response.json()
            # if len(data) > 10:
            #     data = data[:8]
            return response 
        else:
            print(f"Error: {response.status_code}")
            return None
    

    def mangas_from_page(self, page: bytes):
        bs = BeautifulSoup(page, "html.parser")
        cards = bs.find_all('div', class_='item item-spc')
        names = []
        urls = []
        images = []

        for card in cards:
            a_tag = card.find('a')
            if a_tag is not None:
                name = a_tag.find("img").get('alt').strip()
                url = urljoin(self.base_url.geturl(), a_tag.get('href').strip())
                print(url)
                img_tag = card.find("img")
                image =(
                    img_tag.get('src').strip()) if img_tag else None

                names.append(name)
                urls.append(url)
                images.append(image)

        mangas = [MangaCard(self, *tup) for tup in zip(names, urls, images)]
        return mangas


    def chapters_from_page(self, page: bytes, manga: MangaCard = None):
        

        data = json.loads(page)
        texts = []
        chapters = []

        for data in data['chapters']:
            
            text = data.get("chapter_number").split("-")[0].strip()
            url = data.get("chapter_slug").strip()
            if text and url:
                texts.append(f" Chapter {text}")
                chapters.append(f"https://www.mangamob.com/chapter/en/{url}")
                
        return list(
            map(lambda x: MangaChapter(self, x[0], x[1], manga, []),
                zip(texts, chapters)))


    def updates_from_page(self, content: bytes):
        bs = BeautifulSoup(content, "html.parser")

        container = bs.find("div", {"id": "latest-chap"})
        items = container.findAll("div", {"class": "item item-spc"})

        urls = dict()

        for item in items:
            manga_url = urljoin(self.base_url.geturl(), item.find('a').get('href'))
            if manga_url in urls:
                continue

            chapter_url = item.find("div", {"class": "chapter"}).find("a").get("href")
            new_chapter_url = f"{self.base_url.geturl()}{chapter_url}/"  

            urls[manga_url] = new_chapter_url

        return urls

    async def pictures_from_chapters(self, content: bytes, response=None):
        bs = BeautifulSoup(content, "html.parser")

        chapter_reader_div = bs.find("div", {"id": "chapter-images"})
        image_items = chapter_reader_div.find_all("img") if chapter_reader_div else []

        images_url = [image_item.get("data-src") for image_item in image_items]

        return images_url[:-1]

    async def get_picture(self, manga_chapter: MangaChapter, url, *args, **kwargs):
        headers = dict(self.headers)
        headers['Referer'] = self.base_url.geturl()

        return await super(mangamob, self).get_picture(manga_chapter, url, headers=headers, *args, **kwargs)

    async def search(self, query: str = "", page: int = 1) -> List[MangaCard]:

        "https://www.mangamob.com/browse-comics/?search=revenge"

        request_url = self.search_url
        query = query.strip()
        query = query.replace(" ", "+").replace("’", "+")

        if query:
            request_url = f'{request_url}?{self.search_param}={query}'

        content = await self.get_url(request_url)


        return self.mangas_from_page(content)

    async def get_chapters(self, manga_card: MangaCard, page: int = 1) -> List[MangaChapter]:
        request_url = manga_card.url

        content = await self.get_url(request_url)

        id = self.get_manga_id(content)
        if not id:
            return []
        
        print(f" id {id}")
        
        data_1 = await self.get_url(f"https://www.mangamob.com/get/chapters/?manga_id={id}")

        return self.chapters_from_page(data_1, manga_card)[(page - 1) * 20:page * 20]

    async def iter_chapters(self, manga_url: str, manga_name) -> AsyncIterable[MangaChapter]:
        manga_card = MangaCard(self, manga_name, manga_url, '')

        request_url = manga_card.url

        content = await self.get_url(request_url)

        id = self.get_manga_id(content)
        if not id:
            pass
        
        print(f" id {id}")
        
        data_1 = await self.get_url(f"https://www.mangamob.com/get/chapters/?manga_id={id}")

        for chapter in self.chapters_from_page(data_1, manga_card):
            yield chapter

    async def contains_url(self, url: str):
        return url.startswith(self.base_url.geturl())

    async def check_updated_urls(self, last_chapters: List[LastChapter]):

        updates_url = self.update_url

        content = await self.get_url(updates_url)

        updates = self.updates_from_page(content)

        updated = []
        not_updated = []
        for lc in last_chapters:
            if lc.url in updates.keys():
                if updates.get(lc.url) != lc.chapter_url:
                    updated.append(lc.url)
            elif updates.get(lc.url) == lc.chapter_url:
                not_updated.append(lc.url)
                
        return updated, not_updated
