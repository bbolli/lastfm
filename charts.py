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

def make_feed(charts):
    f = xmlbuilder.builder()
    with f.feed(xmlns=ATOM_NS):
        who = charts('user')
        when = datetime.datetime.utcfromtimestamp(int(charts('to')))
        when = when.isoformat() + 'Z'
        lastfm = 'http://www.last.fm/user/%s' % who
        f.title(u"Meine last.fm-Hitparade")
        with f.author:
            f.name(who)
        f.link(None, href=lastfm)
        f.updated(when)
        f.id('tag:drbeat.li,2010:lastfmcharts:%s' % who)
        f.link(None, rel='self', href='http://%s%s' % (DOMAIN, PATH))
        with f.entry:
            f.title(u"Meist gespielte Bands vom %s" % when[:10])
            f.updated(when)
            f.id('tag:%s,%s:%s:%s' % (DOMAIN, when[:10], PATH, who))
            f.link(None, rel='alternate', type='text/html', href=lastfm + '/charts?charttype=weekly')
            for term in ('charts', 'music', 'last.fm'):
                f.category(None, term=term)
            with nested(f.content(type='xhtml'), f.div(xmlns=XHTML_NS), f.ol):
                for artist in first_n_ranks(charts['artist':], RANKS, playcount):
                    with f.li:
                        f.a(unicode(artist.name), href=str(artist.url))
                        f['(%s)' % artist.playcount]
    return str(f)

def application(environ, start_response):
    """WSGI interface"""
    user_id = environ.get('user_id') or 'bbolli'
    ch = fetch_weekly_charts(user_id)
    if ch._name == 'weeklyartistchart' and prune_charts(ch):
        start_response('200 OK', [('Content-Type', 'application/atom+xml')])
        return [make_feed(ch)]
    else:
        start_response('404 Not found', [('Content-Type', 'text/xml')])
        environ['rc'] = 1
        return [ch.__repr__(1, 1).encode('utf-8') + '\n']

if __name__ == '__main__':
    """command-line interface"""
    from wsgi import WSGIWrapper
    environ = {'user_id': sys.argv[1] if len(sys.argv) == 2 else None, 'rc': 0}
    WSGIWrapper().run(application, environ)
