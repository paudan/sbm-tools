import csv
import io
import json
from lxml.html import document_fromstring


class CoreAPI:

    def export_json(self, items, filename):
        with io.open(filename, 'w', encoding='utf8') as outfile:
            outfile.write(unicode(json.dumps(items, ensure_ascii=False, indent=2)))


    def export_netscape(self, items, filename):
        with io.open(filename, 'w', encoding='utf-8') as outfile:
            outfile.write(u"""
            <!DOCTYPE NETSCAPE-Bookmark-file-1>
             <META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
             <TITLE>Bookmarks</TITLE>
             <H1 LAST_MODIFIED="">Bookmarks</H1>
             <DL><p>
             <DT><H3 ID="">Diigo Bookmarks</H3>
             <DL><p>
            """)
            for item in items.values():
                title = unicode(item['description']) if item.has_key('description') \
                    else unicode(item['title']) if item.has_key('title') else u''
                outfile.write(u'<DT><A HREF="{0}" LAST_MODIFIED="" SHORTCUTURL="{1}" ID="">{2}</A><DD>\n'.
                              format(item['link'], ', '.join(item['tags']), title))
            outfile.write(u'</DL><p></DL><p>')


    def export_csv(self, items, filename):
        with open(filename, 'wb') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL, quotechar='"')
            writer.writerow(['title','url','tags','description','comments','annotations'])
            for item in items.values():
                title = item['description'].encode('utf-8') if item.has_key('description') \
                    else item['title'].encode('utf-8') if item.has_key('title') else None
                writer.writerow([title, item['link'].encode('utf-8'),
                                ', '.join(item['tags']).decode('utf-8'), None, None, None])


    def import_netscape(self, filename):
        content = io.open(filename, 'r', encoding='utf8').read()
        doc = document_fromstring(content)
        return [{'title' : a.text_content().strip(),
                 'tags': a.get('shortcuturl').split() if a.get('shortcuturl') else [],
                 'link': a.get('href')}
                for a in doc.cssselect('a')]


    def import_csv(self, filename):
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile, dialect='excel', delimiter=',',
                                quoting=csv.QUOTE_MINIMAL, quotechar='"')
            next(reader)
            return [{'title' : row[0].decode('utf-8'),
                     'link': row[1].decode('utf-8'),
                     'tags': row[2].decode('utf-8').split() if row[2] else [] }
                    for row in reader]
