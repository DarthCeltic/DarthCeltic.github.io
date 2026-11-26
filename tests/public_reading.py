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
        root = Path(__file__).resolve().parents[1] / "mathcase"
        technical_label = re.compile(r"\b[0-9a-f]{64}\b|\bM31[ -]step[ -]34\b|\bM0 packet SHA", re.I)
        for name in ("work.html", "collatz.html", "frontier.html", "roadmap.html"):
            with self.subTest(page=name):
                view = ReadingView()
                view.feed((root / name).read_text(encoding="utf-8"))
                self.assertTrue(view.text, "Expected a visible article")
                self.assertNotRegex(" ".join(view.text), technical_label)

    def test_research_cards_explain_the_860_families_and_current_ramsey_replay(self):
        root = Path(__file__).resolve().parents[1] / "mathcase"
        cases = (root / "cases.html").read_text(encoding="utf-8")
        diagnostics = (root / "diagnostics.html").read_text(encoding="utf-8")

        m31 = re.search(
            r'<article class="case-card-page" id="collatz-m31-lift">(.*?)</article>',
            cases,
            re.S,
        )
        self.assertIsNotNone(m31)
        self.assertIn("860 selected groups of Collatz starting numbers", m31.group(1))
        self.assertIn("Each group contains infinitely many starts", m31.group(1))
        self.assertIn("does not run Lean", m31.group(1))
        self.assertIn("not a proof that every Collatz sequence reaches 1", m31.group(1))
        self.assertIn("860 selected groups of Collatz starting numbers", diagnostics)

        r66 = re.search(
            r'<article class="case-card-page" id="ramsey66">(.*?)</article>',
            cases,
            re.S,
        )
        self.assertIsNotNone(r66)
        self.assertIn("fresh MathCase output folder", r66.group(1))
        self.assertIn("Read what Lean checked and how to rebuild it", r66.group(1))
        self.assertIn("Browse the replay files and earlier run history", r66.group(1))
        self.assertNotRegex(r66.group(1), r'href="[^"]+\.json')
        self.assertIn("A stranger has not yet independently rebuilt it", r66.group(1))
        self.assertIn("independent mathematical review remains open", r66.group(1))
        self.assertNotIn("fresh replay remains open", r66.group(1))

        frontier = (root / "frontier.html").read_text(encoding="utf-8")
        self.assertIn("a stranger has not yet reproduced the run", frontier)
        self.assertNotIn("pinned image is not verified as anonymously pullable", frontier)
        self.assertIn("Browse the replay files and earlier run history", frontier)

    def test_collatz_twelve_of_twenty_density_is_plain_and_bounded(self):
        root = Path(__file__).resolve().parents[1] / "mathcase"
        collatz = (root / "collatz.html").read_text(encoding="utf-8")
        self.assertIn("natural density exactly 62,985/524,288", collatz)
        self.assertIn("about 12.0134%", collatz)
        self.assertIn("other starts may also be", collatz)
        self.assertIn("proves no global convergence", collatz)


if __name__ == "__main__":
    unittest.main()
