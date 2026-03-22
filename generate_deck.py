#!/usr/bin/env python3
"""
generate_deck.py — Anki MCQ deck generator from JSON question files.

Usage:
    cd ~/proj/npopesku/anki-book-generator
    python3 generate_deck.py books/kubernetes-book/book.yaml \
            --questions books/kubernetes-book/questions/ch06-10.json

Output:
    output/<Book Title>/k8s_anki_ch06-10.apkg   (auto-named from chapter range)

See CLAUDE.md for how to add questions for new chapters or new books.
"""

import argparse
import json
import os
import pathlib
import sys
from collections import Counter, defaultdict

import yaml
import genanki

# ---------------------------------------------------------------------------
# Fixed model ID — stable across all decks so Anki reuses the card template
# instead of creating duplicates on re-import.
# ---------------------------------------------------------------------------
MODEL_ID = 1_800_000_001

# ---------------------------------------------------------------------------
# Card template (type-in-answer)
# ---------------------------------------------------------------------------

FRONT = """\
<div class="question">{{Question}}</div>
<div class="choices">
  <div class="choice"><b>A)</b> {{ChoiceA}}</div>
  <div class="choice"><b>B)</b> {{ChoiceB}}</div>
  <div class="choice"><b>C)</b> {{ChoiceC}}</div>
  <div class="choice"><b>D)</b> {{ChoiceD}}</div>
</div>
<p class="prompt">Type the correct letter (a / b / c / d):</p>
{{type:CorrectAnswer}}
"""

BACK = """\
{{FrontSide}}
<hr id="answer">
<div class="result">
  <p><b>Correct answer:</b> <span class="letter">{{CorrectAnswer}}</span></p>
  <div class="explanation">{{Explanation}}</div>
  <p class="chapter-tag">{{Chapter}}</p>
</div>
"""

CSS = """\
body { font-family: Arial, sans-serif; font-size: 16px; color: #222; }
.question { font-weight: bold; font-size: 1.15em; margin-bottom: 14px; }
.choices { background: #f5f5f5; border-left: 4px solid #4a90d9;
           padding: 10px 14px; border-radius: 4px; margin-bottom: 12px; }
.choice { margin: 6px 0; }
.prompt { color: #555; font-style: italic; margin-bottom: 6px; }
.result { background: #e8f5e9; padding: 12px; border-radius: 4px; margin-top: 8px; }
.letter { font-size: 1.25em; font-weight: bold; color: #2e7d32; text-transform: uppercase; }
.explanation { margin-top: 8px; line-height: 1.55; }
.chapter-tag { margin-top: 10px; font-size: 0.8em; color: #888; }
"""

