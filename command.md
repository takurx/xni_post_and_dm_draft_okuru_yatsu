# command.md
cluade, cline, vscodeに送るコマンド

## draft 1
XにPostのdraftとDMのdraftを送るstreamlitのWeb GUIアプリを作る

GUIとしては以下の要素がある
- 感想のテキストボックスがある
- Post送信ボタンがある
- DM送信ボタンがある

事前に送るテンプレートがある, template.yaml
テンプレートの内容としては下記である

```yaml
(早乙女あずき)さんの『Elysium』に投票します！
ここ感想 YYYY/MM/DD
#ミューコミＶＲ #VTuber楽曲ランキング
https://www.youtube.com/watch?v=01Mpk-w688s
```

ここ感想のところにテキストボックスで入力した内容が入る。テキストボックスが空であれば。空にする。
YYYY/MM/DDのところに今日の日付が入る。

## 追加draft 2
- postは下記のようにリンクを生成してボタン１つで送れる状態にする
https://x.com/intent/post?text=(%E6%97%A9%E4%B9%99%E5%A5%B3%E3%81%82%E3%81%9A%E3%81%8D)%E3%81%AE%E3%80%8EElysium%E3%80%8F%E3%81%AB%E6%8A%95%E7%A5%A8%E3%81%97%E3%81%BE%E3%81%99%EF%BC%81%0A%23%E3%83%9F%E3%83%A5%E3%83%BC%E3%82%B3%E3%83%9F%EF%BC%B6%EF%BC%B2%0A%23VTuber%E6%A5%BD%E6%9B%B2%E3%83%A9%E3%83%B3%E3%82%AD%E3%83%B3%E3%82%B0
- dmは下記のようにリンクを生成してボタン１つで送れる状態にする
https://x.com/messages/compose?recipient_id=100786821&text=(%E6%97%A9%E4%B9%99%E5%A5%B3%E3%81%82%E3%81%9A%E3%81%8D)%E3%81%AE%E3%80%8EElysium%E3%80%8F%E3%81%AB%E6%8A%95%E7%A5%A8%E3%81%97%E3%81%BE%E3%81%99%EF%BC%81%0A%23%E3%83%9F%E3%83%A5%E3%83%BC%E3%82%B3%E3%83%9FVR%0A%23VTuber%E6%A5%BD%E6%9B%B2%E3%83%A9%E3%83%B3%E3%82%AD%E3%83%B3%E3%82%B0
- DMはミューコミVR @mc1242宛に送る

## draft sprint 3
- template.yamlの内容を変更に合わせる
  - side barは不要
  - DM送信先はtemplate.yamlのdm_address_idから取得する
  - 投稿内容のテンプレートはtemplate.yamlのtemplate以下になる
- 生成したURLも表示するは常に表示する

## draft sprint 4
- DM送信ボタンは、現在の内容にかつ、生成した送信内容をclipboardにコピーするようにする（DM送信のセキュリティ対策のため）
- template.yamlのdm_address_idはアカウント名を事前に指定する (例: mc1242)
- template.yamlのdm_addressは実際のIDを確認して保存する

## question 1
DM送信ボタンの色が変わったのはなぜ？

