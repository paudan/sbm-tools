# -*- coding: utf-8 -*-

import json
import urllib, urllib2
from urllib2 import HTTPError, URLError
import webbrowser
import requests
from requests.exceptions import RequestException
from configparser import ConfigParser

PINTEREST_OAUTH = "https://api.pinterest.com/oauth/?"
PINTEREST_TOKEN = "https://api.pinterest.com/v1/oauth/token?"
PINTEREST_BOARDS = "https://api.pinterest.com/v1/boards/"
PINTEREST_PINS = "https://api.pinterest.com/v1/pins/"

class PinterestAPI:

    def __init__(self, config):
        self.token = None
        conf = ConfigParser()
        conf.read(config)
        self.appid = conf.get('pinterest', 'appid')
        self.secret = conf.get('pinterest', 'secret')
        self.redirect = conf.get('pinterest', 'redirect_uri')

    def login(self):
        params = {'response_type': 'code',
                  'redirect_uri' : self.redirect,
                  'client_id' : self.appid,
                  'client_secret:' : self.secret,
                  'scope': 'read_public,write_public'}
        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
        webbrowser.open(PINTEREST_OAUTH + urllib.urlencode(params))
        code = raw_input('Enter the code in the URL: ')
        params = {'client_id' : self.appid,
                  'client_secret': self.secret,
                  'grant_type': 'authorization_code',
                  'code': code}
        r = requests.post(PINTEREST_TOKEN + urllib.urlencode(params))
        content = r.json()
        self.token = content['access_token']

    def __check_token(self):
        if self.token is None:
            print('You have not provided access to ypur Pinterest account. You must run login procedure first')
            return False
        return True

    def check_board_exists(self, user, board_name):
        """
        Check if particular pinterest board exists for particular user.
        Return the name of the board which cane be used in Pinterest API, or None, if no such board has been found
        Note, that it does not take into account private boards!
        """
        if not self.__check_token():
            return None
        name = '%s/%s' % (user, board_name)
        params = {'access_token': self.token}
        r = requests.get(PINTEREST_BOARDS + name + '?' + urllib.urlencode(params))
        if r.json().has_key('data'):
            split = r.json()['data']['url'].split('/')
            # Return board name
            return '/'.join(split[-3:-1])
        else:
            return None


    def create_board(self, board_name, user=None, check_exists=True):
        """
        Create a new board for the current user. It may also check for existing boards
        (note, that user parameter must be passed); if one is found, then new board is not
        created and the currently existing one is returned
        """
        if not self.__check_token():
            return None
        if check_exists and user is not None:
            searched = '%s/%s' % (user, board_name)
            found = self.check_board_exists(user, board_name)
            if searched == found:
                return found
        params = {'access_token': self.token, 'name' : board_name}
        r = requests.post(PINTEREST_BOARDS + '?' + urllib.urlencode(params))
        split = r.json()['data']['url'].split('/')
        # Return created board name
        return '/'.join(split[-3:-1])


    def import_items(self, items, board_name):
        if not self.__check_token():
            return None, None
        imported = not_imported = []
        for item in items:
            imgid = self.post_single_picture(item[1], item[0], board_name)
            if imgid:
                imported.append(item)
            else:
                not_imported.append(item)
        return imported, not_imported


    def post_single_picture(self, url, img_name, board_name, link=None):
        params = {'access_token': self.token, 'board' : board_name,
                  'note': img_name.encode('utf-8'),
                  'link': link if link is not None else url,
                  'image_url': url }
        print "Posting image'%s'" % url
        result = None
        try:
            r = requests.post(PINTEREST_PINS + '?' + urllib.urlencode(params))
            result = r.json()
        except RequestException as e:
            print "Error importing '%s'" % url
        if result and result.has_key('data'):
            return result['data']['id']
        else:
            return None

