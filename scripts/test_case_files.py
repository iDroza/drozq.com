"""Regression tests for the three rendered client case files."""

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
CASES = (
    "testimonials/001-long-beach-firefighter/index.html",
    "testimonials/002-corona-analyst/index.html",
    "testimonials/003-riverside-first-home/index.html",
)
INDEX = "testimonials/index.html"


class CaseParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.images: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"])
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"])
        if tag == "img":
            self.images.append(values)


def local_target(href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        return None
    if parsed.path.startswith(("/api/", "/cdn-cgi/")):
        return None
    if parsed.path == "/":
        return ROOT / "index.html"
    target = ROOT / parsed.path.lstrip("/")
    return target / "index.html" if parsed.path.endswith("/") else target


class CaseFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pages = {name: (ROOT / name).read_text(encoding="utf-8") for name in CASES}

    def test_case_file_index_contract(self) -> None:
        html = (ROOT / INDEX).read_text(encoding="utf-8")
        self.assertIn('data-count-target="58250" data-count-prefix="$"', html)
        self.assertIn('data-count-target="1790000" data-count-prefix="$"', html)
        self.assertEqual(html.count('href="/testimonials/003-riverside-first-home/"'), 1)
        self.assertIn('id="drozq-page-chrome"', html)
        self.assertIn('id="drozq-xref-css"', html)
        self.assertNotIn("drozq-hero-rotate", html)
        self.assertNotIn("Homepage market-trends widget", html)
        self.assertNotIn('"@type":"FAQPage"', html)

    def test_anonymized_client_name_stays_off_public_pages(self) -> None:
        blocked_identity = "Rich" + "ard"
        public_files = list(ROOT.rglob("*.html")) + [ROOT / "llms.txt"]
        for path in public_files:
            if any(part in {".git", ".codex", "node_modules"} for part in path.parts):
                continue
            with self.subTest(page=path.relative_to(ROOT)):
                self.assertNotIn(blocked_identity.lower(), path.read_text(encoding="utf-8").lower())

    def test_shared_case_file_contract(self) -> None:
        for name, html in self.pages.items():
            with self.subTest(page=name):
                self.assertIn('<section class="cf-hero">', html)
                self.assertIn('class="cf-hero-stat__number" data-count-target="', html)
                self.assertIn('id="drozq-page-chrome"', html)
                self.assertIn('id="drozq-xref-css"', html)
                self.assertIn('id="cf-scroll-js"', html)
                self.assertIn('aria-labelledby="tab-buy"', html)
                self.assertNotIn("drozq-hero-rotate", html)
                self.assertNotIn("Homepage market-trends widget", html)
                self.assertNotRegex(html, r'class="[^"]*\brw-')
                for marker in (
                    "DROZQ_FUNNEL_HTML_BEGIN",
                    "DROZQ_FUNNEL_HTML_END",
                    "DROZQ_FUNNEL_JS_BEGIN",
                    "DROZQ_FUNNEL_JS_END",
                ):
                    self.assertEqual(html.count(marker), 1)

    def test_markup_ids_and_internal_links(self) -> None:
        for name, html in self.pages.items():
            parser = CaseParser()
            parser.feed(html)
            with self.subTest(page=name):
                self.assertEqual(len(parser.ids), len(set(parser.ids)))
                missing = [href for href in parser.hrefs if (target := local_target(href)) and not target.exists()]
                self.assertEqual(missing, [])

    def test_riverside_story_and_photo_contract(self) -> None:
        html = self.pages[CASES[2]]
        self.assertIn('data-count-target="15000" data-count-prefix="$"', html)
        self.assertIn("$15,000", html)
        self.assertIn("22 years", html)
        self.assertIn("only home in his search with a pool", html)
        self.assertIn("Ralphs Truck Driver", html)
        self.assertIn("Case File 003 &middot; Riverside &middot; Truck Driver", html)
        self.assertIn("Escrow closed early", html)
        self.assertIn('<meta property="og:image" content="https://drozq.com/media/images/euclid/pool-day.webp">', html)
        self.assertIn('<meta name="twitter:image" content="https://drozq.com/media/images/euclid/pool-day.webp">', html)
        self.assertNotIn("\u2014", html)

        hero = re.search(r'<section class="cf-hero">(.*?)</section>', html, re.DOTALL)
        self.assertIsNotNone(hero)
        self.assertNotIn("<img", hero.group(1))

        first_gallery = re.search(r'<div class="cf-photo-grid cf-photo-grid--feature".*?</div>', html, re.DOTALL)
        self.assertIsNotNone(first_gallery)
        self.assertIn('/media/images/euclid/pool-day.webp', first_gallery.group(0))
        self.assertLess(
            first_gallery.group(0).index('/media/images/euclid/pool-day.webp'),
            first_gallery.group(0).index('/media/images/euclid/front-day.jpg'),
        )
        self.assertIn("max-width: 1000px", html)

        parser = CaseParser()
        parser.feed(html)
        euclid_images = [image for image in parser.images if image.get("src", "").startswith("/media/images/euclid/")]
        self.assertEqual(len(euclid_images), 6)
        for image in euclid_images:
            self.assertEqual(image.get("width"), "1024")
            self.assertTrue((ROOT / image["src"].lstrip("/")).exists())

    def test_riverside_structured_data(self) -> None:
        html = self.pages[CASES[2]]
        schemas = [
            json.loads(payload)
            for payload in re.findall(
                r'<script type="application/ld\+json">(.*?)</script>',
                html,
                re.DOTALL,
            )
        ]
        schema_types = {schema.get("@type") for schema in schemas}
        self.assertIn("Article", schema_types)
        self.assertIn("BreadcrumbList", schema_types)
        self.assertNotIn("FAQPage", schema_types)


if __name__ == "__main__":
    unittest.main()
