# -*- coding: utf-8 -*-

from lxml.html import document_fromstring  # pip install lxml && pip install cssselect
from configparser import ConfigParser
import mechanize
from .core import CoreAPI
from .progress import SimpleProgressBar

VISUALIZEUS_URL = 'http://vi.sualize.us/'

"""
Reads links from vi.sualize.us website and processes them for further import or export
operations. Only scraping mode supported
"""
class VisualizeUsAPI(CoreAPI):

    def __init__(self, config):
        conf = ConfigParser()
        conf.read(config)
        self.user = conf.get('visualizeus', 'user')
        self.password = conf.get('visualizeus', 'password')
        self.__br = None
        self.loggedin = False

    def login(self):
        url = VISUALIZEUS_URL + 'login/'
        self.__br = mechanize.Browser()
        self.__br.set_handle_robots(False)
        self.__br.set_handle_equiv(False)
        self.__br.set_handle_refresh(False)
        self.__br.addheaders = [('User-Agent', 'Firefox'), ('Accept', '*/*')]
        response = self.__br.open(url)
        for form1 in self.__br.forms():
            form = form1
            break
        self.__br.select_form(nr=0)
        form["login"] = self.user
        form["password"] = self.password
        response = self.__br.submit()
        self.loggedin = True


    def get_items(self):

        def read_page(url):
            response = self.__br.open(url)
            content = response.read().decode('utf-8')
            doc = document_fromstring(content)
            links = []
            next_page = None
            for div in doc.cssselect('nav.paginator div.pager div div'):
                clname = div.get('class')
                if clname and clname.startswith('next_container'):
                    alist = div.cssselect('a')
                    if alist and len(alist) > 0:
                        next_page = alist[0].get('href')
            for li in doc.cssselect('li'):
                clname = li.get('class')
                if clname and clname.startswith('bookmark xfolkentry'):
                    for a in li.cssselect('div.bookmark-media a'):
                        links.append(a.get('href'))
            return links, next_page

        items = []
        if not self.loggedin:
            self.login()
        page_links, page_next = read_page(VISUALIZEUS_URL + self.user)
        items.extend(page_links)
        while page_next:
            page_links, page_next = read_page(page_next)
            items.extend(page_links)
        return self.parse_links(items)


    def parse_links(self, links, pause=True, batch_size=50, time_=120):
        """ Parses a set of links from vi.sualize.us website """
        data = {}
        id, batch = 1, 1
        taglist = set()
        progbar = SimpleProgressBar(len(links))
        for link in links:
            response = self.__br.open(link)
            content = response.read().decode('utf-8')
            doc = document_fromstring(content)
            titlediv = doc.cssselect('title')
            title = titlediv[0].text_content().replace('Picture on VisualizeUs', '').strip() if titlediv else None
            imgs = doc.cssselect('div.media-content img')
            img = imgs[0].get('src') if imgs else None
            if not img:
                continue
            links = doc.cssselect('div.quote a')
            link = links[0].get('href') if links else None
            tags = []
            for a in doc.cssselect('ul.tags-links li a'):
                tg = a.text_content().strip()
                tags.append(tg)
                taglist.add(tg)
            data[id] = {'title': title, 'image_url': img, 'link': link, 'tags': tags}
            progbar.update(id)
            if pause and batch_size > 0 and batch == batch_size:
                if not time_ is None and time_ > 0:
                    progbar.pause(time_)
                batch = 0
            id += 1
            batch += 1
        progbar.finish()
        return data, taglist


