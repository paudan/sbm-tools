
from lxml.etree import tostring
from lxml.html import document_fromstring  # pip install lxml && pip install cssselect
from configparser import ConfigParser
from urlparse import urljoin
import re
import mechanize

MYVIDSTER_URL = 'http://www.myvidster.com/'

"""
Reads links myvidster.com.us website and processes them for further import or export
operations. Currently only scraping mode is supported
"""
class MyVidsterAPI:

    def __init__(self, config):
        conf = ConfigParser()
        conf.read(config)
        self.user = conf.get('myvidster', 'user')
        self.password = conf.get('myvidster', 'password')
        self.loggedin = False
        self.br = None


    def login(self):
        url = MYVIDSTER_URL + 'user/'
        self.br = mechanize.Browser()
        self.br.set_handle_robots(False)
        self.br.set_handle_equiv(False)
        self.br.set_handle_refresh(False)
        self.br.addheaders = [('User-Agent', 'Firefox'), ('Accept', '*/*')]
        response = self.br.open(url)
        for form1 in self.br.forms():
            form = form1
        if form is None:
            return
        self.br.select_form(nr=1)
        form["user_id"] = self.user
        form["password"] = self.password
        response = self.br.submit()
        self.loggedin = True


    def __parse_page__(self, url):
        links = {}
        response = self.br.open(url)
        content = response.read().decode('utf-8')
        doc = document_fromstring(content)
        for a in doc.cssselect('a.folder'):
            links[a.text_content().strip()] = urljoin(MYVIDSTER_URL, a.get('href'))
        next_page = None
        page_links = doc.cssselect('div.pagination a')
        for a in page_links:
            if a.text_content().strip().lower().startswith('next'):
                next_page = MYVIDSTER_URL + 'user/' + a.get('href')
                next_page = re.sub("entries_per_page=([\\d]+)", "entries_per_page=50", next_page)
        return links, next_page


    def get_collection_list(self):
        url = MYVIDSTER_URL + 'user/manage.php?entries_per_page=50'
        links, next_page = self.__parse_page__(url)
        while next_page:
            nlinks, next_page = self.__parse_page__(next_page)
            links.update(nlinks)
        return links


    def get_collection_url(self, collection, collection_data=None):
        if collection_data is None:
            collection_data = self.get_collection_list()
        return collection_data[collection]


    def get_channel_url(self, channel_name, collection, collection_url=None, collection_data=None, channel_data=None):
        if channel_data is not None:
            return channel_data[channel_name]
        channel_data = self.get_channel_list(collection, url=collection_url, collection_data=collection_data)
        return channel_data[channel_name]


    def get_channel_list(self, collection, url=None, collection_data=None):
        if url is None:
            url = self.get_collection_url(collection, collection_data)
        links, next_page = self.__parse_page__(url)
        while next_page:
            nlinks, next_page = self.__parse_page__(next_page)
            links.update(nlinks)
        return links


    def get_links(self, channel_name, channel_url=None, channel_data=None):
        if channel_url is None:
            channel_url = self.get_channel_url(channel_name, channel_data=channel_data)
        pass


    def get_all_bookmarks(self):

        def read_page_bookmarks(page_url):
            links = set()
            data = {}
            response = self.br.open(page_url)
            content = response.read()
            doc = document_fromstring(content)
            for a in doc.cssselect('li.thumbnail a'):
                links.add(urljoin(MYVIDSTER_URL, a.get('href')))
            for link in links:
                id = link.split('/')[-2]
                response = self.br.open(link)
                content = response.read().decode('utf-8')
                doc = document_fromstring(content)
                h2 = doc.cssselect('div.details_header * h2')
                collection, channel, title_ = None, None, None
                if h2 is not None and len(h2) > 0:
                    title = h2[0]
                    alist = title.cssselect('a')
                    collection = alist[0].text_content().strip()
                    channel = alist[1].text_content().strip()
                    title_ = alist[2].text_content().strip()
                block_html = None
                videoblock = doc.cssselect('div#video_space')
                if videoblock:
                    block_html = tostring(videoblock[0], method='html').\
                        replace('\nYour browser does not support inline frames or is currently configured not to display inline frames.\n', '')
                detlist = doc.cssselect('div.details_video')
                date_, link_, description_ = None, None, None
                tags = []
                if detlist is not None and len(detlist) > 0:
                    details = detlist[2]
                    for td in details.cssselect('td'):
                        b = td.cssselect('b')
                        if b is not None and len(b) > 0:
                            txt = b[0].text_content().strip()
                            if txt.lower().startswith('bookmark date'):
                                date_ = td.text_content().strip()
                                date_ = date_.replace('Bookmark Date:\n', '')
                            elif txt.lower().startswith('source link'):
                                a = td.cssselect('a')
                                if a is not None and len(a) > 0:
                                    link_ = a[0].get('href')
                desc = doc.cssselect('div#desc_more')
                if desc is not None:
                    description_ = desc[0].text_content().replace('(less)', '').strip(' \n')
                for a in doc.cssselect('a.tag_cloud'):
                    tags.append(a.text_content().strip())
                data[id] = {'title': title_, 'collection': collection, 'channel': channel,
                            'date': date_, 'link': link_, 'description': description_, 'tags': tags,
                            'block_html': block_html}
            return data

        return read_page_bookmarks(MYVIDSTER_URL + 'profile/' + self.user)