#!/usr/bin/env python3

"""Gets the weekly play statistic from last.fm and generates
an Atom feed with the most played artists."""

# configuration
DOMAIN = 'drbeat.li'
PATH = '/lastfm.atom'
RANKS = 3
MIN_PLAYCOUNT = 2

from dataclasses import dataclass
import datetime
from itertools import groupby, islice
import urllib.parse
import sys

import xmlbuilder
import xmltramp

XHTML_NS = 'http://www.w3.org/1999/xhtml'

LASTFM_URL = 'https://ws.audioscrobbler.com/2.0/?'
LASTFM_KEY = '4605ebe7bfcaf0c1e9aa76f167da8efc'


def first_n_ranks(items, n, keyfunc):
    for key, group in islice(groupby(items, keyfunc), n):
        for i in group:
            yield i

def fetch_weekly_charts(user_id):
    params = {
        'user': user_id,
        'api_key': LASTFM_KEY,
        'method': 'user.gettopartists',
        'period': '7day',
        'limit': 200,
    }
    url = LASTFM_URL + urllib.parse.urlencode(params)
    try:
        lfm = xmltramp.load(url)
        if lfm('status') == 'ok':
            return lfm[0]   # first child element
        return lfm
    except Exception as e:
        return xmltramp.Element('error', value=str(e), attrs={'class': e.__class__.__name__})

def playcount(artist):
    """Return the play count of the artist as an int."""
    return int(str(artist.playcount))

def prune_charts(charts):
    """Remove all artists that have too few plays.
    Return True if any are left."""

    for a in charts['artist':]:
        if playcount(a) < MIN_PLAYCOUNT:
            del charts[a]
    return hasattr(charts, 'artist')


@dataclass
class Artist:
    name: str
    url: str
    playcount: int

    def as_html(self, builder):
        """Render this artist as HTML."""
        builder.a(self.name, href=self.url, _post=f' ({self.playcount})')


class Entry:
    """Holds the parsed Last.fm output and produces the charts in either
    Blosxom or ATOM format."""

    def __init__(self, charts):
        self.who = charts('user')
        self.when = datetime.datetime.now().isoformat() + 'Z'
        self.date = self.when[:10]
        self.tags = ('charts', 'music', 'last.fm')
        self.artists = [
            Artist(str(a.name), str(a.url), playcount(a))
            for a in first_n_ranks(charts['artist':], RANKS, playcount)
        ]
        self.title = f"Meist gespielte Bands vom {self.date}"

    def as_blosxom(self):
        """Render the charts as a Blosxon blog entry."""
        builder = xmlbuilder.XMLBuilder(version=None)
        self.content(builder)
        return f'{self.title}\nmeta-tags: {", ".join(self.tags)}\n\n{builder}'

    def as_atom(self):
        """Render the charts as an ATOM feed."""
        f = xmlbuilder.ATOMBuilder()
        with f.start():
            lastfm = f'http://www.last.fm/user/{self.who}'
            f.title("Meine last.fm-Hitparade")
            with f.author:
                f.name(self.who)
            f.link(href=lastfm)
            f.updated(self.when)
            f.id(f'tag:drbeat.li,2010:lastfmcharts:{self.who}')
            f.link(rel='self', href=f'http://{DOMAIN}{PATH}')
            with f.entry:
                f.title(self.title)
                f.updated(self.when)
                f.id(f'tag:{DOMAIN},{self.date}:{PATH}:{self.who}')
                f.link(rel='alternate', type='text/html',
                    href=lastfm + '/library/artists?date_preset=LAST_7_DAYS'
                )
                for term in self.tags:
                    f.category(term=term)
                with f.content(type='xhtml'), f.div(xmlns=XHTML_NS):
                    self.content(f)
        return str(f)

    def content(self, builder):
        """Render the ordered list of all artists."""
        with builder.ol:
            for artist in self.artists:
                with builder.li:
                    artist.as_html(builder)


def application(environ, start_response):
    """WSGI interface"""
    ch = fetch_weekly_charts(environ['user_id'])
    if ch._name == 'topartists' and prune_charts(ch):
        if environ.get('fmt') == 'blosxom':
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [Entry(ch).as_blosxom()]
        else:
            start_response('200 OK', [('Content-Type', 'application/atom+xml')])
            return [Entry(ch).as_atom()]
    else:
        start_response('404 Not found', [('Content-Type', 'text/xml')])
        environ['rc'] = 1
        return [ch.__repr__(1, 1)]

if __name__ == '__main__':
    """command-line interface"""
    import getopt
    import os
    from wsgi import WSGIWrapper
    environ = {'rc': 0, 'fmt': 'atom', 'user_id': 'bbolli'}
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'bn:')
    except getopt.GetoptError:
        prog = sys.argv[0].split(os.sep)[-1]
        print(f"Usage: {prog} [-b] [-n ranks]")
        sys.exit(1)
    for o, v in opts:
        if o == '-b':
            environ['fmt'] = 'blosxom'
        elif o == '-n':
            RANKS = int(v)
    if len(args) == 1:
        environ['user_id'] = args[0]
    WSGIWrapper().run(application, environ)
