
from lxml.etree import tostring
from lxml.html import document_fromstring
try:
    from xml.etree import cElementTree as ElementTree
except ImportError, e:
    from xml.etree import ElementTree

from configparser import ConfigParser
from urlparse import urljoin, urlparse, parse_qs
import re
import mechanize
import requests
import urllib
import hashlib
from requests.exceptions import RequestException
from .core import CoreAPI
from .exceptions import MissingParameterException, NotConnectedException, RequestProcessingException
from .progress import SimpleProgressBar

MYVIDSTER_URL = 'http://www.myvidster.com/'

"""
Reads links myvidster.com.us website and processes them for further import or export
operations. Currently only scraping mode is supported
"""
class MyVidsterAPI(CoreAPI):

    def __init__(self, config):
        conf = ConfigParser()
        conf.read(config)
        self.user = conf.get('myvidster', 'user')
        self.password = conf.get('myvidster', 'password')
        self.loggedin = False
        self.__br = None


    def login(self):
        url = MYVIDSTER_URL + 'user/'
        self.__br = mechanize.Browser()
        self.__br.set_handle_robots(False)
        self.__br.set_handle_equiv(False)
        self.__br.set_handle_refresh(False)
        self.__br.addheaders = [('User-Agent', 'Firefox'), ('Accept', '*/*')]
        response = self.__br.open(url)
        for form1 in self.__br.forms():
            form = form1
        if form is None:
            return
        self.__br.select_form(nr=1)
        form["user_id"] = self.user
        form["password"] = self.password
        response = self.__br.submit()
        self.loggedin = True


    def parse_acollection(self, doc):
        return {a.text_content().strip() : urljoin(MYVIDSTER_URL, a.get('href'))
                for a in doc.cssselect('a.folder')}


    def __parse_page__(self, url, linkfun):
        if not self.loggedin:
            raise NotConnectedException('You must call login() in order to use this method!')
        response = self.__br.open(url + '&entries_per_page=50')
        content = response.read().decode('utf-8')
        doc = document_fromstring(content)
        links = linkfun(doc)
        next_page = None
        page_links = doc.cssselect('div.pagination a')
        for a in page_links:
            if a.text_content().strip().lower().startswith('next'):
                next_page = MYVIDSTER_URL + 'user/' + a.get('href')
                next_page = re.sub("entries_per_page=([\\d]+)", "entries_per_page=50", next_page)
        return links, next_page


    def get_collection_list(self):
        url = MYVIDSTER_URL + 'user/manage.php?entries_per_page=50'
        links, next_page = self.__parse_page__(url, self.parse_acollection)
        while next_page:
            nlinks, next_page = self.__parse_page__(next_page, self.parse_acollection)
            links.update(nlinks)
        return links


    def get_collection_url(self, collection, collection_data=None):
        if collection_data is None:
            collection_data = self.get_collection_list()
        return collection_data[collection] if collection_data.has_key(collection) else None


    def get_channel_url(self,  collection, channel_name, collection_url=None, collection_data=None, channel_data=None):
        if not self.loggedin:
            raise NotConnectedException('You must call login() in order to use this method!')
        if channel_data is not None:
            return channel_data[channel_name]
        url = collection_url if collection_url else self.get_collection_url(collection, collection_data)
        if url is None:
            return None
        links, next_page = self.__parse_page__(url, self.parse_acollection)
        if links.has_key(channel_name):
            return links[channel_name]
        while next_page:
            nlinks, next_page = self.__parse_page__(next_page, self.parse_acollection)
            if nlinks.has_key(channel_name):
                return nlinks[channel_name]
        return None


    def get_channel_id(self, collection, channel_name, collection_url=None, collection_data=None, channel_data=None):
        url = self.get_channel_url(collection, channel_name, collection_url, collection_data, channel_data)
        params = parse_qs(urlparse(url).query)
        return params['id'][0]


    def get_channel_list(self, collection, url=None, collection_data=None):
        if url is None:
            url = self.get_collection_url(collection, collection_data)
        links, next_page = self.__parse_page__(url, self.parse_acollection)
        while next_page:
            nlinks, next_page = self.__parse_page__(next_page, self.parse_acollection)
            links.update(nlinks)
        return links


    def get_links(self, channel_name=None, channel_url=None, channel_data=None):

        def parse_alinks(doc):
            return [urljoin(MYVIDSTER_URL, a.get('href')) for a in doc.cssselect('form#contentList * a')
                    if a.text_content().strip().lower().startswith("view")]

        if channel_name is None and channel_url is None:
            raise MissingParameterException('At least one of channel_name or channel_url parameters must be provided')
        if channel_url is None:
            channel_url = self.get_channel_url(channel_name, channel_data=channel_data)
        links, next_page = self.__parse_page__(channel_url, parse_alinks)
        while next_page:
            nlinks, next_page = self.__parse_page__(next_page, parse_alinks)
            links.extend(nlinks)
        return links


    def __read_bookmark_data__(self, link):
        response = self.__br.open(link)
        content = response.read()
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
            block_html = tostring(videoblock[0], method='html'). \
                replace(
                '\nYour browser does not support inline frames or is currently configured not to display inline frames.\n',
                '')
        detlist = doc.cssselect('div.details_video')
        date_, link_, description_ = None, None, None
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
        tags = [a.text_content().strip() for a in doc.cssselect('a.tag_cloud')]
        data = {'title': title_, 'collection': collection, 'channel': channel,
                    'date': date_, 'link': link_, 'description': description_, 'tags': tags,
                    'block_html': block_html}
        return data


    def get_all_bookmarks(self, links, pause=True, batch_size=50, time_=120):
        if not self.loggedin:
            raise NotConnectedException('You must call login() in order to use this method!')
        data = {}
        progbar = SimpleProgressBar(len(links), width=5)
        print 'Reading links and retrieving data...'
        for i in xrange(0, len(links)):
            link = links[i]
            data[link.split('/')[-1]] = self.__read_bookmark_data__(link)
            progbar.update(i)
            if pause and i > 0 and i % batch_size == 0:
                if not time_ is None and time_ > 0:
                    progbar.pause(time_)
        progbar.finish()
        print 'Finished'
        return data


    def insert_entry(self, channel_id, url, access='public', embed_code=None):
        access_type = 0
        if access == 'public':
            access_type = 0
        elif access == 'private':
            access_type = 1
        elif access == 'adult':
            access_type = 2
        params = {'action' : 'insert', 'email' : self.user,
                  'password' : hashlib.sha1(self.password).hexdigest(),
                  'channel_id': channel_id, 'url': url,
                  'access': access_type, 'embed': embed_code}
        try:
            r = requests.get(MYVIDSTER_URL + 'user/api.php?' + urllib.urlencode(params))
            tree = ElementTree.fromstring(r.content)
            root = tree.find('video_details')
            status = root.findtext('status')
            if status != 'Success':
                raise RequestProcessingException(status)
            else:
                return {'video_id': root.findtext('video_id'),
                        'title': root.findtext('title'),
                        'description': root.findtext('description'),
                        'source': url}
        except RequestException as e:
            print "Error inserting '%s'" % url


    def fetch_video_info(self, video_id):
        params = {'action': 'fetch', 'email': self.user,
                  'password': hashlib.sha1(self.password).hexdigest(),
                  'video_id': video_id}
        try:
            r = requests.get(MYVIDSTER_URL + 'user/api.php?' + urllib.urlencode(params))
            tree = ElementTree.fromstring(r.content)
            root = tree.find('video_details')
            return {'video_id': root.findtext('video_id'),
                        'title': root.findtext('title'),
                        'description': root.findtext('description'),
                        'source': root.findtext('source')}
        except RequestException as e:
            print "Error retrieving information of '%s'" % video_id
