"""Check the default reading view of the public results and research pages."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


class ReadingView(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.details = []
        self.in_summary = False
        self.in_script = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.in_main = True
        elif tag == "details":
            self.details.append("open" in dict(attrs))
        elif tag == "summary":
            self.in_summary = True
        elif tag in ("script", "style"):
            self.in_script = True

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False
        elif tag == "details":
            self.details.pop()
        elif tag == "summary":
            self.in_summary = False
        elif tag in ("script", "style"):
            self.in_script = False

    def handle_data(self, data):
        if not self.in_main or self.in_script:
            return
        ancestors = self.details[:-1] if self.in_summary else self.details
        if all(ancestors):
            self.text.append(data)


class PublicReadingTests(unittest.TestCase):
    def test_research_identifiers_stay_in_the_evidence(self):
        root = Path(__file__).resolve().parents[1]
        technical_label = re.compile(r"\b[0-9a-f]{64}\b|\bM31[ -]step[ -]34\b|\bM0 packet SHA", re.I)
        for name in ("work.html", "collatz.html", "frontier.html", "roadmap.html"):
            with self.subTest(page=name):
                view = ReadingView()
                view.feed((root / name).read_text(encoding="utf-8"))
                self.assertTrue(view.text, "Expected a visible article")
                self.assertNotRegex(" ".join(view.text), technical_label)


if __name__ == "__main__":
    unittest.main()
