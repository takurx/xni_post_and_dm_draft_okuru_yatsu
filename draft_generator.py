"""テンプレートからX(旧Twitter)送信用テキストとURLを生成するロジックモジュール。

Streamlitに依存しない純粋ロジックとして切り出してあり、単体テストができる。
"""

import html
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import yaml
from zoneinfo import ZoneInfo

TIMEZONE = "Asia/Tokyo"

# WindowsではIANAタイムゾーンデータにtzdataパッケージが必要。
# 無い環境でもローカル時刻で動くようフォールバックする。
try:
    _TZ = ZoneInfo(TIMEZONE)
except Exception:
    _TZ = None


def today_str() -> str:
    """今日の日付を ``YYYY/MM/DD`` 形式で返す。"""
    now = datetime.now(_TZ) if _TZ else datetime.now()
    return now.strftime("%Y/%m/%d")


def load_config(path: str | Path) -> dict:
    """template.yaml を読み込んで設定dictを返す。

    キー:
    - ``dm_address``: DM送信先の実際のUser ID(数値)
    - ``dm_address_id``: DM送信先のアカウント名(例: mc1242)
    - ``template``: 投稿テンプレート(プレースホルダ: ここ感想 / YYYY/MM/DD)

    ファイルが無ければ FileNotFoundError、形式が不正なら ValueError。
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("template.yaml の形式が正しくありません(dictが必要)")
    for key in ("dm_address", "dm_address_id", "template"):
        if key not in data:
            raise ValueError(f"template.yaml に {key} がありません")
    return {
        "dm_address": str(data["dm_address"]).strip(),
        "dm_address_id": str(data["dm_address_id"]).strip(),
        "template": str(data["template"]).strip(),
    }


def build_text(template: str, impression: str, date: str) -> str:
    """テンプレートのプレースホルダを置換して送信テキストを生成する。

    - ``ここ感想``  -> 感想テキスト(空ならプレースホルダごと消す)
    - ``YYYY/MM/DD`` -> 日付
    """
    impression = (impression or "").strip()

    if impression:
        text = template.replace("ここ感想", impression)
    else:
        # 空欄のときは「ここ感想」と直後のスペースごと消して日付だけ残す
        text = template.replace("ここ感想 ", "").replace("ここ感想", "")

    return text.replace("YYYY/MM/DD", date)


def build_post_url(text: str) -> str:
    """Xの投稿作成画面を開くURLを生成する。"""
    return "https://x.com/intent/post?text=" + quote(text, safe="()")


def build_dm_url(text: str, recipient_id: str) -> str:
    """XのDM作成画面(指定ユーザー宛)を開くURLを生成する。"""
    return (
        "https://x.com/messages/compose"
        f"?recipient_id={quote(str(recipient_id), safe='()')}"
        f"&text={quote(text, safe='()')}"
    )


def _js_string(value: str) -> str:
    """HTML内の<script>に埋め込む安全なJS文字列リテラルを作る。

    ``</script>`` によるscriptタグの終了を防ぎ、JS文字列として不正な
    ``\\u2028``(行区切り) / ``\\u2029``(段落区切り)をエスケープする。
    """
    s = json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")
    return s.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def build_dm_button_html(label: str, url: str, copy_text: str) -> str:
    """DM送信ボタンのHTMLを生成する。

    クリック時に:
    - copy_text をクリップボードへコピー
    - url のDM作成画面を新しいタブで開く

    見た目は可能なら親ページの st.link_button を参照し、
    Streamlit標準ボタンの計算済みスタイルをコピーする。
    取得できない場合は親ページの背景色からライト/ダークを判定して
    フォールバック配色を適用する。
    """
    label_escaped = html.escape(label)
    href = html.escape(url, quote=True)
    text_literal = _js_string(copy_text)

    return f"""
<style>
body {{
    margin: 0;
}}

.st-dm-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;

    height: 2.5rem;
    padding: 0 0.9rem;

    border: 1px solid rgba(250, 250, 250, 0.2);
    border-radius: 0.5rem;

    background: transparent;
    color: #FAFAFA;

    font-size: 0.875rem;
    font-weight: 600;
    text-decoration: none;

    cursor: pointer;
    box-sizing: border-box;
}}

