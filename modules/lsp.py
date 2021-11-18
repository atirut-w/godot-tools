from gi.repository import Ide
from gi.repository import Gio
from gi.repository import GObject

class GDScriptService(Ide.Object):
    _client = None
    _connected = False

    @GObject.property(type=Ide.LspClient)
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        self._client = value
        self.notify("client")

    @classmethod
    def from_context(klass, context):
        return context.ensure_child_typed(GDScriptService)

    def _ensure_connected(self):
        if not self._connected:
            socket = Gio.SocketClient.new()
            socket.family = Gio.SocketFamily.IPV4
            socket.type = Gio.SocketType.STREAM
            socket.protocol = Gio.SocketProtocol.TCP

            # TODO: Automatic reconnect
            connection = socket.connect_to_host("127.0.0.1:6008", 6008)
            self._client = Ide.LspClient.new(connection)
            self.append(self._client)
            self._client.add_language('gdscript')
            self._client.start()
            self.notify('client')

            self._connected = True

    @classmethod
    def bind_client(klass, provider):
        context = provider.get_context()
        self = GDScriptService.from_context(context)
        self._ensure_connected()
        self.bind_property('client', provider, 'client', GObject.BindingFlags.SYNC_CREATE)

# TODO: Fix unexpected "null" identifier when saving.
# Error: `1:1: error: Unexpected token: Identifier:Null#`
class GDScriptDiagnosticProvider(Ide.LspDiagnosticProvider, Ide.DiagnosticProvider):
    def do_load(self):
        GDScriptService.bind_client(self)

class GDScriptCompletionProvider(Ide.LspCompletionProvider, Ide.CompletionProvider):
    def do_load(self, context):
        GDScriptService.bind_client(self)

    def do_get_priority(self, context):
        # This provider only activates when it is very likely that we
        # want the results. So use high priority (negative is better).
        return -1000

class GDScriptSymbolResolver(Ide.LspSymbolResolver, Ide.SymbolResolver):
    def do_load(self):
        GDScriptService.bind_client(self)

class GDScriptHighlighter(Ide.LspHighlighter, Ide.Highlighter):
    def do_load(self):
        GDScriptService.bind_client(self)

class GDScriptFormatter(Ide.LspFormatter, Ide.Formatter):
    def do_load(self):
        GDScriptService.bind_client(self)

class GDScriptHoverProvider(Ide.LspHoverProvider, Ide.HoverProvider):
    def do_prepare(self):
        self.props.category = 'GDScript'
        self.props.priority = 200
        GDScriptService.bind_client(self)

class GDScriptRenameProvider(Ide.LspRenameProvider, Ide.RenameProvider):
    def do_load(self):
        GDScriptService.bind_client(self)

# class GDScriptCodeActionProvider(Ide.LspCodeActionProvider, Ide.CodeActionProvider):
#     def do_load(self):
#         GDScriptService.bind_client(self)

