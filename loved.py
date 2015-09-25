#!/usr/bin/env python
# encoding: utf-8

"""Gets the loved tracks and reformats them into a new feed suitable for
tumble.py"""

from contextlib import nested
import datetime
import sys
import urllib

import basefetcher
import xmlbuilder
import xmltramp

ATOM_NS = 'http://www.w3.org/2005/Atom'
XHTML_NS = 'http://www.w3.org/1999/xhtml'

LASTFM_URL = 'https://ws.audioscrobbler.com/2.0/?'
LASTFM_KEY = '4605ebe7bfcaf0c1e9aa76f167da8efc'


class LovedTracks(basefetcher.UrlTimestampDataBase):

    def fetch(self, user):
        self.user = user
        self.loved = []
        params = {
            'method': 'user.getlovedtracks',
            'user': user,
            'api_key': LASTFM_KEY,
        }
        self.url = LASTFM_URL + urllib.urlencode(params)
        lfm = xmltramp.load(self.url)
        if lfm('status') == 'ok':
            self.open_key(self.url)
            for loved in lfm.lovedtracks['track':]:
                self.handle_if_newer(int(loved.date('uts')), loved)
            self.close_key()

    def handle_entry(self, entry):
        self.loved.append(entry)
        return True

    def write_feed(self):
        if not self.loved:
            return ''
        f = xmlbuilder.builder()
        with f.feed(xmlns=ATOM_NS):
            f.title(u"last.fm loved tracks")
            f.link(None, href=self.url)
            f.id('tag:drbeat.li,2013:lastfmloved:%s' % self.user)
            for entry in self.loved:
                with f.entry:
                    f.title('')
                    d = datetime.datetime.fromtimestamp(int(entry.date('uts')))
                    f.updated(d.isoformat())
                    f.id(str(entry.mbid))
                    f.link('')          # an empty link makes it a text post
                    for term in ('loved', 'music', 'last.fm'):
                        f.category(None, term=term)
                    with nested(f.content(type='xhtml'), f.div(xmlns=XHTML_NS), f.p):
                        f[u"Favorite track:"]
                        f.a(u"%s – %s" % (entry.artist.name, entry.name),
                            href=str(entry.url))
        return str(f)


def application(environ, start_response):
    """WSGI interface"""
    user_id = environ.get('user_id') or 'bbolli'
    lt = LovedTracks()
    #lt.force = True
    #lt.dry_run = True
    #lt.debug = 1
    try:
        lt.fetch(user_id)
        lt.close()
        start_response('200 OK', [('Content-Type', 'application/atom+xml')])
        return [lt.write_feed()]
    except IOError as e:
        start_response('500 Server error', [('Content-Type', 'text/plain')])
        environ['rc'] = 1
        return [repr(e).encode('utf-8')]


if __name__ == '__main__':
    """command-line interface"""
    from wsgi import WSGIWrapper
    environ = {
        'user_id': sys.argv[1] if len(sys.argv) == 2 else None,
        'rc': 0,
    }
    WSGIWrapper().run(application, environ)
