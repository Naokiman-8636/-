#!/usr/bin/env python3
"""スポーツニュース（特に相撲）を RSS/Atom から集めて HTML 一覧を作る。

使い方:
    python3 sports_news/fetch_news.py --out site

標準ライブラリのみで動作する。設定は同じフォルダの config.json。
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

JST = timezone(timedelta(hours=9))
HERE = Path(__file__).resolve().parent
UA = "Mozilla/5.0 (compatible; sports-news-digest/1.0)"
ATOM = "{http://www.w3.org/2005/Atom}"
DC = "{http://purl.org/dc/elements/1.1/}"


@dataclass
class Item:
    title: str
    link: str
    source: str
    published: str  # ISO8601 (JST)
    section: str  # "sumo" | "other"


def fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_date(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    try:
        d = parsedate_to_datetime(text)  # RFC 822 (RSS)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(text.replace("Z", "+00:00"))  # ISO (Atom)
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=JST)
    return d.astimezone(JST)


def parse_feed(data: bytes, feed_name: str) -> list[tuple[str, str, str, datetime | None]]:
    """(title, link, source, published) のリストを返す。RSS 2.0 / RSS 1.0 / Atom 対応。"""
    root = ET.fromstring(data)
    out = []
    # RSS 2.0 / RSS 1.0 (RDF)
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag != "item":
            continue
        g = lambda name: next((c.text for c in it if c.tag.split("}")[-1] == name), None)
        title = (g("title") or "").strip()
        link = (g("link") or "").strip()
        src_el = next((c for c in it if c.tag.split("}")[-1] == "source"), None)
        source = (src_el.text.strip() if src_el is not None and src_el.text else feed_name)
        pub = parse_date(g("pubDate") or g("date"))
        out.append((title, link, source, pub))
    # Atom
    for e in root.iter(f"{ATOM}entry"):
        title = (e.findtext(f"{ATOM}title") or "").strip()
        link_el = e.find(f"{ATOM}link[@rel='alternate']")
        if link_el is None:
            link_el = e.find(f"{ATOM}link")
        link = link_el.get("href", "") if link_el is not None else ""
        pub = parse_date(e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated"))
        out.append((title, link, feed_name, pub))
    return out


def clean_title(title: str, source: str) -> str:
    # Google ニュースはタイトル末尾に " - 媒体名" が付くので取り除く
    suffix = f" - {source}"
    if title.endswith(suffix):
        title = title[: -len(suffix)]
    return html.unescape(title).strip()


def norm_key(title: str) -> str:
    return re.sub(r"[\s　「」『』【】（）()・、。！!？?\"'”“]", "", title)[:40]


def is_sumo(title: str, keywords: list[str]) -> bool:
    return any(k in title for k in keywords)


def collect(cfg: dict, now: datetime) -> tuple[list[Item], list[str]]:
    cutoff = now - timedelta(hours=cfg.get("hours", 36))
    kw = cfg["sumo_keywords"]
    items: list[Item] = []
    seen: set[str] = set()
    errors: list[str] = []
    for feed in cfg["feeds"]:
        try:
            entries = parse_feed(fetch(feed["url"]), feed["name"])
        except Exception as e:  # 1つのフィードが落ちても全体は止めない
            errors.append(f"{feed['name']}: {e}")
            print(f"[warn] {feed['name']}: {e}", file=sys.stderr)
            continue
        for title, link, source, pub in entries:
            title = clean_title(title, source)
            if not title or not link:
                continue
            if pub is not None and pub < cutoff:
                continue
            key = norm_key(title)
            if key in seen:
                continue
            seen.add(key)
            section = "sumo" if (feed["section"] == "sumo" or is_sumo(title, kw)) else "other"
            items.append(Item(title, link, source, (pub or now).isoformat(), section))
        print(f"[ok] {feed['name']}: {len(entries)} entries", file=sys.stderr)
    items.sort(key=lambda i: i.published, reverse=True)
    return items, errors


CSS = """
:root{--bg:#faf8f3;--card:#fff;--fg:#111;--muted:#555;--line:#ddd6c8;--accent:#b3261e;--chip:#efe8da;--fs:20px}
@media (prefers-color-scheme:dark){:root{--bg:#121214;--card:#1d1d21;--fg:#f4f4f6;--muted:#b4b4bc;--line:#34343c;--accent:#ff8a80;--chip:#2a2a31}}
html.big{--fs:24px} html.huge{--fs:28px}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:var(--fs)/1.65 -apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif;-webkit-text-size-adjust:100%}
main{max-width:760px;margin:0 auto;padding:20px 16px 64px}
header h1{font-size:1.35em;margin:0;line-height:1.3}
header p{margin:4px 0 0;color:var(--muted);font-size:.85em}
.size{display:flex;align-items:center;gap:8px;margin:14px 0 0;font-size:16px;color:var(--muted);white-space:nowrap}
.size button{font:inherit;font-size:18px;font-weight:700;color:var(--fg);background:var(--chip);border:2px solid transparent;border-radius:10px;min-width:64px;min-height:48px;padding:0 12px;cursor:pointer}
.size button[aria-pressed=true]{border-color:var(--accent);color:var(--accent)}
nav{display:flex;gap:10px;margin:14px 0 0}
nav a{flex:1;text-align:center;padding:10px 8px;border-radius:12px;background:var(--chip);color:var(--fg);text-decoration:none;font-weight:700;font-size:18px;white-space:nowrap}
section{margin-top:28px}
h2{font-size:1.15em;border-left:6px solid var(--accent);padding-left:10px;margin:0 0 10px}
h2 small{color:var(--muted);font-weight:normal;font-size:.75em}
ul{list-style:none;margin:0;padding:0;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden}
li{border-top:1px solid var(--line)}
li:first-child{border-top:0}
li a{display:block;padding:16px;color:var(--fg);text-decoration:none;font-weight:700}
li a:active{background:var(--chip)}
.meta{display:block;color:var(--muted);font-size:.75em;font-weight:normal;margin-top:4px}
.new{display:inline-block;background:var(--accent);color:var(--card);font-size:.7em;border-radius:6px;padding:0 6px;margin-right:6px;vertical-align:.15em}
.empty{padding:16px;color:var(--muted)}
.top{display:block;text-align:center;margin:24px 0 0;padding:14px;border-radius:12px;background:var(--chip);color:var(--fg);text-decoration:none;font-weight:700}
footer{margin-top:28px;color:var(--muted);font-size:.7em}
"""

SIZE_JS = """
(function(){var r=document.documentElement,k='fontsize';
function set(v){r.classList.remove('big','huge');if(v!=='normal')r.classList.add(v);
document.querySelectorAll('.size button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.v===v)});
try{localStorage.setItem(k,v)}catch(e){}}
var v='normal';try{v=localStorage.getItem(k)||'normal'}catch(e){}
set(v);document.querySelectorAll('.size button').forEach(function(b){b.onclick=function(){set(b.dataset.v)}});})();
"""

WEEK = "月火水木金土日"


def when(d: datetime, now: datetime) -> str:
    """「今日 6:10」「きのう 21:30」のような分かりやすい表記。"""
    days = (now.date() - d.date()).days
    hm = f"{d.hour}:{d.minute:02d}"
    if days == 0:
        return f"今日 {hm}"
    if days == 1:
        return f"きのう {hm}"
    return f"{d.month}月{d.day}日 {hm}"


def render(cfg: dict, items: list[Item], errors: list[str], now: datetime) -> str:
    limit = cfg.get("max_items_per_section", 60)
    e = html.escape

    def block(sec_id: str, label: str) -> str:
        rows = [i for i in items if i.section == sec_id][:limit]
        lis = []
        for i in rows:
            d = datetime.fromisoformat(i.published)
            fresh = '<span class="new">新着</span>' if now - d < timedelta(hours=12) else ""
            lis.append(
                f'<li><a href="{e(i.link)}" target="_blank" rel="noopener">{fresh}{e(i.title)}'
                f'<span class="meta">{e(i.source)}・{when(d, now)}</span></a></li>'
            )
        body = "\n".join(lis) if lis else '<li class="empty">今日はニュースがありません</li>'
        return f'<section id="{sec_id}"><h2>{label} <small>{len(rows)}件</small></h2><ul>{body}</ul></section>'

    err = "<p>※一部の配信元から取得できませんでした。</p>" if errors else ""
    title = e(cfg["title"])
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="theme-color" content="#b3261e">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="スポーツ">
<style>{CSS}</style></head>
<body><main id="top">
<header><h1>{title}</h1><p>{now.month}月{now.day}日（{WEEK[now.weekday()]}）{now.hour}時{now.minute:02d}分 更新</p></header>
<div class="size" role="group" aria-label="文字の大きさ">文字の大きさ
<button data-v="normal" aria-pressed="true">普通</button><button data-v="big" aria-pressed="false">大</button><button data-v="huge" aria-pressed="false">特大</button></div>
<nav><a href="#sumo">相撲</a><a href="#other">その他のスポーツ</a></nav>
{block('sumo', '相撲')}
{block('other', 'その他のスポーツ')}
<a class="top" href="#top">▲ いちばん上へ</a>
<footer>{err}<p>毎朝7時ごろに新しくなります。見出しを押すと記事が開きます。</p><p>記事の著作権は各配信元に帰属します。</p></footer>
</main><script>{SIZE_JS}</script></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(HERE / "config.json"))
    ap.add_argument("--out", default="site")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    now = datetime.now(JST)
    items, errors = collect(cfg, now)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    # アイコン・マニフェスト・使い方ページなどをコピー
    for f in (HERE / "static").iterdir():
        if f.is_file():
            shutil.copy2(f, out / f.name)
    (out / "index.html").write_text(render(cfg, items, errors, now), encoding="utf-8")
    (out / "news.json").write_text(
        json.dumps({"generated": now.isoformat(), "items": [asdict(i) for i in items]},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    n_sumo = sum(i.section == "sumo" for i in items)
    print(f"done: {len(items)} items (sumo {n_sumo}) -> {out}/index.html", file=sys.stderr)
    # 全フィードが失敗したときだけ異常終了
    return 1 if len(errors) == len(cfg["feeds"]) else 0


if __name__ == "__main__":
    sys.exit(main())
