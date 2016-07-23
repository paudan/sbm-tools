import sys
sys.path.insert(0, '../')

from sbmtools.delicious import DeliciousAPI

api = DeliciousAPI(config='../../config.ini')
print api.get_tags()
print api.get_url_info('http://tullo.ch/articles/svm-py/')
tag = 'svm'
print 'All bookmarks with tag %s' % tag
print api.get_bookmarks_with_tag(tag)
print 'Popular bookmarks'
print api.get_popular_bookmarks()
