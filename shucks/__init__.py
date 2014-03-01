"""A silly command line XBMC client.

Usage:
    shucks [--host=HOST] [--port=PORT]

Options:
    -H --host=HOST      Address of the XBMC server to connect with.
    -P --port=PORT      Web server port on server [default: 8080].
    --version           Show version.
    -h --help           Show this screen.
"""
VERSION = "0.0.1"

import cmd
from docopt import docopt
import json
import os
from pprint import pprint
import sys
import textwrap

from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc import RPCClient


def success(message):
    check = u"\u2713"
    green = u"\033[0;32m%s\033[0m"
    print green % (" ".join((check, message)))


def fail(message):
    x = u"\u2717"
    red = u"\033[0;31m%s\033[0m"
    print red % (" ".join((x, message)))


_width = int(os.popen("stty size", "r").read().split()[1])
TAG_WRAP = textwrap.TextWrapper(width=_width, initial_indent="    ",
                                subsequent_indent="    ")
PLOT_WRAP = textwrap.TextWrapper(width=_width, initial_indent="      ",
                                 subsequent_indent="      ")


def movie_to_string(obj):
    def num_to_str(num):
        # Convert a number to a time string
        from datetime import timedelta
        duration = timedelta(seconds=float(num))

        days, seconds = duration.days, duration.seconds
        hours = days*24 + seconds/3600
        minutes = (seconds % 3600) / 60
        seconds = seconds % 60

        return "%dh %dm" % (hours, minutes) + \
                (" %ds" % seconds if seconds else "")

    r = "\033[1;37m"
    r += obj.get('title', ">> NO TITLE <<")
    r += (" (%d)" % obj['year'] if 'year' in obj else '')
    r += u"\033[0;32m \u22ef ID: %d" % obj['movieid']
    r += "\033[0m\n"

    r += "    \033[1mLength:\033[0m %s\n" % num_to_str(obj['runtime'])

    if obj['tagline']:
        tagline = TAG_WRAP.fill(obj['tagline'])
        r += "\033[1;33m" + tagline + "\033[0m\n"

    if obj['plot']:
        r += PLOT_WRAP.fill(obj['plot']) + "\n"

    pos = float(obj.get('resume', {}).get('position', 0))
    if pos:
        position = num_to_str(pos)
        r += "    \033[0;35m> Playback position: %s\033[0m\n" % str(position)

    return r


class ShucksShell(cmd.Cmd):
    def __init__(self, args):
        cmd.Cmd.__init__(self)

        self.prompt = "\n\033[1;33m# \033[0m"

        self.args = args

        uri = ''.join(["http://", args['--host'], ":", args['--port'],
                       "/jsonrpc"])

        rpc_client = RPCClient(
            JSONRPCProtocol(),
            HttpPostClientTransport(uri))

        self.xbmc = rpc_client

        # Will throw exception if it doesn't work
        #self.xbmc.call("JSONRPC.Ping", [], {})

    def do_ping(self, arg=""):
        """Ping the server to see if the connection works."""
        try:
            self.xbmc.call("JSONRPC.Ping", [], {})
            success("Ping successful.")
        except Exception, e:
            fail(str(e))

    def do_movies(self, arg):
        """Alias for `list movies`"""
        return self.do_list("movies")

    def do_list(self, what):
        """`list movies`: Get a list of movies in the library."""
        if not what:
            fail("Need to say 'list movies' or 'list <whatever>'")
            return

        try:
            if what == "movies":
                props = ["title", "year", "tagline", "resume", "runtime",
                         "plot"]
                response = self.xbmc.call("VideoLibrary.GetMovies",
                        [], {"properties": props, "sort": {"method": "title"}})
                movies = response['movies']
                for movie in movies:
                    print movie_to_string(movie).rstrip() + "\n"
            else:
                fail("I only understand movies right now...")
                return False
        except Exception, e:
            fail(str(e))

    def do_info(self, arg):
        """`info movie <id>`: get movie details"""
        if not arg:
            fail("info on what? 'info movie #', etc.")
            return False

        args = arg.split()
        if args[0] != "movie":
            fail("I can only handle movie info at the moment")
            return False

        try:
            mid = int(args[1])
        except ValueError:
            fail("Usage: list movie <id>")
            return False

        try:
            #props = ["title", "year", "tagline", "plot", "genre", "runtime",
                     #"plot"]
            props = ["title", "year", "runtime", "tagline", "plot"]
            info = self.xbmc.call("VideoLibrary.GetMovieDetails", [],
                                  {"movieid": mid, "properties": props})
            print movie_to_string(info['moviedetails']).rstrip() + "\n\n"
        except Exception, e:
            print repr(e)
            fail(str(e))

    def do_players(self, arg):
        try:
            print self.xbmc.call("Player.GetActivePlayers", [], {})
        except Exception, e:
            fail(repr(e))

    def do_call(self, arg):
        args = arg.split()

        if not len(args):
            fail("Usage: call <method> [args] [kwargs]")
            return
        elif len(args) == 1:
            args = args + [ "[]", "{}" ]
        elif len(args) == 2:
            args = args + [ "{}" ]
        elif len(args) > 3:
            fail("Usage: call <method> [args] [kwargs]")
            return

        try:
            args[1] = json.loads(args[1])
            if not isinstance(args[1], list):
                raise Exception
        except Exception:
            fail("'args' is not a valid JSON list")
            return

        try:
            args[2] = json.loads(args[2])
            if not isinstance(args[2], dict):
                raise Exception
        except Exception:
            fail("'kwargs' is not a valid JSON dict")
            return

        try:
            print u"\033[36m\u21B3 Trying method \"%s\"...\033[0m" % args[0]

            method, args, kwargs = args
            print json.dumps(self.xbmc.call(method, args, kwargs), indent=2)
        except Exception, e:
            fail(repr(e))

    def do_EOF(self, arg=""):
        print "\nAww, shucks! Leaving so soon?"
        return True

    def do_quit(self, arg):
        return self.do_EOF()

    def do_exit(self, arg):
        return self.do_EOF()

    def emptyline(self):
        pass


def begin():
    arguments = docopt(__doc__, version="Shucks v" + VERSION)
    if not arguments['--host']:
        if 'SHUCKS' not in os.environ:
            print "No host given, and no environment variable named SHUCKS."
            sys.exit(1)
        else:
            config = json.load(open(os.environ['SHUCKS'], "r"))
            arguments['--host'] = config['host']

    ShucksShell(arguments).cmdloop()
