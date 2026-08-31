"""X(旧Twitter)にPostとDMを送るStreamlit Web GUIアプリ。

template.yaml を読み込み、感想テキストボックスの内容と今日の日付で
プレースホルダを置換したテキストを生成する。
- Post送信ボタン: Xの投稿作成画面を新しいタブで開く
- DM送信ボタン: 生成テキストをクリップボードにコピーしてからXのDM作成画面を開く
"""

from pathlib import Path

import streamlit as st

from draft_generator import (
    build_dm_button_html,
    build_dm_url,
    build_post_url,
    build_text,
    load_config,
    today_str,
)

TEMPLATE_PATH = Path(__file__).parent / "template.yaml"

st.set_page_config(page_title="早乙女あずきさんのElysiumをミューコミVRの長イントロ編に投票するXのPost/DMのDraftを作るやつ v0.7", page_icon="🏴")

st.title("早乙女あずきさんのElysiumをミューコミVRの長イントロ編に投票するXのPost/DMのDraftを作るやつ v0.7")
#st.caption(f"設定ファイル: `{TEMPLATE_PATH.name}`")
st.markdown(
    """
    **ミューコミVRの長イントロ編** の投票期間：～2026/09/22 23:59 JST
    
    - 1日1回までXのPostと@mc1242へのDMでの投票ができます  
    - アーティスト名と曲名とハッシュタグのテンプレートがあります  
    - 投票理由や応援コメントなど感想が付けられます
    
    投票ルール詳細：[https://x.com/mc1242/status/2094084197917093989](https://x.com/mc1242/status/2094084197917093989)
    """
)

try:
    config = load_config(TEMPLATE_PATH)
except (FileNotFoundError, ValueError) as e:
    st.error(e)
    st.stop()

template = config["template"]
dm_address = config["dm_address"]
dm_address_id = config["dm_address_id"]

st.caption(f"DM送信先: @{dm_address_id} (User ID: {dm_address})")

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
dm_url = build_dm_url(text, dm_address)

col1, col2 = st.columns(2)
with col1:
    st.link_button("📨 Post送信", post_url)
with col2:
    st.iframe(
        build_dm_button_html("✉️ DM送信", dm_url, text),
        width="content",
        height=50,
    )

st.caption(
    "**Post送信**: Xの投稿作成画面を新しいタブで開きます。"
)
st.caption(
    "**DM送信**: 生成テキストをクリップボードにコピーしてから、XのDM作成画面(新しいタブ)を開きます。"
    "DMは送信前に貼り付けて内容を必ず確認してください。"
)

st.subheader("生成URL")
st.text_input("Post URL", value=post_url, disabled=False)
st.text_input("DM URL", value=dm_url, disabled=False)

# with st.expander("テンプレート (template.yaml)"):
#     st.code(template)
