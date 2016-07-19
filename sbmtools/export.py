
import io
import json

def export_json(items, filename):
    with io.open(filename, 'w', encoding='utf8') as outfile:
        outfile.write(unicode(json.dumps(items, ensure_ascii=False, indent=2)))


