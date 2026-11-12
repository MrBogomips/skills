#!/usr/bin/env python3
"""Fetch a web page and print its readable text. The page reader for Gemini research workers.

Usage: read_page.py <url>

HTML is reduced to its visible text, one block per line. Other text types print as-is.
Only http and https URLs are accepted. Exits non-zero with a one-line message on bad URLs,
HTTP or network errors and non-text responses. The body read is capped at 2 MB.
"""

import html.parser
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_BYTES = 2 * 1024 * 1024
TIMEOUT_SECONDS = 30

SKIP_TAGS = {"script", "style", "noscript", "svg", "template", "head"}
BLOCK_TAGS = {
    "p", "div", "section", "article", "main", "li", "ul", "ol", "tr", "table", "br",
    "h1", "h2", "h3", "h4", "h5", "h6", "pre", "blockquote", "header", "footer", "nav", "dt", "dd",
}


class TextExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TAGS:
            self.skip_depth += 1
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)

    def text(self):
        lines = (" ".join(line.split()) for line in "".join(self.parts).splitlines())
        return "\n".join(line for line in lines if line)


def html_to_text(body):
    extractor = TextExtractor()
    extractor.feed(body)
    return extractor.text()


def check_url(url):
    """Return the URL if it is http(s) with a host, else exit with a one-line message."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        sys.exit(f"read_page: only http and https URLs are supported: {url}")
    return url


def ssl_context():
    """Default verification; some Python builds on macOS ship without CA certificates."""
    context = ssl.create_default_context()
    system_bundle = "/etc/ssl/cert.pem"
    if not context.cert_store_stats().get("x509_ca") and os.path.isfile(system_bundle):
        context = ssl.create_default_context(cafile=system_bundle)
    return context


def fetch(url):
    """Return (final url, content type, body text). Exit with a one-line message on failure."""
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research reader)"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS, context=ssl_context()) as response:
            content_type = response.headers.get_content_type()
            raw = response.read(MAX_BYTES)
            charset = response.headers.get_content_charset() or "utf-8"
            final_url = response.geturl()
    except urllib.error.HTTPError as exc:
        sys.exit(f"read_page: HTTP {exc.code} {exc.reason} for {url}")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        sys.exit(f"read_page: cannot fetch {url}: {getattr(exc, 'reason', exc)}")
    return final_url, content_type, raw.decode(charset, errors="replace")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: read_page.py <url>")
    final_url, content_type, body = fetch(check_url(sys.argv[1]))
    if not (content_type.startswith("text/") or content_type in {"application/json", "application/xml"}):
        sys.exit(f"read_page: {final_url} is {content_type}, not a text page")
    print(f"URL: {final_url}\n")
    print(html_to_text(body) if content_type == "text/html" else body)


if __name__ == "__main__":
    main()
