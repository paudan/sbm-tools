# -*- coding: utf-8 -*-

import urllib
import urllib2
import webbrowser
from functools import wraps
import requests
from configparser import ConfigParser
from requests.exceptions import RequestException
from .core import CoreAPI
from .exceptions import TokenNotFoundException, ResourseNotExistException

PINTEREST_OAUTH = "https://api.pinterest.com/oauth/?"
PINTEREST_TOKEN = "https://api.pinterest.com/v1/oauth/token?"
PINTEREST_BOARDS = "https://api.pinterest.com/v1/boards/"
PINTEREST_PINS = "https://api.pinterest.com/v1/pins/"
PINTEREST_USERS = "https://api.pinterest.com/v1/users/"
PINTEREST_USERBOARDS = "https://api.pinterest.com/v1/users/"
PINTEREST_USER = "https://api.pinterest.com/v1/me/"
PINTEREST_SEARCH = PINTEREST_USER + 'search/'
PINTEREST_FOLLOW = PINTEREST_USER + 'following/'

ATTR_BOARD = 'id,name,url,counts,created_at,description,creator,privacy,reason,image'
ATTR_PINS = 'id,link,note,url,attribution,board,color,counts,created_at,creator,image,media,metadata,original_link'
ATTR_USER = 'first_name,id,last_name,url,account_type,bio,counts,created_at,image,username'


def check_token(func):
    @wraps(func)
    def func_wrapper(self, *args, **kwargs):
        if self.token is None:
            raise TokenNotFoundException('You have not provided access to ypur Pinterest account. '
                                         'You must run login procedure first')
        return func(self, *args, **kwargs)

    return func_wrapper


