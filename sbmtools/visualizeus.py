# -*- coding: utf-8 -*-

import json
from lxml.html import document_fromstring  # pip install lxml && pip install cssselect
import urllib, urllib2
from configparser import ConfigParser
import mechanize

VISUALIZEUS_URL = 'http://vi.sualize.us/'

"""
Reads links from vi.sualize.us website and processes them for further import or export
operations. Currently only scraping mode is supported which works only with public bookmarks
"""
class VisualizeUsAPI:

    def __init__(self, config):
        conf = ConfigParser()
        conf.read(config)
        self.user = conf.get('visualizeus', 'user')
        self.password = conf.get('visualizeus', 'password')
#        self.user = 'danpaulius'
#        self.password = 'fatality'
        self.loggedin = False

    def login(self):
        url = VISUALIZEUS_URL + 'login/'
        br = mechanize.Browser()
        response = br.open(url)
        for form1 in br.forms():
            form = form1
            break;
        br.select_form(nr=0)
        form["login"] = self.user
        form["password"] = self.password
        response = br.submit()
        self.loggedin = True


    def get_items(self):

        def read_page(url):
            response = urllib2.urlopen(url)
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
            print 'Reading ', page_next
            page_links, page_next = read_page(page_next)
            items.extend(page_links)
        return self.parse_links(items)


    def parse_links(self, links):
        """ Parses a set of links from vi.sualize.us website """
        data = []
        taglist = set()
        for link in links:
            response = urllib2.urlopen(link)
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
            data.append({'title': title, 'image_url': img, 'link': link,
                         'tags': tags})
        return data, taglist


    def select_by_tag(self, data, tag):
        return [item for item in data if item.has_key('tags') and tag in item['tags']]

