# 朝のスポーツニュース（相撲優先）

毎朝 7 時（JST）までに、スポーツニュースの見出しを集めて 1 ページの一覧にします。
相撲関連の記事は「🏆 相撲」セクションに分けて先頭に表示します。

## 仕組み
- `fetch_news.py` … RSS/Atom（Google ニュース検索・NHK・Yahoo!ニュース）を取得し、
  重複除去・直近 36 時間で絞り込み・相撲判定をして `site/index.html` と `site/news.json` を出力
- `.github/workflows/sports-news.yml` … 毎日 06:40 JST に実行し GitHub Pages に公開
- `static/` … アイコン・マニフェスト・使い方ページ（`howto.html`）。そのまま公開フォルダにコピーされます
- Python 標準ライブラリのみ（pip インストール不要）

## 初回セットアップ（済んでいないのは 1 だけ）
1. **GitHub Pages を有効にする**（リポジトリ所有者にしかできない設定です）
   https://github.com/Naokiman-8636/-/settings/pages を開き、
   「Build and deployment」→「Source」を **GitHub Actions** に変更
2. Actions タブ →「朝のスポーツニュース」→ **Run workflow**（または Claude に再実行を依頼）
3. 緑の ✓ になったら https://naokiman-8636.github.io/-/ が開けます

## うまく動かないとき
| 症状 | 原因と対策 |
|---|---|
| ページが 404 | Pages が未設定。上の手順 1 を実施し、ワークフローを再実行 |
| deploy が「Get Pages site failed」で失敗 | 同上（Pages が無効） |
| deploy が「not allowed to deploy to github-pages」で失敗 | デフォルトブランチ以外から公開しようとしている。デフォルトブランチで実行する |
| 毎朝更新されない | 定時実行はデフォルトブランチのワークフローのみ動作。Actions タブで無効化されていないか確認 |
| 記事が少ない・偏る | ワークフローのログ「ニュース収集」に配信元ごとの「採用/古い/重複」件数が出るので確認 |

## 家族（父など）に使ってもらう
ページは公開されているので、URL を知っていればログイン不要・無料で誰でも見られます。

1. 使い方ページ **https://naokiman-8636.github.io/-/howto.html** を LINE やメールで送る
2. 本人にその手順どおり「ホーム画面に追加」してもらう（iPhone/Android 両方の手順入り）
3. 以後は赤い「相」アイコンを押すだけで、毎朝更新された一覧が開きます

見やすさの工夫: 大きめの文字（「大」「特大」ボタンで切替・設定は端末に記憶）、
押しやすい大きな行、「今日 6:10」「きのう 21:30」形式の時刻、12時間以内の記事に「新着」表示。

## カスタマイズ（config.json）
- `feeds` … フィードの追加・削除。`section: "sumo"` はすべて相撲扱い、`"auto"` はキーワードで自動判定
- `sumo_keywords` … 相撲と判定する語（力士名を足すと精度が上がります）
- `hours` … 何時間前までの記事を載せるか

## ローカル実行
```
python3 sports_news/fetch_news.py --out site
open site/index.html
```
