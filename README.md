lastfm
======

* `charts.py` gets the weekly charts from last.fm and outputs an ATOM
  feed of the most played artists.
* `lastfm` is a shell script that keeps track of the charts already
  posted to Tumblr and posts only new charts or edits old ones.
* `loved.py` gets the newly loved tracks as an ATOM feed. Its output is
  compatible with [`tumble`][tu].

The posts are back-dated to the date and time the chart was generated or
the track was loved.

Installation
------------

1. Download and unzip the [archive][zip] or clone the [repo][git]
2. Create symlinks in your `~/bin` (you have a personal `bin` folder,
   right? Right?) to `charts.py` and `loved.py`, dropping the `.py`
   extension, like this:

        cd ~/bin
        ln -s <src-dir>/charts.py charts
        ln -s <src-dir>/loved.py loved

3. Create a daily cron job with the command `lastfm; loved | tumble`

Dependencies
------------

* `charts.py`: [`xmltramp`][tramp], [`xmlbuilder`][build]
* `lastfm`: [`tumblr-utils`][tu]
* `loved.py`: [`rss-fetcher`][f], [`xmlbuilder`][build]
  * `rss-fetcher`: [feedparser][parser]

License
-------

[GPL2][gpl2] or later.

[tu]: https://github.com/bbolli/tumblr-utils
[f]: https://github.com/bbolli/rss-fetcher/raw/master/basefetcher.py
[rss]: https://github.com/bbolli/rss-fetcher
[zip]: https://github.com/bbolli/lastfm/archive/master.zip
[git]: https://github.com/bbolli/lastfm.git
[tramp]: https://github.com/bbolli/xmltramp
[build]: https://github.com/bbolli/xmlwitch
[parser]: http://code.google.com/p/feedparser/
[gpl2]: http://www.gnu.org/licenses/gpl-2.0.txt

<!-- vim: set tw=72 : -->
