# -*- coding: utf-8 -*-

__author__ = 'Paulius Danenas'

import json
import urllib, urllib2
from urllib2 import HTTPError, URLError
from configparser import ConfigParser

DIIGO_API_URL = 'https://secure.diigo.com/api/v2/bookmarks'

class DiigoAPI:

    def __init__(self, config):
        conf = ConfigParser()
        conf.read(config)
        self.user = conf.get('diigo', 'user')
        self.password = conf.get('diigo', 'password')
        self.key = conf.get('diigo', 'key')
        self.filter = conf.get('diigo', 'filter')
        self.loggedin = False

    def login(self):
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, DIIGO_API_URL, self.user, self.password)
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)
        self.loggedin = True

    def get_bookmarks(self, tags):
        items = []
        if not self.loggedin:
            self.login()
        for tag in tags:
            print 'Exporting tag %s..' % tag
            more_output = 1
            start_ = 0
            while more_output > 0:
                try:
                    params = {'key': self.key, 'user': self.user, 'filter': self.filter,
                              'tags': tag, 'count': 100, 'start' : start_}
                    url = DIIGO_API_URL + '?' + urllib.urlencode(params)
                    req = urllib2.urlopen(url)
                    content =req.read().decode('utf-8')
                    output = json.loads(content)
                    more_output = len(output)
                    start_ += 100
                    items.extend([link for link in output])
                except URLError as e:
                    print 'Error while connecting: %s' % e.reason
        return items
