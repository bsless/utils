'''donwload mp3s from bandcamp url
this was an exercise I was drawn into when I needed some mp3s to test cmus
on a vm'''


import re
import os
import sys
import logging
import urllib.request
import json
from distutils.util import strtobool
import argparse
import threading


CONSOLELEVEL = logging.DEBUG
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(CONSOLELEVEL)
FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
CH = logging.StreamHandler()
CH.setLevel(CONSOLELEVEL)
CH.setFormatter(FORMATTER)
LOGGER.addHandler(CH)

def get_parser():
    '''get parser for bandcamp downloader
    accepts:
        url (mandatory)
        -force (optional)'''
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument(
        '-force',
        action='store_true',
        default=False,
        help='force re-download and overwrite cache'
    )
    return parser

def user_yes_no_query(question):
    '''prompt user for y/n'''
    sys.stdout.write('%s [y/n]\n' % question)
    while True:
        try:
            return strtobool(input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'.\n')

def r_u_asshole():
    '''ask the user if he's a tit'''
    question = '''Dear User
    I couldn't help but notice you took the time and effort to go scrape
    a url of an artist you like from bandcamp for their mp3s.
    If you like them enough to bother,
    how about you go purchase the album instead?'''
    answer = user_yes_no_query(question)
    if answer:
        print('Thanks buddy')
        sys.exit(0)
    else:
        pass

def download_webpage(url):
    '''Downloads and caches url'''
    cache = os.path.join('/tmp', url.split('/')[-1]+'.html')
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
    values = {'name': 'Michael Foord',
              'location': 'Northampton',
              'language': 'Python'}
    headers = {'User-Agent': user_agent}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(url, data, headers)
    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')
    if html:
        with open(cache, 'w') as html_fh:
            html_fh.write(html)
    else:
        LOGGER.error('failed to get non-empty reply')
        reply = user_yes_no_query('try again?')
        if reply:
            html = download_webpage(url)
        else:
            sys.exit(-1)
    return html

def get_webpage(url, force=False):
    '''get webpage html fromm url or cached'''
    LOGGER.debug(msg='getting url: %s' %(url))
    cache = os.path.join('/tmp', url.split('/')[-1]+'.html')
    if not force:
        if os.path.exists(cache):
            filesize = os.stat(cache).st_size
            if filesize > 0:
                with open(cache) as html_fh:
                    html = html_fh.read()
            else:
                LOGGER.warning(msg='cache file %s is size 0' %(cache))
                reply = user_yes_no_query('delete cache and try again?')
                if reply:
                    os.remove(cache)
                    html = get_webpage(url)
                else:
                    LOGGER.warning(msg='program aborting, nothing to do')
                    sys.exit(-1)
        else:
            html = download_webpage(url)
    else:
        html = download_webpage(url)

    return html

def get_bandcamp_tracks(html):
    '''finds trackinfo in bandcamp html and parse json object
    returns list of dictionaries'''
    trackinfo = re.findall(
        'trackinfo:.*\n', html
    )[0].replace(',\n', '').replace('trackinfo:', '').strip()
    tracks = json.loads(trackinfo)
    return tracks

def download(filename, url):
    '''download filename from url'''
    LOGGER.info(msg='Downloading %s from %s' %(filename, url))
    try:
        urllib.request.urlretrieve(url, filename)
        LOGGER.info(msg='Done downloading %s' %(filename))
    except FileNotFoundError:
        LOGGER.error(msg='FAILED downloading %s from %s' %(filename, url))

def tracks_downloader(tracks):
    '''download tracks'''
    threads = []
    for track in tracks:
        file_http = ':'.join(['http', track['file']['mp3-128']])
        title = '.'.join([track['title'].replace('/', ' -'), 'mp3'])
        thread = threading.Thread(
            target=download,
            args=(title, file_http,)
        )
        threads.append(thread)
    #########
    _ = [thread.start() for thread in threads]


def main():
    '''main program'''
    r_u_asshole()
    parser = get_parser()
    args = parser.parse_args()
    url = args.url
    html = get_webpage(url, args.force)
    tracks = get_bandcamp_tracks(html)
    tracks_downloader(tracks)

if __name__ == '__main__':
    main()
