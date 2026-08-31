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

    クリックすると ``copy_text`` をクリップボードにコピーし、
    同時に ``url``(DM作成画面)を新しいタブで開く。

    配色は同じページ内にあるネイティブのPost送信ボタン(``st.link_button``)の
    計算済みスタイルをそのままコピーするため、Streamlitのテーマ
    (ライト/ダーク/カスタム)に完全に追従する。
    """
    label_escaped = html.escape(label)
    href = html.escape(url, quote=True)
    text_literal = _js_string(copy_text)
    return f"""\
<style>
body {{ margin: 0; }}
.st-dm-btn {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 2.5rem;
    padding: 0 0.9rem;
    border: 1px solid rgba(49, 51, 63, 0.2);
    border-radius: 0.5rem;
    background-color: transparent;
    color: #31333F;
    font-size: 0.875rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    box-sizing: border-box;
}}
.st-dm-btn:hover {{
    background-color: color-mix(in srgb, black 15%, var(--dm-bg, transparent));
}}
.st-dm-btn:active {{
    background-color: color-mix(in srgb, black 25%, var(--dm-bg, transparent));
}}
</style>
<a class="st-dm-btn" href="{href}" target="_blank" rel="noopener noreferrer" id="st-dm-link">{label_escaped}</a>
<script>
(function () {{
    var link = document.getElementById('st-dm-link');
    var text = {text_literal};
    var original = link ? link.textContent : '';

    // 親ページのPost送信ボタン(ネイティブ st.link_button)の計算済みスタイルをコピーする
    function applyNativeStyle() {{
        if (!link) return false;
        try {{
            var doc = window.parent.document;
            var post = doc.querySelector('a[data-testid^="stBaseLinkButton"]')
                    || doc.querySelector('[data-testid="stLinkButton"] a');
            if (!post) return false;
            var cs = window.parent.getComputedStyle(post);
            var props = [
                'color', 'backgroundColor', 'borderColor', 'borderWidth', 'borderStyle',
                'borderRadius', 'fontFamily', 'fontSize', 'fontWeight', 'lineHeight',
                'height', 'padding', 'boxShadow'
            ];
            for (var i = 0; i < props.length; i++) {{
                var v = cs.getPropertyValue(props[i]);
                if (v) link.style[props[i]] = v;
            }}
            link.style.setProperty('--dm-bg', cs.getPropertyValue('backgroundColor') || 'transparent');
            return true;
        }} catch (e) {{
            return false;
        }}
    }}

    // フォールバック: 親ページの背景色の明るさからライト/ダークを判定して配色する
    function applyFallbackTheme() {{
        if (!link) return;
        var dark = false;
        try {{
            var doc = window.parent.document;
            var cands = [doc.documentElement, doc.body, doc.querySelector('.stApp')];
            for (var i = 0; i < cands.length; i++) {{
                if (!cands[i]) continue;
                var bg = window.parent.getComputedStyle(cands[i]).backgroundColor;
                var m = bg && bg.match(/rgba?\\((\\d+)[,\\s]+(\\d+)[,\\s]+(\\d+)(?:[,\\s]+([\\d.]+))?\\)/);
                if (m) {{
                    var alpha = m[4] === undefined ? 1 : parseFloat(m[4]);
                    if (alpha > 0) {{
                        var lum = 0.299 * +m[1] + 0.587 * +m[2] + 0.114 * +m[3];
                        dark = lum < 128;
                        break;
                    }}
                }}
            }}
        }} catch (e) {{}}
        if (dark) {{
            link.style.color = '#FAFAFA';
            link.style.borderColor = 'rgba(250, 250, 250, 0.2)';
        }} else {{
            link.style.color = '#31333F';
            link.style.borderColor = 'rgba(49, 51, 63, 0.2)';
        }}
        link.style.setProperty('--dm-bg', link.style.backgroundColor || 'transparent');
    }}

    function fallbackCopy(t) {{
        var ta = document.createElement('textarea');
        ta.value = t;
        ta.style.position = 'fixed';
        ta.style.top = '-1000px';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        try {{ document.execCommand('copy'); }} catch (e) {{}}
        document.body.removeChild(ta);
    }}
    function copyText(t, done) {{
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(t).then(
                function () {{ if (done) done(); }},
                function () {{ fallbackCopy(t); if (done) done(); }}
            );
        }} else {{
            fallbackCopy(t);
            if (done) done();
        }}
    }}

    // 読み込み時に適用。親のボタンがまだ描画されていなければ少し待って再試行する
    var tries = 0;
    (function init() {{
        if (applyNativeStyle() || tries++ >= 20) {{
            if (!applyNativeStyle()) applyFallbackTheme();
            return;
        }}
        setTimeout(init, 100);
    }})();

    if (link) {{
        link.addEventListener('click', function () {{
            if (!applyNativeStyle()) applyFallbackTheme();
            copyText(text, function () {{
                link.textContent = '✓ コピーしました';
                setTimeout(function () {{ link.textContent = original; }}, 2000);
            }});
        }});
    }}
}})();
</script>
"""
