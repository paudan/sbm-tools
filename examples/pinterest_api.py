import sys
sys.path.insert(0, '../')

from sbmtools.pinterest import PinterestAPI

user = 'dpaul82'

api = PinterestAPI(config='../../config.ini')
api.login()
print api.get_board_info(user, 'cars')
print api.get_user_info(user=user)
# print api.get_board_suggestions()
print 'User %s likes:' % user
print api.get_user_likes()
# print 'User %s pins:' % user
# print api.get_user_pins()

query = "science"
print 'Entries of {0} in board data'.format(query)
print api.query_boards_data(query)
print 'Entries of {0} in pins data'.format(query)
print api.query_pins_data(query)

pin_id = '475552041883020131'
print api.check_pin_exists(pin_id)
print api.get_pin_info(pin_id)


