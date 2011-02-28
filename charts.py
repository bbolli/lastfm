#!/usr/bin/env python
# encoding: utf-8

"""Gets the weekly play statistic from last.fm and generates
an Atom feed with the most played artists."""

# configuration
DOMAIN = 'drbeat.li'
PATH = '/lastfm.atom'
MAX = 3

import sys, datetime
import xmltramp, xmlbuilder

ATOM_NS = 'http://www.w3.org/2005/Atom'
XHTML_NS = 'http://www.w3.org/1999/xhtml'

def fetch_weekly_charts(user_id):
    url = 'http://ws.audioscrobbler.com/2.0/user/%s/weeklyartistchart.xml' % user_id
    try:
        parsed = xmltramp.load(url)
    except Exception, e:
        sys.stderr.write(repr(e) + '\n')
        sys.exit(1)
    if parsed._name == 'weeklyartistchart':
        return parsed

def make_feed(charts):
    f = xmlbuilder.builder()
    with f.feed(xmlns=ATOM_NS):
        who = str(charts('user'))
        when = datetime.datetime.utcfromtimestamp(int(charts('to')))
        when = when.isoformat() + 'Z'
        lastfm = 'http://www.last.fm/user/%s' % who
        f.title("%s’s weekly last.fm charts" % who)
        with f.author:
            f.name(who)
        f.link(None, href=lastfm)
        f.updated(when)
        f.id('tag:drbeat.li,2010:lastfmcharts:%s' % who)
        f.link(None, rel='self', href='http://%s%s' % (DOMAIN, PATH))
        with f.entry:
            f.title("Top artists for the week ending %s" % when[:10])
            f.updated(when)
            f.id('tag:%s,%s:%s:%s' % (DOMAIN, when[:10], PATH, who))
            f.link(None, rel='alternate', type='text/html', href=lastfm + '/charts?charttype=weekly')
            clast = None; i = 0
            with f.content(type='xhtml').div(xmlns=XHTML_NS).ol:
                for artist in charts['artist':]:
                    c = str(artist.playcount).strip()
                    if c != clast:
                        clast = c; i += 1
                        if i > MAX: break
                    with f.li:
                        f.a(str(artist.name), href=str(artist.url))
                        f['(%s)' % c]
    return str(f)

def application(environ, start_response):
    """WSGI interface"""
    user_id = environ.get('user_id') or 'bbolli'
    ch = fetch_weekly_charts(user_id)
    if ch:
        start_response('200 OK', [('Content-Type', 'application/atom+xml')])
        return [make_feed(ch)]
    else:
        start_response('404 Not found', [('Content-Type', 'text/plain')])
        return ['last.fm user "', user_id, '" not found\n']

if __name__ == '__main__':
    """command-line interface"""
    environ = {'user_id': sys.argv[1] if len(sys.argv) == 2 else None}
    status = ''
    def _start(_st, _hdr):
        global status
        status = _st
    for chunk in application(environ, _start):
        sys.stdout.write(chunk)
    if status[0] >= '4':
        sys.stderr.write(status + '\n')
        sys.exit(1)
