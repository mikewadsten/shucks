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

import cmd2
from docopt import docopt
import json
import os
from pprint import pprint
import sys
import textwrap

from tinyrpc.protocols.jsonrpc import JSONRPCProtocol
from tinyrpc.transports.http import HttpPostClientTransport
from tinyrpc import RPCClient

from shucks.proxies import Input, GUI


def success(message):
    check = u"\u2713".encode('utf-8')
    green = u"\033[0;32m%s\033[0m".encode('utf-8')
    print green % (" ".join((check, message)))


def fail(message):
    x = u"\u2717".encode('utf-8')
    red = u"\033[0;31m%s\033[0m".encode('utf-8')
    print red % (" ".join((x, message)))


# Decorator to wrap a function in try/catch
def failexc(func):
    from functools import wraps
    @wraps(func)
    def handles_exception(self, *args):
        try:
            return func(self, *args)
        except Exception, e:
            fail(str(e))

    return handles_exception


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


class ShucksShell(cmd2.Cmd):
    def __init__(self, args):
        cmd2.Cmd.__init__(self)

        self.prompt = "\n\033[1;33m# \033[0m"

        self.args = args

        uri = ''.join(["http://", args['--host'], ":", args['--port'],
                       "/jsonrpc"])

        rpc_client = RPCClient(
            JSONRPCProtocol(),
            HttpPostClientTransport(uri))

        self.xbmc = rpc_client

        self.input = Input(self.xbmc)
        self.gui = GUI(self.xbmc)

        # Will throw exception if it doesn't work
        #self.xbmc.call("JSONRPC.Ping", [], {})

    @failexc
    def do_ping(self, arg=""):
        """Ping the server to see if the connection works."""
        self.xbmc.call("JSONRPC.Ping", [], {})
        success("Ping successful.")

    @failexc
    def do_clear(self, arg=""):
        os.system('clear')

    @failexc
    def do_notify(self, arg=""):
        import shlex
        args = shlex.split(arg)
        if len(args) != 2:
            fail("Expected two strings: title and message")
            return

        self.gui.notify(title=args[0], message=args[1])
        success("")

    @failexc
    def do_movies(self, arg):
        """Alias for `list movies`"""
        import subprocess
        # This will page the output if it's greater than one screen. Also will
        # allow colors, and search ignores case.
        less = subprocess.Popen(["less", "-iRX"], stdin=subprocess.PIPE)
        rv = self.do_ls("movies", output=less.stdin)
        less.communicate()
        less.stdin.close()
        self.do_clear()
        return rv

    # output is the output stream to write to. We want the 'movies' command to
    # have its output piped to less, so this is necessary.
    @failexc
    def do_ls(self, what, output=sys.stdout):
        """`ls movies`: Get a list of movies in the library."""
        if not what:
            fail("Need to say 'ls movies' or 'ls <whatever>'")
            return

        if what == "movies":
            props = ["title", "year", "tagline", "resume", "runtime",
                        "plot"]
            response = self.xbmc.call("VideoLibrary.GetMovies",
                    [], {"properties": props, "sort": {"method": "title"}})
            movies = response['movies']
            for movie in movies:
                s = movie_to_string(movie).rstrip() + "\n"
                output.write(s.encode('utf-8'))
                output.write("\n")
        else:
            fail("I only understand movies right now...")
            return False

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

        #props = ["title", "year", "tagline", "plot", "genre", "runtime",
                    #"plot"]
        props = ["title", "year", "runtime", "tagline", "plot", "resume"]
        info = self.xbmc.call("VideoLibrary.GetMovieDetails", [],
                                {"movieid": mid, "properties": props})
        print (movie_to_string(info['moviedetails']).rstrip() +
                "\n\n").encode('utf-8')

    @failexc
    def do_players(self, arg):
        print self.xbmc.call("Player.GetActivePlayers", [], {})

    @failexc
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

        print (u"\033[36m\u21B3 Trying method \"%s\"...\033[0m" %
                args[0]).encode('utf-8')

        method, args, kwargs = args
        return_value = self.xbmc.call(method, args, kwargs)
        print json.dumps(return_value, indent=2)

    @failexc
    def do_left(self, arg):
        result = self.input.left()
        success("") if (result == "OK") else fail(result)

    @failexc
    def do_right(self, arg):
        result = self.input.right()
        success("") if (result == "OK") else fail(result)

    @failexc
    def do_down(self, arg):
        result = self.input.down()
        success("") if (result == "OK") else fail(result)

    @failexc
    def do_up(self, arg):
        result = self.input.up()
        success("") if (result == "OK") else fail(result)

    @failexc
    def do_s(self, arg):
        result = self.input.select()
        success("") if (result == "OK") else fail(result)

    @failexc
    def do_c(self, arg):
        result = self.input.menu()
        success("") if (result == "OK") else fail(result)
    do_menu = do_c

    @failexc
    def do_b(self, arg):
        result = self.input.back()
        success("") if (result == "OK") else fail(result)
    do_back = do_b

    def do_EOF(self, arg=""):
        print "\nAww, shucks! Leaving so soon?"
        return True
    do_exit = do_EOF
    do_quit = do_EOF
    do_q = do_EOF

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
