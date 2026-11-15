# 朝のスポーツニュース（相撲優先）

毎朝 7 時（JST）までに、スポーツニュースの見出しを集めて 1 ページの一覧にします。
相撲関連の記事は「🏆 相撲」セクションに分けて先頭に表示します。

## 仕組み
- `fetch_news.py` … RSS/Atom（Google ニュース検索・NHK・Yahoo!ニュース）を取得し、
  重複除去・直近 36 時間で絞り込み・相撲判定をして `site/index.html` と `site/news.json` を出力
- `.github/workflows/sports-news.yml` … 毎日 06:40 JST に実行し GitHub Pages に公開
- Python 標準ライブラリのみ（pip インストール不要）

## 初回セットアップ
1. このブランチをデフォルトブランチ（main 等）にマージする（定時実行はデフォルトブランチでのみ動きます）
2. リポジトリの Settings → Pages → Source を **GitHub Actions** にする
3. Actions タブ →「朝のスポーツニュース」→ **Run workflow** で一度手動実行
4. 表示された URL（`https://<ユーザー名>.github.io/<リポジトリ名>/`）をスマホのホーム画面に追加

## カスタマイズ（config.json）
- `feeds` … フィードの追加・削除。`section: "sumo"` はすべて相撲扱い、`"auto"` はキーワードで自動判定
- `sumo_keywords` … 相撲と判定する語（力士名を足すと精度が上がります）
- `hours` … 何時間前までの記事を載せるか

## ローカル実行
```
python3 sports_news/fetch_news.py --out site
open site/index.html
```
