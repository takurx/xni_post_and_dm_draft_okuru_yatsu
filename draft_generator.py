"""テンプレートからX(旧Twitter)送信用テキストとURLを生成するロジックモジュール。

Streamlitに依存しない純粋ロジックとして切り出してあり、単体テストができる。
"""

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
    - ``dm_address_id``: DM送信先のUser ID
    - ``template``: 投稿テンプレート(プレースホルダ: ここ感想 / YYYY/MM/DD)

    ファイルが無ければ FileNotFoundError、形式が不正なら ValueError。
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {p}")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("template.yaml の形式が正しくありません(dictが必要)")
    if "dm_address_id" not in data:
        raise ValueError("template.yaml に dm_address_id がありません")
    if "template" not in data:
        raise ValueError("template.yaml に template がありません")
    return {
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
