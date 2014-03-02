class RPCNamespace(object):
    def __init__(self, method_map, prefix, rpc):
        full = lambda method: '.'.join((prefix, method))
        self.methods = {n: ProxiedRPC(rpc, full(method)) for n,method in \
                            method_map.iteritems()}
        self.prefix = prefix
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
    def __init__(self, rpc):
        super(Input, self).__init__(self.methods, "Input", rpc)


class GUI(RPCNamespace):
    methods = {
        "notify": "ShowNotification",
        "show_notification": "ShowNotification"
    }
    def __init__(self, rpc):
        super(GUI, self).__init__(self.methods, "GUI", rpc)
