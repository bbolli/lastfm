#!/usr/bin/env python
# encoding: utf-8

"""Gets the RSS feed of the loved tracks and reformats them into
a new feed that is tumblable."""

import sys, datetime
import xmlbuilder
from basefetcher import BaseRSSFetcher

ATOM_NS = 'http://www.w3.org/2005/Atom'
XHTML_NS = 'http://www.w3.org/1999/xhtml'

class LovedTracks(BaseRSSFetcher):

    def fetch(self, user):
        self.user = user
        self.loved = []
        url = 'http://ws.audioscrobbler.com/2.0/user/%s/lovedtracks.rss' % user
        BaseRSSFetcher.fetch(self, url)

    def handle_entry(self, entry):
        self.loved.append(entry)
        return True

    def write_feed(self):
        if not self.loved:
            return ''
        f = xmlbuilder.builder()
        with f.feed(xmlns=ATOM_NS):
            f.title(self.parsed_feed.feed.title)
            f.link(None, href=self.parsed_feed.feed.link)
            f.updated(self.parsed_feed.feed.updated)
            f.id('tag:drbeat.li,2013:lastfmloved:%s' % self.user)
            for entry in self.loved:
                with f.entry:
                    f.title('')
                    f.updated(entry.updated)
                    f.id(entry.id)
                    f.link('')          # an empty link makes it a text post
                    f.category(None, term='loved')
                    f.category(None, term='music')
                    f.category(None, term='last.fm')
                    with f.content(type='xhtml').div(xmlns=XHTML_NS).p:
                        f[u"Favorite track:"]
                        f.a(entry.title, href=entry.link)
        return str(f)


def application(environ, start_response):
    """WSGI interface"""
    user_id = environ.get('user_id') or 'bbolli'
    lt = LovedTracks()
    lt.debug = -1       # suppress the log on stdout
    #lt.force = True
    #lt.dry_run = True
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

    class WSGIWrapper:
        def start_response(self, status, header):
            self.status = status
        def run(self, app, env, out=sys.stdout):
            self.status = ''
            for chunk in app(env, self.start_response):
                out.write(chunk)
            return self.status

    environ = {
        'user_id': sys.argv[1] if len(sys.argv) == 2 else None,
        'rc': 0,
    }
    WSGIWrapper().run(application, environ)
    sys.exit(environ['rc'])
