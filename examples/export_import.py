import io
import json
import sys
sys.path.insert(0, '../')

from sbmtools.core import CoreAPI

filename = '../../visualizeus.json'
netscape_file=  '../../visualizeus.html'
csv_file = '../../visualizeus.csv'

with io.open(filename, 'r', encoding='utf8') as csvfile:
    links = json.load(csvfile, encoding='utf8')
print 'Number of loaded links:', len(links)
api = CoreAPI()
api.export_netscape(links, netscape_file)
api.export_csv(links, csv_file)
links_n = api.import_netscape(netscape_file)
print 'Number of imported links from Netscape file:', len(links_n)
links_csv = api.import_csv(csv_file)
print 'Number of imported links from CSV file:', len(links_csv)

