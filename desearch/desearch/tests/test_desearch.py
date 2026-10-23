"""Offline tests: the HTTP session is a stub, no network and no real key."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.desearch_client import DesearchClient, DesearchError, collect_links, parse_sources  # noqa: E402


class _Resp:
    def __init__(self, status=200, body=None, text=""):
        self.status_code = status
        self._body = body
        self.text = text

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


class _Session:
    def __init__(self, resp):
        self.resp = resp
        self.calls = []

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        return self.resp


def test_missing_key():
    with pytest.raises(DesearchError, match="console.desearch.ai/api-keys"):
        DesearchClient("  ")


def test_web_search_sends_raw_key_without_bearer():
    s = _Session(_Resp(body={"data": []}))
    DesearchClient("test-key", session=s).web_search("q", start=10)
    method, url, kw = s.calls[0]
    assert (method, url) == ("GET", "https://api.desearch.ai/web")
    assert kw["headers"]["Authorization"] == "test-key"
    assert kw["params"] == {"query": "q", "start": 10}
    assert kw["timeout"]


def test_ai_search_body():
    s = _Session(_Resp(body={"completion": "a"}))
    DesearchClient("k", session=s).ai_search("p", ["web", "reddit"], "PAST_WEEK")
    method, url, kw = s.calls[0]
    assert (method, url) == ("POST", "https://api.desearch.ai/desearch/ai/search")
    assert kw["json"] == {"prompt": "p", "tools": ["web", "reddit"], "streaming": False, "date_filter": "PAST_WEEK"}


def test_x_search_drops_empty_filters():
    s = _Session(_Resp(body=[]))
    DesearchClient("k", session=s).x_search("q", count=5, sort="Latest", user=None, lang="en", start_date="")
    assert s.calls[0][2]["params"] == {"query": "q", "count": 5, "sort": "Latest", "lang": "en"}


@pytest.mark.parametrize("status,match", [(401, "rejected"), (403, "rejected"), (429, "rate limit"), (500, "HTTP 500")])
def test_http_errors(status, match):
    s = _Session(_Resp(status=status, text="secret-key echoed"))
    with pytest.raises(DesearchError, match=match) as e:
        DesearchClient("secret-key", session=s).web_search("q")
    assert "secret-key" not in str(e.value)


def test_parse_sources():
    assert parse_sources("") == ["web", "twitter"]
    assert parse_sources("Reddit, x, reddit") == ["reddit", "twitter"]
    with pytest.raises(DesearchError, match="Unknown source"):
        parse_sources("youtube")


def test_collect_links_dedupes_across_lists():
    body = {"search": [{"title": "A", "link": "https://a"}], "reddit_search": [{"title": "A2", "link": "https://a"}, {"url": "https://b"}], "completion": "x"}
    assert collect_links(body) == [{"title": "A", "link": "https://a"}, {"title": "", "link": "https://b"}]


@pytest.mark.parametrize("status,ok", [(422, True), (403, False), (401, False), (200, False), (500, False)])
def test_check_key_is_free_route(status, ok):
    s = _Session(_Resp(status=status, body={}))
    client = DesearchClient("k", session=s)
    if ok:
        client.check_key()
    else:
        with pytest.raises(DesearchError):
            client.check_key()
    method, url, kw = s.calls[0]
    assert (method, url) == ("GET", "https://api.desearch.ai/web")
    assert "params" not in kw or not kw.get("params")
    assert kw["headers"]["Authorization"] == "k"
