import hashlib
import json
import urllib2
from configparser import ConfigParser
from .core import CoreAPI
from .exceptions import URLNotFoundException, AuthorizationException, NotConnectedException, RequestProcessingException

DELICIOUS_URL = 'http://del.icio.us'
API_URL = 'http://feeds.del.icio.us/v2/json/'


class DeliciousAPI(CoreAPI):
    def __init__(self, config):
        conf = ConfigParser()
        conf.read(config)
        self.user = conf.get('delicious', 'user')
        self.password = conf.get('delicious', 'password')

    def get(self, url):
        handlers = []
        pwd_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pwd_mgr.add_password(None, DELICIOUS_URL, self.user, self.password)
        basic_auth_handler = urllib2.HTTPBasicAuthHandler(pwd_mgr)
        handlers.append(basic_auth_handler)
        opener = urllib2.build_opener(*handlers) if handlers else urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Firefox')]
        try:
            f = opener.open(url)
            result = f.read()
            f.close()
            return result
        except urllib2.HTTPError, e:
            if e.code == 301 or e.code == 302 or e.code == 404:
                raise URLNotFoundException, "Error %s: URL not found" % e.code
            elif e.code == 401 or e.code == 403:
                raise AuthorizationException, "Error %s: authentication failed" % e.code
            elif e.code == 500 or e.code == 503 or e.code == 999:
                raise RequestProcessingException, "Error %s: unable to process request" % e.code
            else:
                raise NotConnectedException, "Error %s: unknown" % e.code

    def get_tags(self):
        try:
            return json.loads(self.get(API_URL + 'tags/' + self.user))
        except TypeError:
            pass
        return {}

    def get_url_info(self, url):
        data = self.get(API_URL + 'url/' + hashlib.md5(url).hexdigest())
        response = json.loads(data)
        if not response:
            return {}
        response = response[0]
        return {'title': response['d'] or u"", 'tags': response['t'], 'user': response['a'],
                'date': response['dt']}

    def __get_links(self, url, count=None):
        data = self.get(url + ('?count=%d' % count if count else ''))
        response = json.loads(data)
        if not response:
            return None
        return [{'title': item['d'], 'tags': item['t'], 'user': item['a'], 'date': item['dt']}
                for item in response]

    def get_bookmarks(self):
        return self.__get_links(API_URL + self.user)

    def get_bookmarks_with_tag(self, tag):
        return self.__get_links(API_URL + self.user + '/' + tag)

    def get_popular_bookmarks(self):
        return self.__get_links(API_URL + 'popular')

    def get_followed_users(self):
        data = self.get(API_URL + 'following/' + self.user)
        return json.loads(data)

    def get_followers(self):
        data = self.get(API_URL + 'followers/' + self.user)
        return json.loads(data)