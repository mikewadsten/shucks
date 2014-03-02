class RPCNamespace(object):
    def __init__(self, method_map, rpc):
        full = lambda method: '.'.join((self.prefix, method))
        self.methods = {n: ProxiedRPC(rpc, full(method)) for n,method in \
                            method_map.iteritems()}
        self.rpc = rpc

    def __getattr__(self, name):
        if name not in self.methods:
            raise AttributeError("Method not defined: " + name)
        return self.methods[name]


class ProxiedRPC(object):
    def __init__(self, rpc, method):
        self.rpc = rpc
        self.method = method

    def __str__(self):
        return "<RPC method '%s' (at 0x%s)>" % (self.method, hex(id(self)))

    def __repr__(self):
        return self.__str__()

    def __call__(self, **kwargs):
        return self.rpc.call(self.method, [], kwargs)


class Input(RPCNamespace):
    methods = {
        "back": "Back", "menu": "ContextMenu", "down": "Down",
        "execute_action": "ExecuteAction", "do": "ExecuteAction",
        "exec": "ExecuteAction", "home": "Home", "info": "Info",
        "left": "Left", "right": "Right", "select": "Select",
        "enter": "Select", "send_text": "SendText", "text": "SendText",
        "codec": "ShowCodec", "show_codec": "ShowCodec",
        "osd": "ShowOSD", "show_osd": "ShowOSD", "up": "Up"
    }
    prefix = "Input"

    def __init__(self, rpc):
        super(Input, self).__init__(self.methods, rpc)


class GUI(RPCNamespace):
    methods = {
        "notify": "ShowNotification",
        "show_notification": "ShowNotification"
    }
    prefix = "GUI"

    def __init__(self, rpc):
        super(GUI, self).__init__(self.methods, rpc)


class JSONRPC(RPCNamespace):
    methods = {"ping": "Ping", "version": "Version"}
    prefix = "JSONRPC"

    def __init__(self, rpc):
        super(JSONRPC, self).__init__(self.methods, rpc)


class VideoLibrary(RPCNamespace):
    methods = {
        "clean": "Clean", "get_episode_details": "GetEpisodeDetails",
        "episodes": "GetEpisodes", "get_episodes": "GetEpisodes",
        "genres": "GetGenres", "get_genres": "GetGenres",
        "get_movie_details": "GetMovieDetails",
        "get_movie_set_details": "GetMovieSetDetails",
        "get_movie_sets": "GetMovieSets", "get_movies": "GetMovies",
        "get_recently_added_movies": "GetRecentlyAddedMovies",
        "get_seasons": "GetSeasons", "get_tv_show_details": "GetTVShowDetails",
        "get_tv_shows": "GetTVShows", "remove_episode": "RemoveEpisode",
        "remove_movie": "RemoveMovie", "scan": "Scan"
    }
    prefix = "VideoLibrary"

    def __init__(self, rpc):
        super(VideoLibrary, self).__init__(self.methods, rpc)
