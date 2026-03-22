# Anki Book Generator

Generates Anki flashcard decks (`.apkg`) from technical books using multiple-choice
questions with **type-in-answer** cards — type A/B/C/D and get instant feedback.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 generate_deck.py books/kubernetes-book/book.yaml \
        --questions books/kubernetes-book/questions/ch06-10.json
```

Output: `books/<book-slug>/decks/<book>_anki_chXX-XX.apkg`

Import into Anki: **File → Import → select the `.apkg` file**

## Study by chapter

Each card is tagged with `ch1`, `ch2`, etc.
In Anki: **Custom Study → Study by tag** → pick the chapter(s) you want.

## Question format

12 questions per chapter, perfectly balanced: 3 correct answers per letter (A/B/C/D).
Questions are stored as JSON in `books/<book>/questions/`.

## Books

| Book | Chapters covered |
|------|-----------------|
| The Kubernetes Book (Nigel Poulton, 2025) | 1–10 |
