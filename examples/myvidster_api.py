import sys
sys.path.insert(0, '../')

from sbmtools.myvidster import MyVidsterAPI

api = MyVidsterAPI('../../config.ini')
print api.fetch_video_info('54069817')

url = 'https://www.youtube.com/watch?v=8pDm_kH4YKY'
api.login()  # Must be called if you want to retrieve channel ID by name
channel_id = api.get_channel_id('study & education', 'java')
print api.insert_entry(channel_id, url)
