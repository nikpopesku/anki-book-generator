# CLAUDE.md — Anki Book Generator

This project generates Anki MCQ flashcard decks (`.apkg`) from JSON question files.
Cards use Anki's **type-in-answer** feature: the user types A/B/C/D and gets
instant green/red feedback.

---

## Quick commands

```bash
cd ~/proj/npopesku/anki-book-generator

# Generate a deck from a questions file
python3 generate_deck.py books/kubernetes-book/book.yaml \
        --questions books/kubernetes-book/questions/ch06-10.json

# Output lands in:  output/<Book Title>/<slug>_anki_chXX-XX.apkg
```

---

## Adding questions for new chapters (most common task)

**Steps:**
1. Read the PDF pages for each new chapter (see PDF access below)
2. Generate questions following the JSON format (see below) — 12 per chapter, 3A 3B 3C 3D
3. Save to `books/<book-slug>/questions/chXX-XX.json`
4. Run `generate_deck.py` to build the `.apkg`
5. Commit the new JSON file to git (`.apkg` is gitignored)

---

## PDF access — IMPORTANT

The Kubernetes Book PDF has an apostrophe in its filename which breaks plain string paths.
**Always use `pathlib` to locate the file:**

```python
import pathlib, subprocess

pdf_dir = pathlib.Path("/home/niku/Yandex.Disk/Books/!Programming/K8s/")
pdf = next(pdf_dir.glob("The Kubernetes Book*"))   # finds the file safely
# pdf is now a Path object — pass str(pdf) to pdftotext

result = subprocess.run(
    ["pdftotext", "-f", str(start_page), "-l", str(end_page), str(pdf), "-"],
    capture_output=True, text=True
)
text = result.stdout
```

Chapter page ranges are in `books/kubernetes-book/book.yaml`.

---

## Question JSON format

File: `books/<slug>/questions/chXX-XX.json`

```json
[
  {
    "chapter": 6,
    "chapter_title": "Kubernetes Deployments",
    "question": "What resource sits below a Deployment and handles self-healing?",
    "choices": {
      "A": "StatefulSet",
      "B": "ReplicaSet",
      "C": "DaemonSet",
      "D": "ConfigMap"
    },
    "correct": "B",
    "explanation": "A Deployment manages a ReplicaSet which runs a reconciliation loop to maintain the correct Pod count."
  }
]
```

**Balance rule (enforced by the script):** Each chapter must have exactly **3 questions
with each correct answer letter** (3A + 3B + 3C + 3D = 12 per chapter).
The script warns if any chapter deviates beyond 15–35% per letter.

---

## book.yaml format

```yaml
title: "The Kubernetes Book"       # used in deck name and output folder
deck_prefix: "The Kubernetes Book" # prefix for the Anki deck name
pdf_path: "/path/to/pdf/folder/"   # directory containing the PDF
pdf_glob: "The Kubernetes Book*"   # glob pattern to find the PDF file
tags: ["k8s"]                      # global tags added to every card
chapters:
  - {num: 1,  title: "Kubernetes Primer",   pages: "5-12"}
  - {num: 2,  title: "...",                 pages: "13-30"}
```

---

## Adding a new book

1. Create `books/<new-slug>/book.yaml` with the book's metadata and chapter list
2. Create `books/<new-slug>/questions/chXX-XX.json` with the first batch of questions
3. Run `python3 generate_deck.py books/<new-slug>/book.yaml --questions ...`

---

## Project structure

```
anki-book-generator/
├── generate_deck.py          # generic CLI — works for any book
├── requirements.txt          # pip install -r requirements.txt
├── CLAUDE.md                 # this file
├── README.md
├── .gitignore                # output/ is ignored
├── books/
│   └── kubernetes-book/
│       ├── book.yaml
│       └── questions/
│           ├── ch01-05.json
│           ├── ch06-10.json
│           └── chXX-XX.json  # add new batches here
└── output/                   # gitignored
    └── The Kubernetes Book/
        └── *.apkg
```

---

## Anki import & chapter filtering

- **Import:** Anki → File → Import → select `.apkg`
- **Study one chapter:** Custom Study → Study by tag → pick `ch6` (or any chapter tag)
- **Study a range:** pick multiple tags in Custom Study

Tags on every card: global book tags (e.g. `k8s`) + `ch<N>` (e.g. `ch6`).
