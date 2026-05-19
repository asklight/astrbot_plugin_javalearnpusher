import runpy
import sys
import types
from pathlib import Path


def test_main_imports_local_package_when_loaded_without_plugin_dir_on_sys_path(monkeypatch):
    plugin_dir = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(
        sys,
        "path",
        [path for path in sys.path if Path(path or ".").resolve() != plugin_dir],
    )

    assert str(plugin_dir) not in sys.path

    astrbot = types.ModuleType("astrbot")
    api = types.ModuleType("astrbot.api")
    event = types.ModuleType("astrbot.api.event")
    message_components = types.ModuleType("astrbot.api.message_components")
    star = types.ModuleType("astrbot.api.star")
    core = types.ModuleType("astrbot.core")
    utils = types.ModuleType("astrbot.core.utils")
    astrbot_path = types.ModuleType("astrbot.core.utils.astrbot_path")

    class _Logger:
        def info(self, _message):
            pass

        def error(self, _message):
            pass

    class _Star:
        def __init__(self, context, config=None):
            self.context = context

    class _MessageChain:
        def __init__(self, chain=None):
            self.chain = chain or []

    class _Plain:
        def __init__(self, text):
            self.text = text

    class _Filter:
        @staticmethod
        def command(_name):
            return lambda func: func

    def _register(*_args, **_kwargs):
        return lambda cls: cls

    api.AstrBotConfig = dict
    api.logger = _Logger()
    event.AstrMessageEvent = object
    event.MessageChain = _MessageChain
    event.filter = _Filter()
    message_components.Plain = _Plain
    star.Context = object
    star.Star = _Star
    star.register = _register
    astrbot_path.get_astrbot_plugin_data_path = lambda: str(plugin_dir / "data")

    monkeypatch.setitem(sys.modules, "astrbot", astrbot)
    monkeypatch.setitem(sys.modules, "astrbot.api", api)
    monkeypatch.setitem(sys.modules, "astrbot.api.event", event)
    monkeypatch.setitem(sys.modules, "astrbot.api.message_components", message_components)
    monkeypatch.setitem(sys.modules, "astrbot.api.star", star)
    monkeypatch.setitem(sys.modules, "astrbot.core", core)
    monkeypatch.setitem(sys.modules, "astrbot.core.utils", utils)
    monkeypatch.setitem(sys.modules, "astrbot.core.utils.astrbot_path", astrbot_path)

    runpy.run_path(str(plugin_dir / "main.py"), run_name="xlin_import_test")
