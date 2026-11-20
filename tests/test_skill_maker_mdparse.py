"""Unit tests of skill-maker/scripts/mdparse.py."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skill-maker", "scripts"))

import mdparse  # noqa: E402

README = """---
summary: >-
  Draws a diagram
  as one page.
other: "quoted"
---

# erd

<!-- generated -->
Draws a diagram
from a description.

Second paragraph.

## Why

Text with a [link](references/a.md#part) and [site](https://example.com).

## Use cases

### From SQL

```markdown
## Not a heading
### Neither
[ghost](missing.md)
```

~~~~
## Still fenced
```
## Fenced too
~~~~

### From an ORM ###

## Usage
"""


class FrontmatterTest(unittest.TestCase):
    def test_folded_and_quoted_values(self):
        data, body, first = mdparse.split_frontmatter(README)
        self.assertEqual(data["summary"], "Draws a diagram as one page.")
        self.assertEqual(data["other"], "quoted")
        self.assertEqual(first, 7)
        self.assertEqual(body[1], "# erd")

    def test_no_frontmatter(self):
        data, body, first = mdparse.split_frontmatter("# title\n")
        self.assertIsNone(data)
        self.assertEqual((body, first), (["# title"], 1))

    def test_unclosed_frontmatter_is_not_frontmatter(self):
        data, _, first = mdparse.split_frontmatter("---\nsummary: x\n# title\n")
        self.assertIsNone(data)
        self.assertEqual(first, 1)

    def test_literal_block_keeps_lines(self):
        data, _, _ = mdparse.split_frontmatter("---\ntext: |\n  one\n  two\n---\n")
        self.assertEqual(data["text"], "one\ntwo")


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.doc = mdparse.parse(README)

    def test_headings_skip_fenced_blocks(self):
        titles = [(h["level"], h["title"]) for h in self.doc["headings"]]
        self.assertEqual(titles, [
            (1, "erd"), (2, "Why"), (2, "Use cases"), (3, "From SQL"),
            (3, "From an ORM"), (2, "Usage"),
        ])

    def test_line_numbers_count_the_frontmatter(self):
        lines = README.splitlines()
        expected = [lines.index(text) + 1 for text in
                    ("# erd", "## Why", "## Use cases", "### From SQL", "### From an ORM ###", "## Usage")]
        self.assertEqual([head["line"] for head in self.doc["headings"]], expected)
        self.assertEqual(expected[0], 8)

    def test_bom_and_crlf(self):
        doc = mdparse.parse("\ufeff---\r\nsummary: x\r\n---\r\n# t\r\n\r\nIntro.\r\n\r\n## Why\r\n")
        self.assertEqual(doc["frontmatter"], {"summary": "x"})
        self.assertEqual((doc["intro"], doc["sections"][0]["title"]), ("Intro.", "Why"))

    def test_html_comments_hide_headings_and_are_not_the_intro(self):
        doc = mdparse.parse("# t\n\n<!--\nnote\n## Why\n-->\n\n<!-- marker -->\nReal intro.\n\n## Usage\n")
        self.assertEqual([s["title"] for s in doc["sections"]], ["Usage"])
        self.assertEqual(doc["intro"], "Real intro.")

    def test_link_forms(self):
        text = ("Use `[a](code.md)` here.\n[![badge](img.svg)](skills/x/README.md)\n"
                "[a](b.md 'Title') and [c](<d e.md>)\n[ref]: refs/e.md\n")
        targets = [link["target"] for link in mdparse.parse(text)["links"]]
        self.assertEqual(targets, ["img.svg", "skills/x/README.md", "b.md", "d e.md", "refs/e.md"])

    def test_intro_is_the_first_paragraph_after_h1(self):
        self.assertEqual(self.doc["intro"], "Draws a diagram from a description.")

    def test_sections_carry_their_h3(self):
        sections = {s["title"]: s for s in self.doc["sections"]}
        self.assertEqual([h["title"] for h in sections["Use cases"]["h3"]], ["From SQL", "From an ORM"])
        self.assertEqual(sections["Why"]["h3"], [])
        self.assertEqual(sections["Why"]["end"], sections["Use cases"]["line"])

    def test_links_skip_fenced_blocks(self):
        targets = [link["target"] for link in self.doc["links"]]
        self.assertEqual(targets, ["references/a.md#part", "https://example.com"])

    def test_intro_empty_when_a_heading_follows_h1(self):
        self.assertEqual(mdparse.parse("# t\n\n## Why\n\ntext\n")["intro"], "")

    def test_hash_without_space_is_not_a_heading(self):
        self.assertEqual(mdparse.parse("#tag\n\n#  spaced  \n")["headings"][0]["title"], "spaced")


if __name__ == "__main__":
    unittest.main()
