import sys
sys.path.insert(0, '../')

from sbmtools.myvidster import MyVidsterAPI
from sbmtools.export import export_json

api = MyVidsterAPI('../../config.ini')
api.login()
data = api.get_all_bookmarks()
export_json(data, '../../output.json')