MCQ_MODEL = genanki.Model(
    MODEL_ID,
    "Anki Book Generator MCQ (type-in)",
    fields=[
        {"name": "Question"},
        {"name": "ChoiceA"},
        {"name": "ChoiceB"},
        {"name": "ChoiceC"},
        {"name": "ChoiceD"},
        {"name": "CorrectAnswer"},
        {"name": "Explanation"},
        {"name": "Chapter"},
    ],
    templates=[{"name": "MCQ Card", "qfmt": FRONT, "afmt": BACK}],
    css=CSS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_yaml(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_questions(path: str) -> list[dict]:
    with open(path) as f:
        return json.load(f)


def chapter_title_map(book: dict) -> dict[int, str]:
    return {ch["num"]: ch["title"] for ch in book["chapters"]}


def stable_deck_id(name: str) -> int:
    """Deterministic deck ID from name so re-imports update rather than duplicate."""
    import hashlib
    h = hashlib.md5(name.encode()).hexdigest()
    return int(h[:8], 16) % (1 << 31)


def output_filename(questions: list[dict], book_title: str) -> str:
    """E.g. 'k8s_anki_ch06-10.apkg' derived from chapter numbers in the JSON."""
    slug = book_title.lower().replace(" ", "_").replace(":", "")
    chapters = sorted({q["chapter"] for q in questions})
    ch_range = f"ch{chapters[0]:02d}-{chapters[-1]:02d}"
    return f"{slug}_anki_{ch_range}.apkg"


def validate_balance(questions: list[dict]) -> None:
    """Warn if any chapter has a skewed answer distribution."""
    by_chapter: dict[int, list] = defaultdict(list)
    for q in questions:
        by_chapter[q["chapter"]].append(q["correct"].upper())

    ok = True
    for ch_num in sorted(by_chapter):
        counts = Counter(by_chapter[ch_num])
        total = sum(counts.values())
        for letter in "ABCD":
            pct = counts[letter] / total * 100
            if pct < 15 or pct > 35:
                print(f"  WARNING Ch{ch_num}: {letter}={counts[letter]}/{total} ({pct:.0f}%) — imbalanced")
                ok = False
    if ok:
        print("  Balance check passed.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Build an Anki .apkg from a questions JSON file.")
    parser.add_argument("book_yaml", help="Path to book.yaml (e.g. books/kubernetes-book/book.yaml)")
    parser.add_argument("--questions", required=True, help="Path to questions JSON file")
    parser.add_argument("--out-dir", help="Override output directory (default: output/<Book Title>/)")
    args = parser.parse_args()

    book = load_yaml(args.book_yaml)
    questions = load_questions(args.questions)
    ch_titles = chapter_title_map(book)
    book_title = book["title"]
    book_tags = book.get("tags", [])

    print(f"Book:      {book_title}")
    print(f"Questions: {len(questions)} loaded from {args.questions}")

    # Output directory
    book_yaml_dir = pathlib.Path(args.book_yaml).parent
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else (book_yaml_dir / "decks")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Derive deck name from chapter range
    chapters = sorted({q["chapter"] for q in questions})
    ch_range_label = f"Ch{chapters[0]:02d}\u2013{chapters[-1]:02d}"
    deck_name = f"{book['deck_prefix']} :: {ch_range_label}"
    deck_id = stable_deck_id(deck_name)
    deck = genanki.Deck(deck_id, deck_name)

    print(f"\nDeck:      {deck_name}")
    print(f"Chapters:  {chapters}")

    # Validate balance
    print("\nValidating answer balance...")
    validate_balance(questions)

    # Build notes
    by_chapter: dict[int, list] = defaultdict(list)
    for q in questions:
        by_chapter[q["chapter"]].append(q)

    print("\nChapter breakdown:")
    total_questions = 0
    for ch_num in sorted(by_chapter):
        qs = by_chapter[ch_num]
        counts = Counter(q["correct"].upper() for q in qs)
        title = ch_titles.get(ch_num, f"Chapter {ch_num}")
        print(f"  Ch{ch_num:02d} {title}: {len(qs)} questions  "
              f"A={counts['A']} B={counts['B']} C={counts['C']} D={counts['D']}")
        total_questions += len(qs)

        for q in qs:
            ch_label = f"Ch{ch_num:02d} \u2013 {title}"
            tags = book_tags + [f"ch{ch_num}"]
            note = genanki.Note(
                model=MCQ_MODEL,
                fields=[
                    q["question"],
                    q["choices"]["A"],
                    q["choices"]["B"],
                    q["choices"]["C"],
                    q["choices"]["D"],
                    q["correct"].lower(),
                    q["explanation"],
                    ch_label,
                ],
                tags=tags,
            )
            deck.add_note(note)

    # Overall distribution
    all_correct = [q["correct"].upper() for q in questions]
    counts = Counter(all_correct)
    print(f"\nOverall distribution ({total_questions} questions):")
    for letter in "ABCD":
        bar = "#" * counts[letter]
        pct = counts[letter] / total_questions * 100
        print(f"  {letter}: {counts[letter]:3d} ({pct:.0f}%)  {bar}")

    # Write .apkg
    filename = output_filename(questions, book_title)
    out_path = out_dir / filename
    genanki.Package(deck).write_to_file(str(out_path))
    print(f"\nSaved: {out_path}")
    print("Import in Anki: File \u2192 Import \u2192 select the .apkg file")
    print(f"Filter by chapter: Custom Study \u2192 Study by tag \u2192 select ch1, ch2, etc.")


if __name__ == "__main__":
    main()
