"""draft_generator の単体テスト。

実行方法: python -m unittest test_draft_generator
"""

import unittest
from urllib.parse import unquote

from draft_generator import build_dm_url, build_post_url, build_text, today_str

TEMPLATE = (
    "(早乙女あずき)さんの『Elysium』に投票します！\n"
    "ここ感想 YYYY/MM/DD\n"
    "#ミューコミＶＲ #VTuber楽曲ランキング\n"
    "https://www.youtube.com/watch?v=01Mpk-w688s"
)


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


class DateTest(unittest.TestCase):
    def test_today_str_形式(self):
        value = today_str()
        self.assertRegex(value, r"^\d{4}/\d{2}/\d{2}$")


if __name__ == "__main__":
    unittest.main()
