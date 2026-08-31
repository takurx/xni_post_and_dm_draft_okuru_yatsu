"""draft_generator の単体テスト。

実行方法: python -m unittest test_draft_generator
"""

import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

from draft_generator import (
    build_dm_button_html,
    build_dm_url,
    build_post_url,
    build_text,
    load_config,
    today_str,
)

TEMPLATE = (
    "(早乙女あずき)さんの『Elysium』に投票します！\n"
    "ここ感想 YYYY/MM/DD\n"
    "#ミューコミＶＲ #VTuber楽曲ランキング\n"
    "https://www.youtube.com/watch?v=01Mpk-w688s"
)


class ConfigTest(unittest.TestCase):
    def test_load_config_実ファイル(self):
        config = load_config("template.yaml")
        self.assertEqual(config["dm_address"], "100786821")
        self.assertEqual(config["dm_address_id"], "mc1242")
        self.assertIn("(早乙女あずき)さんの『Elysium』に投票します！", config["template"])
        self.assertIn("ここ感想 YYYY/MM/DD", config["template"])
        self.assertIn("#ミューコミＶＲ #VTuber楽曲ランキング", config["template"])
        self.assertIn("https://www.youtube.com/watch?v=01Mpk-w688s", config["template"])

    def test_load_config_無いファイル(self):
        with self.assertRaises(FileNotFoundError):
            load_config("no_such_file_please.yaml")

    def test_load_config_形式不正(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("ただの文字列\n")
            tmp = f.name
        try:
            with self.assertRaises(ValueError):
                load_config(tmp)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_load_config_キー不足(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("dm_address: 12345\n")
            f.write("template: |\n")
            f.write("  hello\n")
            tmp = f.name
        try:
            with self.assertRaises(ValueError):
                load_config(tmp)
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_load_config_数値は文字列化(self):
        with tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write("dm_address: 999\n")
            f.write("dm_address_id: mc1242\n")
            f.write("template: |\n")
            f.write("  hello\n")
            tmp = f.name
        try:
            config = load_config(tmp)
            self.assertEqual(config["dm_address"], "999")
            self.assertEqual(config["dm_address_id"], "mc1242")
            self.assertEqual(config["template"], "hello")
        finally:
            Path(tmp).unlink(missing_ok=True)


class BuildTextTest(unittest.TestCase):
    def test_impression_あり(self):
        text = build_text(TEMPLATE, "めっちゃいい曲", "2026/08/31")
        self.assertIn("めっちゃいい曲 2026/08/31", text)
        self.assertNotIn("ここ感想", text)
        self.assertNotIn("YYYY/MM/DD", text)

    def test_impression_空(self):
        text = build_text(TEMPLATE, "", "2026/08/31")
        self.assertNotIn("ここ感想", text)
        self.assertNotIn("YYYY/MM/DD", text)
        # 「ここ感想 」ごと消えて日付だけの行になる
        self.assertIn("\n2026/08/31\n", text)
        self.assertNotIn(" 2026/08/31", text)

    def test_空白のみ_空扱い(self):
        text = build_text(TEMPLATE, "   \n ", "2026/08/31")
        self.assertNotIn("ここ感想", text)
        self.assertIn("\n2026/08/31\n", text)

    def test_前後空白は除去(self):
        text = build_text(TEMPLATE, "  最高でした  ", "2026/08/31")
        self.assertIn("最高でした 2026/08/31", text)
        self.assertNotIn("  ", text[: text.index("最高") + 1])

    def test_テンプレートの他行は維持(self):
        text = build_text(TEMPLATE, "最高", "2026/08/31")
        self.assertIn("(早乙女あずき)さんの『Elysium』に投票します！", text)
        self.assertIn("#ミューコミＶＲ #VTuber楽曲ランキング", text)
        self.assertIn("https://www.youtube.com/watch?v=01Mpk-w688s", text)


class UrlTest(unittest.TestCase):
    def test_post_url_形式(self):
        url = build_post_url("テスト")
        self.assertTrue(url.startswith("https://x.com/intent/post?text="))

    def test_post_url_丸括弧はそのまま(self):
        url = build_post_url("(早乙女あずき)のElysium")
        self.assertIn("text=(", url)
        self.assertIn(")%E3%81%AE", url)  # ) はそのまま、の はエンコード

    def test_post_url_日本語と記号はエンコード(self):
        url = build_post_url("投票します！\n#ミューコミＶＲ")
        self.assertIn("%E6%8A%95%E7%A5%A8%E3%81%97%E3%81%BE%E3%81%99%EF%BC%81", url)  # 投票します！
        self.assertIn("%0A", url)  # 改行
        self.assertIn("%23", url)  # #
        self.assertIn("%EF%BC%B6%EF%BC%B2", url)  # ＶＲ(全角)

    def test_post_url_デコードで元に戻る(self):
        text = build_text(TEMPLATE, "神曲すぎて泣いた", "2026/08/31")
        url = build_post_url(text)
        q = url.split("?text=", 1)[1]
        self.assertEqual(unquote(q), text)

    def test_post_url_ユーザー例と同形式(self):
        # ユーザーから提示された形式 (https://x.com/intent/post?text=...) と同形式になること
        text = (
            "(早乙女あずき)さんの『Elysium』に投票します！\n"
            "#ミューコミＶＲ\n"
            "#VTuber楽曲ランキング"
        )
        url = build_post_url(text)
        expected = (
            "https://x.com/intent/post?text="
            "(%E6%97%A9%E4%B9%99%E5%A5%B3%E3%81%82%E3%81%9A%E3%81%8D)"
            "%E3%81%95%E3%82%93%E3%81%AE%E3%80%8EElysium%E3%80%8F"
            "%E3%81%AB%E6%8A%95%E7%A5%A8%E3%81%97%E3%81%BE%E3%81%99%EF%BC%81%0A"
            "%23%E3%83%9F%E3%83%A5%E3%83%BC%E3%82%B3%E3%83%9F%EF%BC%B6%EF%BC%B2%0A"
            "%23VTuber%E6%A5%BD%E6%9B%B2%E3%83%A9%E3%83%B3%E3%82%AD%E3%83%B3%E3%82%B0"
        )
        self.assertEqual(url, expected)

    def test_dm_url_形式(self):
        text = build_text(TEMPLATE, "最高", "2026/08/31")
        url = build_dm_url(text, "100786821")
        self.assertTrue(url.startswith("https://x.com/messages/compose?"))
        self.assertIn("recipient_id=100786821", url)
        self.assertIn("text=", url)
        self.assertIn("%0A", url)

    def test_dm_url_デコードで元に戻る(self):
        text = build_text(TEMPLATE, "", "2026/08/31")
        url = build_dm_url(text, "100786821")
        params = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
        self.assertEqual(params["recipient_id"], "100786821")
        self.assertEqual(unquote(params["text"]), text)

    def test_dm_url_はconfigのdm_addressを使う(self):
        config = load_config("template.yaml")
        text = build_text(config["template"], "最高", "2026/08/31")
        url = build_dm_url(text, config["dm_address"])
        self.assertIn("recipient_id=100786821", url)
        self.assertIn("mc1242", config["dm_address_id"])


class DmButtonHtmlTest(unittest.TestCase):
    def test_構成(self):
        url = "https://x.com/messages/compose?recipient_id=100786821&text=abc"
        out = build_dm_button_html("✉️ DM送信", url, "コピーする本文")
        self.assertIn(
            'href="https://x.com/messages/compose?recipient_id=100786821&amp;text=abc"',
            out,
        )
        self.assertIn('target="_blank"', out)
        self.assertIn('rel="noopener noreferrer"', out)
        self.assertIn("✉️ DM送信", out)
        self.assertIn("コピーする本文", out)
        self.assertIn("navigator.clipboard", out)
        self.assertIn("execCommand('copy')", out)
        self.assertIn("✓ コピーしました", out)

    def test_scriptタグを壊さない(self):
        out = build_dm_button_html(
            "DM",
            "https://x.com/messages/compose?text=</script><b>x</b>",
            "</script><b>x</b>",
        )
        # コピー本文の </script> が \u003c に置換され、scriptブロックが壊れないこと
        self.assertEqual(out.count("<script>"), 1)  # 本来の開きタグのみ
        self.assertEqual(out.count("</script>"), 1)  # 本来の閉じタグのみ
        self.assertIn("\\u003c/script>", out)  # コピー本文側は \u003c に置換
        self.assertIn("&lt;/script&gt;", out)  # href側はHTMLエスケープ

    def test_クリックでURLが新タブで開く構成(self):
        out = build_dm_button_html("DM", "https://x.com/messages/compose?recipient_id=1", "text")
        self.assertIn("st-dm-link", out)
        self.assertIn("addEventListener('click'", out)


class DateTest(unittest.TestCase):
    def test_today_str_形式(self):
        value = today_str()
        self.assertRegex(value, r"^\d{4}/\d{2}/\d{2}$")


if __name__ == "__main__":
    unittest.main()