class PinterestAPI(CoreAPI):
    def __init__(self, config):
        self.token = None
        conf = ConfigParser()
        conf.read(config)
        self.appid = conf.get('pinterest', 'appid')
        self.secret = conf.get('pinterest', 'secret')
        self.redirect = conf.get('pinterest', 'redirect_uri')


    def login(self):
        params = {'response_type': 'code',
                  'redirect_uri': self.redirect,
                  'client_id': self.appid,
                  'client_secret:': self.secret,
                  'scope': 'read_public,write_public'}
        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
        webbrowser.open(PINTEREST_OAUTH + urllib.urlencode(params))
        code = raw_input('Enter the code in the URL: ')
        params = {'client_id': self.appid,
                  'client_secret': self.secret,
                  'grant_type': 'authorization_code',
                  'code': code}
        r = requests.post(PINTEREST_TOKEN + urllib.urlencode(params))
        content = r.json()
        if content and content.has_key('access_token'):
            self.token = content['access_token']


    @check_token
    def check_board_exists(self, user, board_name):
        """
        Check if particular pinterest board exists for particular user.
        Return the name of the board which cane be used in Pinterest API, or None, if no such board has been found
        Note, that it does not take into account private boards!
        """
        name = '%s/%s' % (user, board_name)
        params = {'access_token': self.token}
        r = requests.get(PINTEREST_BOARDS + name + '?' + urllib.urlencode(params))
        if r.json().has_key('data'):
            split = r.json()['data']['url'].split('/')
            # Return board name
            return '/'.join(split[-3:-1])
        else:
            return None


    @check_token
    def create_board(self, board_name, user=None, check_exists=True):
        """
        Create a new board for the current user. It may also check for existing boards
        (note, that user parameter must be passed); if one is found, then new board is not
        created and the currently existing one is returned
        """
        if check_exists and user is not None:
            searched = '%s/%s' % (user, board_name)
            found = self.check_board_exists(user, board_name)
            if searched == found:
                return found
        params = {'access_token': self.token, 'name': board_name}
        r = requests.post(PINTEREST_BOARDS + '?' + urllib.urlencode(params))
        split = r.json()['data']['url'].split('/')
        # Return created board name
        return '/'.join(split[-3:-1])


    @check_token
    def import_items(self, items, board_name):
        imported = not_imported = []
        for item in items:
            imgid = self.post_single_picture(item[1], item[0], board_name)
            if imgid:
                imported.append(item)
            else:
                not_imported.append(item)
        return imported, not_imported


    def post_single_picture(self, url, img_name, board_name, link=None):
        params = {'access_token': self.token, 'board': board_name,
                  'note': img_name.encode('utf-8'),
                  'link': link if link is not None else url,
                  'image_url': url}
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


    @check_token
    def get_board_info(self, user, board_name):
        name = '%s/%s' % (user, board_name)
        params = {'access_token': self.token, 'fields': ATTR_BOARD}
        try:
            r = requests.get(PINTEREST_BOARDS + name + '?' + urllib.urlencode(params))
            result = r.json()
            if result and result.has_key('data'):
                return result['data']
        except RequestException as e:
            print "Error retrieving board %s info" % name
        else:
            return None


    @check_token
    def rename_board(self, user, board_name, new_name, description=None):
        assert new_name is not None
        name = '%s/%s' % (user, board_name)
        if self.check_board_exists(user, board_name) is None:
            raise ResourseNotExistException('Board %s does not exist' % name)
        params = {'access_token': self.token, 'name': new_name, 'fields': ATTR_BOARD,}
        if description:
            params['description'] = description
        try:
            r = requests.patch(PINTEREST_BOARDS + name + '?' + urllib.urlencode(params))
            result = r.json()
            if result and result.has_key('data'):
                return result['data']
        except RequestException as e:
            print "Error retrieving board %s info" % name
        else:
            return None


    @check_token
    def delete_board(self, user, board_name):
        name = '%s/%s' % (user, board_name)
        if self.check_board_exists(user, board_name) is None:
            raise ResourseNotExistException('Board %s does not exist' % name)
        params = {'access_token': self.token,}
        try:
            r = requests.delete(PINTEREST_BOARDS + name + '?' + urllib.urlencode(params))
            result = r.json()
            return result
        except RequestException as e:
            print "Error retrieving board %s info" % name


    @check_token
    def get_user_info(self, user='me', get_boards=True):
        params = {'access_token': self.token, 'fields': ATTR_USER}
        info = {}
        try:
            r = requests.get(PINTEREST_USERS + user + '?' + urllib.urlencode(params))
            result = r.json()
            info['userinfo'] = result['data'] if result and result.has_key('data') else {}
            if get_boards:
                params = {'access_token': self.token, 'fields': ATTR_BOARD,}
                r = requests.get(PINTEREST_BOARDS + user + '?' + urllib.urlencode(params))
                result = r.json()
                info['boards'] = result['data'] if result and result.has_key('data') else {}
        except RequestException as e:
            print "Error retrieving user's %s info" % user
        return info


    @check_token
    def get_board_suggestions(self, pin_id, user='me'):
        params = {'access_token': self.token, 'pin': pin_id, 'fields': ATTR_BOARD,}
        try:
            r = requests.get(PINTEREST_BOARDS + user + '/suggested/?' + urllib.urlencode(params))
            result = r.json()
            return result['data'] if result and result.has_key('data') else {}
        except RequestException as e:
            print "Error retrieving user's %s info" % user


    @check_token
    def __get_pin_info(self, url):
        params = {'access_token': self.token, 'fields': ATTR_PINS,}
        try:
            r = requests.get(url + '?' + urllib.urlencode(params))
            result = r.json()
            return result['data'] if result and result.has_key('data') else {}
        except RequestException as e:
            print "Error retrieving pins info: %s" % e.__str__()


    def get_user_likes(self):
        """
        Get the likes of the authenticated user
        """
        return self.__get_pin_info(PINTEREST_USER + 'likes/')


    def get_user_pins(self, user=None, board_name=None):
        """
        If user and board_name are not set, return pins of the authenticated user
        """
        if user is not None and board_name is not None:
            name = '%s/%s' % (user, board_name)
            if self.check_board_exists(user, board_name) is None:
                raise ResourseNotExistException('Board %s does not exist' % name)
            return self.__get_pin_info(PINTEREST_BOARDS + name + '/pins/')
        else:
            return self.__get_pin_info(PINTEREST_USER + 'pins/')


    @check_token
    def __query_data(self, query, url, fields):
        params = {'access_token': self.token, 'query': query, 'fields': fields}
        try:
            r = requests.get(url + urllib.urlencode(params))
            result = r.json()
            if result and result.has_key('data'):
                return result['data']
        except RequestException as e:
            print "Error on performiong query: %s" % e.__str__()
        else:
            return None


    def query_boards_data(self, query):
        return self.__query_data(query, PINTEREST_SEARCH + 'boards/?', ATTR_BOARD)

    def query_pins_data(self, query):
        return self.__query_data(query, PINTEREST_SEARCH + 'pins/?', ATTR_PINS)


    @check_token
    def follow_board(self, user, board_name):
        name = '%s/%s' % (user, board_name)
        if self.check_board_exists(user, board_name) is None:
            raise ResourseNotExistException('Board %s does not exist' % name)
        params = {'access_token': self.token, 'board': name}
        try:
            r = requests.post(PINTEREST_FOLLOW + 'boards/?' + urllib.urlencode(params))
            result = r.json()
            return result['data'] if result and result.has_key('data') else {}
        except RequestException as e:
            print "Error trying to follow board %s: %s" % (name, e.__str__())


    @check_token
    def follow_user(self, user):
        params = {'access_token': self.token, 'user': user}
        try:
            r = requests.post(PINTEREST_FOLLOW + 'users/?'+ urllib.urlencode(params))
            result = r.json()
            return result['data'] if result and result.has_key('data') else {}
        except RequestException as e:
            print "Error trying to follow %s: %s" % (user, e.__str__())
            return None


    @check_token
    def unfollow_board(self, user, board_name):
        name = '%s/%s' % (user, board_name)
        if self.check_board_exists(user, board_name) is None:
            raise ResourseNotExistException('Board %s does not exist' % name)
        params = {'access_token': self.token}
        try:
            r = requests.delete(PINTEREST_FOLLOW + 'boards/' + name + '/?' + urllib.urlencode(params))
            return len(r.json()) == 0
        except RequestException as e:
            print "Error trying to follow board %s: %s" % (name, e.__str__())
            return None


    @check_token
    def unfollow_user(self, user):
        params = {'access_token': self.token}
        try:
            r = requests.delete(PINTEREST_FOLLOW + 'users/' + user + '/?' + urllib.urlencode(params))
            return len(r.json()) == 0
        except RequestException as e:
            print "Error trying to follow user %s: %s" % (user, e.__str__())
            return None


    @check_token
    def __get_user_info(self, url, fields=None):
        params = {'access_token': self.token, 'fields': ATTR_USER}
        if fields:
            params['fields'] = fields
        try:
            r = requests.get(url + urllib.urlencode(params))
            result = r.json()
            return result['data'] if result and result.has_key('data') else {}
        except RequestException as e:
            print "Error retrieving user information: %e" % e.__str__()
            return None


    def get_followers(self):
        return self.__get_user_info(PINTEREST_USER + 'followers?', fields=ATTR_USER)

    def get_followed_boards(self):
        return self.__get_user_info(PINTEREST_FOLLOW + 'boards/?')

    def get_followed_interests(self):
        return self.__get_user_info(PINTEREST_FOLLOW + 'interests/?')

    def get_followed_users(self):
        return self.__get_user_info(PINTEREST_FOLLOW + 'users/?')


    @check_token
    def update_pin(self, pin_id, board_name=None, link=None, description=None):
        params = {'access_token': self.token, 'board': board_name,
                  'link': link, 'note': description.encode('utf-8'),
                  'fields': ATTR_PINS}
        try:
            r = requests.patch(PINTEREST_PINS + pin_id + '?' + urllib.urlencode(params))
            result = r.json()
            return result['data'] if result and result.has_key('data') else {}
        except RequestException as e:
            print "Error updating pin '%s'" % pin_id


    @check_token
    def delete_pin(self, pin_id):
        if self.check_pin_exists(pin_id) is None:
            raise ResourseNotExistException('Pin %s does not exist' % pin_id)
        params = {'access_token': self.token}
        try:
            r = requests.delete(PINTEREST_PINS + pin_id + '?' + urllib.urlencode(params))
            return len(r.json()) == 0
        except RequestException as e:
            print "Error trying to follow board %s: %s" % (name, e.__str__())
            return None


    @check_token
    def check_pin_exists(self, pin_id):
        params = {'access_token': self.token}
        try:
            r = requests.get(PINTEREST_PINS + pin_id+ '?' + urllib.urlencode(params))
            result = r.json()
            return result and result['data']['id'] is not None
        except RequestException as e:
            print "Error retrieving pin %s data: %s" % (pin_id, e.__str__())
            return None


    @check_token
    def get_pin_info(self, pin_id):
        params = {'access_token': self.token, 'fields': ATTR_PINS}
        try:
            r = requests.get(PINTEREST_PINS + pin_id + '?' + urllib.urlencode(params))
            result = r.json()
            return result['data'] if result and result.has_key('data') else {}
        except RequestException as e:
            print "Error retrieving pin %s data: %s" % (pin_id, e.__str__())
            return None

