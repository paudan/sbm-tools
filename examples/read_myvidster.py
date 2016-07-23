import sys
sys.path.insert(0, '../')

from sbmtools.myvidster import MyVidsterAPI
from sbmtools.export import export_json

category = 'category'
channel = 'channel'

api = MyVidsterAPI('../../config.ini')
api.login()
channel_url = api.get_channel_url('category', 'channel')
print channel_url
links = api.get_links(channel_url=channel_url)
data = api.get_all_bookmarks(links)
export_json(data, '../../myvidster.json')

