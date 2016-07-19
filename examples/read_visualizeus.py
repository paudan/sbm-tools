
import sys
sys.path.insert(0, '../')
from sbmtools.visualizeus import VisualizeUsAPI
from sbmtools.export import export_json

vapi = VisualizeUsAPI('../../config.ini')
items, tags = vapi.get_items()
print 'Retrieved total items: ', len(items)
export_json(items, '../../visualizeus.json')
