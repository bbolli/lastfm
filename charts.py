#!/usr/bin/env python
# encoding: utf-8

"""Gets the weekly play statistic from last.fm and generates
an Atom feed with the most played artists."""

# configuration
DOMAIN = 'drbeat.li'
PATH = '/lastfm.atom'
RANKS = 3

import sys, datetime
from itertools import groupby, islice

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
            f.category(None, term='charts')
            f.category(None, term='music')
            with f.content(type='xhtml').div(xmlns=XHTML_NS).ol:
                for artist in first_n_ranks(charts['artist':], RANKS, lambda a: str(a.playcount)):
                    with f.li:
                        f.a(unicode(artist.name), href=str(artist.url))
                        f['(%s)' % artist.playcount]
    return str(f)

def application(environ, start_response):
    """WSGI interface"""
    user_id = environ.get('user_id') or 'bbolli'
    ch = fetch_weekly_charts(user_id)
    if ch._name == 'weeklyartistchart':
        start_response('200 OK', [('Content-Type', 'application/atom+xml')])
        return [make_feed(ch)]
    else:
        start_response('404 Not found', [('Content-Type', 'text/xml')])
        return [ch.__repr__(1, 1)]

if __name__ == '__main__':
    """command-line interface"""

    class WSGIWrapper:
        def start_response(self, status, header):
            self.status = status
        def run(self, app, env, out=sys.stdout):
            self.status = ''
            for chunk in app(env, self.start_response):
                out.write(chunk)
            return self.status

    environ = {'user_id': sys.argv[1] if len(sys.argv) == 2 else None}
    WSGIWrapper().run(application, environ)
