import random
import urllib.request
import zipfile
from io import BytesIO
from xml.etree.ElementTree import parse


def scrape(m_type):
    headers = {'User-Agent': ' Mozilla/5.0'}
    url = 'http://predb.me/?cats={}&rss'
    req = urllib.request.Request(url=url.format(m_type), headers=headers)
    handler = urllib.request.urlopen(req)
    for item in parse(handler).iterfind('channel/item'):
        yield item.findtext('title') + random.choice(extensions)


# Create an in-memory ZIP file
zip_io = BytesIO()
zip_data = zipfile.ZipFile(
    file=zip_io,
    mode='w',
    compression=zipfile.ZIP_DEFLATED,
    allowZip64=False
)

# Grab releases from predb RSS feed, add them to in-memory zip file
extensions = ['.mkv', '.wmv', '.mp4', '.avi', '.m4v']
for title in scrape('movies-hd'):
    zip_data.writestr('movies/' + title, '')
for title in scrape('tv-hd'):
    zip_data.writestr('tv/' + title, '')
zip_data.close()
with open('testFiles.zip', 'wb') as f:
    f.write(zip_io.getvalue())