.st-dm-btn:hover {{
    filter: brightness(0.9);
}}

.st-dm-btn:active {{
    filter: brightness(0.8);
}}
</style>

<a
    id="st-dm-link"
    class="st-dm-btn"
    href="{href}"
    target="_blank"
    rel="noopener noreferrer"
>
    {label_escaped}
</a>

<script>
(() => {{
    const link = document.getElementById("st-dm-link");
    if (!link) return;

    const copyTextValue = {text_literal};
    const originalLabel = link.textContent;

    const nativeStyleProps = [
        "color",
        "background-color",
        "border-color",
        "border-width",
        "border-style",
        "border-radius",
        "font-family",
        "font-size",
        "font-weight",
        "line-height",
        "height",
        "padding",
        "box-shadow"
    ];

    function findNativePostButton() {{
        try {{
            const doc = window.parent.document;

            return (
                doc.querySelector('a[data-testid^="stBaseLinkButton"]') ||
                doc.querySelector('[data-testid="stLinkButton"] a')
            );
        }} catch {{
            return null;
        }}
    }}

    function applyNativeStyle() {{
        const nativeButton = findNativePostButton();
        if (!nativeButton) return false;

        try {{
            const cs = window.parent.getComputedStyle(nativeButton);

            for (const prop of nativeStyleProps) {{
                const value = cs.getPropertyValue(prop);
                if (value) {{
                    link.style.setProperty(prop, value);
                }}
            }}

            return true;
        }} catch {{
            return false;
        }}
    }}

    function getParentBackgroundColor() {{
        try {{
            const doc = window.parent.document;
            const candidates = [
                doc.querySelector(".stApp"),
                doc.body,
                doc.documentElement
            ];

            for (const el of candidates) {{
                if (!el) continue;

                const bg = window.parent.getComputedStyle(el).backgroundColor;
                if (bg && bg !== "transparent" && bg !== "rgba(0, 0, 0, 0)") {{
                    return bg;
                }}
            }}
        }} catch {{}}

        return null;
    }}

    function isDarkColor(rgb) {{
        if (!rgb) return true;

        const match = rgb.match(
            /rgba?\\(\\s*(\\d+)\\D+(\\d+)\\D+(\\d+)/
        );

        if (!match) return true;

        const r = Number(match[1]);
        const g = Number(match[2]);
        const b = Number(match[3]);

        const luminance =
            0.299 * r +
            0.587 * g +
            0.114 * b;

        return luminance < 128;
    }}

    function applyFallbackTheme() {{
        const dark = isDarkColor(getParentBackgroundColor());

        if (dark) {{
            link.style.color = "#FAFAFA";
            link.style.borderColor = "rgba(250, 250, 250, 0.2)";
        }} else {{
            link.style.color = "#31333F";
            link.style.borderColor = "rgba(49, 51, 63, 0.2)";
        }}

        link.style.backgroundColor = "transparent";
    }}

    function syncStyle() {{
        if (!applyNativeStyle()) {{
            applyFallbackTheme();
        }}
    }}

    function fallbackCopy(text) {{
        const textarea = document.createElement("textarea");

        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        textarea.style.opacity = "0";

        document.body.appendChild(textarea);

        textarea.focus();
        textarea.select();

        try {{
            document.execCommand("copy");
        }} catch {{}}

        textarea.remove();
    }}

    async function copyToClipboard(text) {{
        try {{
            if (navigator.clipboard && window.isSecureContext) {{
                await navigator.clipboard.writeText(text);
                return;
            }}
        }} catch {{}}

        fallbackCopy(text);
    }}

    async function handleClick() {{
        syncStyle();

        await copyToClipboard(copyTextValue);

        link.textContent = "✓ コピーしました";

        setTimeout(() => {{
            link.textContent = originalLabel;
        }}, 2000);
    }}

    function initStyle(retry = 0) {{
        if (applyNativeStyle()) return;

        if (retry < 20) {{
            setTimeout(() => initStyle(retry + 1), 100);
        }} else {{
            applyFallbackTheme();
        }}
    }}

    initStyle();

    link.addEventListener("click", handleClick);
}})();
</script>
"""
