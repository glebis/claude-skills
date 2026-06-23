import urllib.request

from dtokens import serve


def test_url_for_builds_http_path(tmp_path):
    (tmp_path / "sub").mkdir()
    f = tmp_path / "sub" / "x.html"
    f.write_text("hi")
    assert serve.url_for(tmp_path, f, 9999, "127.0.0.1") == "http://127.0.0.1:9999/sub/x.html"
    assert serve.url_for(tmp_path, None, 9999) == "http://127.0.0.1:9999"


def test_find_free_port_returns_bindable(tmp_path):
    port = serve.find_free_port(19000)
    assert 19000 <= port < 19500


def test_serve_non_blocking_responds(tmp_path):
    (tmp_path / "i.html").write_text("<h1>served ok</h1>")
    port = serve.find_free_port(19500)
    httpd, url = serve.serve(tmp_path, tmp_path / "i.html", port=port,
                             open_browser=False, _block=False)
    try:
        body = urllib.request.urlopen(url, timeout=3).read().decode()
        assert "served ok" in body
    finally:
        httpd.shutdown()
        httpd.server_close()
