import io
import json
import sys
sys.path.insert(0, '../')

from sbmtools.export import export_netscape, export_csv

filename = '../../myvidster.json'

with io.open(filename, 'r', encoding='utf8') as csvfile:
    links = json.load(csvfile, encoding='utf8')
    export_netscape(links, '../../myvidster.html')
    export_csv(links, '../../myvidster.csv')