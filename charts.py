#!/usr/bin/env python
# encoding: utf-8

"""Gets the weekly play statistic from last.fm and generates
an Atom feed with the most played artists."""

# configuration
DOMAIN = 'drbeat.li'
PATH = '/lastfm.atom'
RANKS = 3
MIN_PLAYCOUNT = 2

import sys, datetime
from itertools import groupby, islice
from contextlib import nested

import xmltramp, xmlbuilder

ATOM_NS = 'http://www.w3.org/2005/Atom'
XHTML_NS = 'http://www.w3.org/1999/xhtml'

def first_n_ranks(items, n, keyfunc):
    for key, group in islice(groupby(items, keyfunc), n):
        for i in group:
            yield i

def fetch_weekly_charts(user_id):
    url = 'http://ws.audioscrobbler.com/2.0/user/%s/weeklyartistchart.xml' % user_id
    try:
        return xmltramp.load(url)
    except Exception, e:
        return xmltramp.Element('error', value=str(e), attrs={'class': e.__class__.__name__})

def playcount(artist):
    return int(str(artist.playcount))

def prune_charts(charts):
    for a in charts['artist':]:
        if playcount(a) < MIN_PLAYCOUNT:
            del charts[a]
    return hasattr(charts, 'artist')


class Entry:
    def __init__(self, charts):
        self.who = charts('user')
        self.ts = datetime.datetime.utcfromtimestamp(int(charts('to')))
        self.when = self.ts.isoformat() + 'Z'
        self.tags = ('charts', 'music', 'last.fm')
        self.artists = [dict(name=unicode(a.name), url=str(a.url), playcount=playcount(a))
            for a in first_n_ranks(charts['artist':], RANKS, playcount)
        ]
        self.title = u"Meist gespielte Bands vom %s" % self.when[:10]

    def as_blosxom(self):
        f = xmlbuilder.builder(version=None)
        self.content(f)
        return u'\n'.join([self.title,
            'meta-tags: ' + ', '.join(self.tags), '',
            unicode(f)
        ]).encode('utf-8')

    def as_atom(self):
        f = xmlbuilder.builder()
        with f.feed(xmlns=ATOM_NS):
            lastfm = 'http://www.last.fm/user/%s' % self.who
            f.title(u"Meine last.fm-Hitparade")
            with f.author:
                f.name(self.who)
            f.link(None, href=lastfm)
            f.updated(self.when)
            f.id('tag:drbeat.li,2010:lastfmcharts:%s' % self.who)
            f.link(None, rel='self', href='http://%s%s' % (DOMAIN, PATH))
            with f.entry:
                f.title(u"Meist gespielte Bands vom %s" % self.when[:10])
                f.updated(self.when)
                f.id('tag:%s,%s:%s:%s' % (DOMAIN, self.when[:10], PATH, self.who))
                f.link(None, rel='alternate', type='text/html', href=lastfm + '/charts?charttype=weekly')
                for term in self.tags:
                    f.category(None, term=term)
                with nested(f.content(type='xhtml'), f.div(xmlns=XHTML_NS)):
                    self.content(f)
        return str(f)

    def content(self, f):
        with f.ol:
            for artist in self.artists:
                with f.li:
                    f.a(artist['name'], href=artist['url'])
                    f['(%s)' % artist['playcount']]


def application(environ, start_response):
    """WSGI interface"""
    user_id = environ.get('user_id') or 'bbolli'
    ch = fetch_weekly_charts(user_id)
    if ch._name == 'weeklyartistchart' and prune_charts(ch):
        if environ.get('fmt') == 'blosxom':
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [Entry(ch).as_blosxom()]
        else:
            start_response('200 OK', [('Content-Type', 'application/atom+xml')])
            return [Entry(ch).as_atom()]
    else:
        start_response('404 Not found', [('Content-Type', 'text/xml')])
        environ['rc'] = 1
        return [ch.__repr__(1, 1).encode('utf-8') + '\n']

if __name__ == '__main__':
    """command-line interface"""
    from wsgi import WSGIWrapper
    environ = {'rc': 0}
    if '-b' in sys.argv:
        sys.argv.remove('-b')
        environ['fmt'] = 'blosxom'
    if len(sys.argv) == 2:
        environ['user_id'] = sys.argv[1]
    WSGIWrapper().run(application, environ)
