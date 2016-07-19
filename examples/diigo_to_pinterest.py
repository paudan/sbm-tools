# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '../')

from sbmtools.diigo import DiigoAPI
from sbmtools.pinterest import PinterestAPI

CONFIG = 'config.ini'
tags = ['cars', 'single_pictures']
board_to_import = 'cars'
user = 'user'

print 'Exporting list of image links from Diigo...'
api = DiigoAPI(config=CONFIG)
items = api.get_bookmarks(tags)
items = [(link['title'], link['url']) for link in items]
print 'The number of exported links is %d'  % len(items)
pinterest_api = PinterestAPI(config=CONFIG)
pinterest_api.login()
board_name = pinterest_api.create_board(board_name = board_to_import,
                                        user=user, check_exists=True)
imported, not_imported = pinterest_api.import_items(items, board_name)
print 'Imported total: ', len(imported)
print not_imported





