# xni_post_and_dm_draft_okuru_yatsu

X(旧Twitter)にPostとDMを送るStreamlit Web GUIアプリ。

## 機能

- 感想テキストボックス
- **Post送信**ボタン → Xの投稿作成画面(下書き状態)を新しいタブで開く
- **DM送信**ボタン → XのDM作成画面(ミューコミVR @mc1242 宛)を新しいタブで開く

## テンプレート

`template.yaml` を読み込み、プレースホルダを置換して送信テキストを生成します。

| プレースホルダ | 置換内容 |
| --- | --- |
| `ここ感想` | 感想テキストボックスの内容(空欄ならプレースホルダごと消える) |
| `YYYY/MM/DD` | 今日の日付(Asia/Tokyo) |

## セットアップ

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 使い方

1. 感想を入力する(空欄でもOK)
2. 生成テキストをプレビューで確認する(280文字超は警告)
3. **Post送信** → Xの投稿作成画面が開き、テキストが入力済み
4. **DM送信** → XのDM作成画面が開き、ミューコミVR宛にテキストが入力済み
5. Xの画面で確認して送信(または下書き保存)

送信先の変更はサイドバーの「DM送信先 User ID」で行えます(初期値: `100786821`)。

## ファイル構成

- `app.py` — Streamlit GUI
- `draft_generator.py` — テキスト/URL生成ロジック(Streamlit非依存)
- `template.yaml` — 送信テンプレート
- `test_draft_generator.py` — 単体テスト

## テスト

```bash
python -m unittest test_draft_generator
```

