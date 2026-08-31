"""X(旧Twitter)にPostとDMを送るStreamlit Web GUIアプリ。

template.yaml を読み込み、感想テキストボックスの内容と今日の日付で
プレースホルダを置換したテキストを生成する。
ボタンを押すとXの投稿作成画面 / DM作成画面を新しいタブで開く。
"""

from pathlib import Path

import streamlit as st

from draft_generator import (
    build_dm_url,
    build_post_url,
    build_text,
    load_config,
    today_str,
)

TEMPLATE_PATH = Path(__file__).parent / "template.yaml"

st.set_page_config(page_title="X Post/DM 送信", page_icon="🐦")

st.title("X Post / DM 送信")
st.caption(f"設定ファイル: `{TEMPLATE_PATH.name}`")

try:
    config = load_config(TEMPLATE_PATH)
except (FileNotFoundError, ValueError) as e:
    st.error(e)
    st.stop()

template = config["template"]
dm_address_id = config["dm_address_id"]

# ---------- メイン ----------
impression = st.text_area(
    "感想",
    placeholder="曲の感想を入力してください（空欄でもOK）",
    height=130,
)

text = build_text(template, impression, today_str())

st.subheader("生成テキスト")
st.text_area(
    "生成テキスト（コピー用）",
    value=text,
    height=170,
    disabled=True,
    label_visibility="collapsed",
)

char_count = len(text)
if char_count > 280:
    st.warning(
        f"文字数が {char_count} 文字です。XのPost上限(280文字)を超えています。"
    )
else:
    st.caption(f"文字数: {char_count} / 280")

post_url = build_post_url(text)
dm_url = build_dm_url(text, dm_address_id)

col1, col2 = st.columns(2)
with col1:
    st.link_button("📨 Post送信", post_url)
with col2:
    st.link_button("✉️ DM送信", dm_url)

st.caption(
    "ボタンを押すと、Xの投稿作成 / DM作成画面が新しいタブで開き、テキストが入力済みの状態になります。"
    "その画面で確認して送信（または下書き保存）してください。"
)

st.subheader("生成URL")
st.text_input("Post URL", value=post_url, disabled=True)
st.text_input("DM URL", value=dm_url, disabled=True)

with st.expander("テンプレート (template.yaml)"):
    st.code(template)
