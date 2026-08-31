# xni_post_and_dm_draft_okuru_yatsu

X(旧Twitter)にPostとDMを送るStreamlit Web GUIアプリ。

## 機能

- 感想テキストボックス
- **Post送信**ボタン → Xの投稿作成画面(下書き状態)を新しいタブで開く
- **DM送信**ボタン → 生成テキストをクリップボードにコピーしてから、XのDM作成画面(ミューコミVR @mc1242 宛)を新しいタブで開く
- 生成テキストのプレビューと生成URLを常時表示

## テンプレート (template.yaml)

`template.yaml` から投稿テンプレートとDM送信先を読み込みます。

```yaml
dm_address: 100786821
dm_address_id: mc1242
template: |
  (早乙女あずき)さんの『Elysium』に投票します！
  ここ感想 YYYY/MM/DD
  #ミューコミＶＲ #VTuber楽曲ランキング
  https://www.youtube.com/watch?v=01Mpk-w688s
```

| キー | 内容 |
| --- | --- |
| `dm_address` | DM送信先の実際のUser ID(数値) |
| `dm_address_id` | DM送信先のアカウント名(例: mc1242) |
| `template` | 投稿テンプレート |

テンプレート内のプレースホルダは以下のように置換されます。

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
4. **DM送信** → 生成テキストがクリップボードにコピーされ、XのDM作成画面(`dm_address`で指定した相手宛)が開く
5. DMは送信前にクリップボードから貼り付けて内容を確認してから送信する

## ファイル構成

- `app.py` — Streamlit GUI
- `draft_generator.py` — テキスト/URL生成ロジック(Streamlit非依存)
- `template.yaml` — DM送信先と投稿テンプレート
- `test_draft_generator.py` — 単体テスト

## テスト

```bash
python -m unittest test_draft_generator
```


