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
    """HTML内の<script>に埋め込む安全なJS文字列リテラルを作る。"""
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")


def build_dm_button_html(label: str, url: str, copy_text: str) -> str:
    """DM送信ボタンのHTMLを生成する。

    クリックすると ``copy_text`` をクリップボードにコピーし、
    同時に ``url``(DM作成画面)を新しいタブで開く。
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
    background-color: rgba(151, 166, 195, 0.15);
    color: inherit;
    font-size: 0.875rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    box-sizing: border-box;
}}
.st-dm-btn:hover {{ border-color: rgb(49, 51, 63); }}
</style>
<a class="st-dm-btn" href="{href}" target="_blank" rel="noopener noreferrer" id="st-dm-link">{label_escaped}</a>
<script>
(function () {{
    var link = document.getElementById('st-dm-link');
    var text = {text_literal};
    var original = link ? link.textContent : '';
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
    if (link) {{
        link.addEventListener('click', function () {{
            copyText(text, function () {{
                link.textContent = '✓ コピーしました';
                setTimeout(function () {{ link.textContent = original; }}, 2000);
            }});
        }});
    }}
}})();
</script>
"""
