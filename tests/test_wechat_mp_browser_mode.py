import importlib


def load_resolver(monkeypatch):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    module = importlib.import_module("crawlers.wechat_mp")
    return module.resolve_wechat_mp_headless


def test_auto_mode_is_visible_without_storage(tmp_path, monkeypatch):
    resolve_wechat_mp_headless = load_resolver(monkeypatch)

    assert resolve_wechat_mp_headless("auto", tmp_path / "missing.json") is False


def test_auto_mode_is_headless_with_storage(tmp_path, monkeypatch):
    resolve_wechat_mp_headless = load_resolver(monkeypatch)
    state = tmp_path / "state.json"
    state.write_text("{}", encoding="utf-8")

    assert resolve_wechat_mp_headless("auto", state) is True


def test_visible_and_headless_modes_are_explicit(tmp_path, monkeypatch):
    resolve_wechat_mp_headless = load_resolver(monkeypatch)
    state = tmp_path / "state.json"

    assert resolve_wechat_mp_headless("visible", state) is False
    assert resolve_wechat_mp_headless("headless", state) is True
