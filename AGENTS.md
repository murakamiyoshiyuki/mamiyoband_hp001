# マミヨバンド公式HP — AI編集ルール

## 対象
- 本番URL: https://mamiyoband.com/
- GitHub: `murakamiyoshiyuki/mamiyoband_hp001`
- 公開元: `main` ブランチ / GitHub Pages
- 目的: NEWS、LIVE INFO、出演情報、画像、文章の更新

## 絶対ルール
1. 作業開始時に `git pull --ff-only` を実行し、他スタッフの更新を取り込む。
2. 日付・曜日・会場・出演者・料金・URLは、フライヤーまたは依頼文の現物と照合する。推測しない。
3. 未発表項目は「後日発表」。デザインや過去ページは依頼がない限り変更しない。
4. 画像は `素材/CMS/` へ保存する。秘密情報・個人情報・認証情報はコミットしない。
5. 公開前に必ず `python3 scripts/validate_site.py` を実行し、`PASS`を確認する。
6. 公開後は本番URLをPC幅・スマホ幅で開き、変更ページ、NEWS、LIVE INFO、画像、リンクを確認する。

## AIの標準更新手順
```bash
git pull --ff-only
# 必要なファイルだけ編集
python3 scripts/validate_site.py
git status --short
git diff --check
git add <今回変更したファイルだけ>
git commit -m "Update: 更新内容"
git push origin main
```

- 未追跡・他人の作業中ファイルを勝手に追加、削除、上書きしない。
- `git add -A`、`git reset --hard`、強制pushは禁止。
- 検査失敗時はpushせず、原因を修正する。
- GitHub Pagesの公開完了と本番表示を確認するまで「完了」と報告しない。

## 管理画面で作られるファイル
- 投稿本文: `_updates/*.md`
- 投稿画像: `素材/CMS/`
- 管理画面設定: `.pages.yml`（管理者以外は変更しない）
- 表示テンプレート: `_layouts/update.html`（通常の投稿では変更しない）
