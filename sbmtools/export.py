import csv
import io
import json

def export_json(items, filename):
    with io.open(filename, 'w', encoding='utf8') as outfile:
        outfile.write(unicode(json.dumps(items, ensure_ascii=False, indent=2)))


def export_netscape(items, filename):
    with io.open(filename, 'w', encoding='utf8') as outfile:
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
            outfile.write(u'<DT><A HREF="{0}" LAST_MODIFIED="" SHORTCUTURL="{1}" ID="">{2}</A><DD>\n'.
                          format(item['link'], ' '.join(item['tags']), unicode(item['description'])))
        outfile.write(u'</DL><p></DL><p>')


def export_csv(items, filename):
    with open(filename, 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_MINIMAL, quotechar='"')
        writer.writerow(['title','url','tags','description','comments','annotations'])
        for item in items.values():
            writer.writerow([item['description'].encode('utf-8'), item['link'],
                             ' '.join(item['tags']).encode('utf-8'), None, None, None])

