"""Read bounded public web pages and search results with urllib."""

from __future__ import annotations

import ipaddress
import os
import socket
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

MAX_BYTES = 1_000_000


def public_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        raise ValueError("网页地址须为 HTTP 或 HTTPS")
    if parsed.username or parsed.password or parsed.port not in {None, 80, 443}:
        raise ValueError("网页地址不能包含登录凭证或非网页端口")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
        raise PermissionError("联网工具只读取公网网站")
    return urllib.parse.urlunsplit(parsed._replace(fragment=""))


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, public_url(newurl))


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.title_parts, self.hidden = [], [], []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.hidden.append(tag)
        if tag == "title":
            self.in_title = True
        if tag in {"p", "br", "div", "li", "pre", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.hidden and tag == self.hidden[-1]:
            self.hidden.pop()
        if tag == "title":
            self.in_title = False
        if tag in {"p", "div", "li", "pre"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.hidden:
            return
        self.parts.append(data)
        if self.in_title:
            self.title_parts.append(data)


class WebReader:
    def __init__(self, opener=None):
        self.opener = opener or urllib.request.build_opener(PublicRedirect()).open

    def fetch(self, url: str) -> dict:
        url = public_url(url)
        request = urllib.request.Request(
            url, headers={"User-Agent": "UnderlineResearch/1.0", "Accept-Encoding": "identity"}
        )
        try:
            with self.opener(request, timeout=12) as response:
                final_url = public_url(response.geturl())
                media_type = response.headers.get_content_type()
                if not (media_type.startswith("text/") or media_type.endswith("+xml") or media_type in {"application/xml", "application/json"}):
                    raise ValueError("该地址不是可读取的文本网页")
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("网页超过 1 MB 读取上限")
                text = raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
        except OSError as exc:
            raise RuntimeError(f"网页获取失败：{type(exc).__name__}，未取得正文") from exc
        title = final_url
        if media_type == "text/html":
            parser = PageText()
            parser.feed(text)
            title = "".join(parser.title_parts).strip() or title
            text = "\n".join(line.rstrip() for line in "".join(parser.parts).splitlines() if line.strip())
        if not text.strip():
            raise ValueError("网页没有可读取的正文，可能需要 JavaScript 或登录")
        return {"url": final_url, "requested_url": url, "title": title[:300], "content": text[:60000],
                "truncated": len(text) > 60000}

    def search(self, query: str) -> list[dict]:
        query = query.strip()
        if not 1 <= len(query) <= 300:
            raise ValueError("搜索词须为 1–300 字")
        endpoint = os.environ.get("QQBOT_SEARCH_URL", "https://www.bing.com/search?format=rss&q=")
        page = self.fetch(endpoint + urllib.parse.quote(query))
        try:
            root = ET.fromstring(page["content"])
        except ET.ParseError as exc:
            raise RuntimeError("搜索服务未返回 RSS 结果，请检查 QQBOT_SEARCH_URL") from exc
        return [{"title": item.findtext("title") or "", "url": item.findtext("link") or "",
                 "summary": item.findtext("description") or "", "kind": "search_snippet"}
                for item in root.findall(".//item")[:5]]
