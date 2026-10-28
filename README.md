# quizlet-import

An AI-agent skill for turning a messy quiz, exam dump, or question bank into a
`.txt` file that imports cleanly into [Quizlet](https://quizlet.com).

You point an agent at a question file — a Word export, an OCR'd PDF, a wall of
pasted text — and it gives you back a file you paste into Quizlet's Import box.
The skill handles the parts that go wrong in practice: inconsistent numbering,
option prefixes that change style (or vanish) halfway through, answers hidden in
a key at the end of the file, advertising and page furniture mixed into the
questions, and above all the byte-exact output format.

Works with any agent that can read a file: Claude Code, Claude.ai, Cursor,
Codex, Gemini CLI, GitHub Copilot, or a chat window you paste into.

---

## The output format

Quizlet's importer takes custom separators. This skill uses:

| Between | Separator |
| --- | --- |
| Question (term) and answer (definition) | `$$$` |
| One card and the next | `###` |

A file with three cards is **exactly** this, byte for byte:

```
Question text one
A. opt1
B. opt2
C. opt3
D. opt4$$$B. opt2###Question text two
A. opt1
B. opt2$$$A. opt1###Question text three
A. yes
B. no$$$B. no
```

Card N's answer and card N+1's question share a line. Nothing sits on either
side of `###` — no space, no newline. The file looks cramped and malformed, and
that is what correct output looks like.

This is the whole reason the skill exists. Agents know the rule and break it
anyway, because a line reading `D. opt4$$$B. opt2###Question text two` looks
broken and the reflex is to tidy it. Any whitespace added next to `###` is
imported by Quizlet as literal content inside a card, so the import "succeeds"
and every card is quietly wrong.

Other rules the skill enforces:

- answers show **letter and content** (`B. opt2`), never a bare `B` and never
  bare content
- question numbers (`Q1.`, `Câu 12:`) are stripped; a number inside the prose
  (`Điều 15 quy định...`) is kept
- option prefixes are normalized to `A. B. C. D.` whatever the source used —
  including sources with no prefixes at all
- parenthetical selection instructions such as `(Chọn 2 đáp án)` appear on
  their own line after the question stem and before the options; alternative
  question forms with their own options become separate cards, and other
  parenthetical material goes into the back
- questions with no answer anywhere in the source are skipped and reported,
  never answered by guesswork
- output is UTF-8 without BOM, LF only, no trailing newline

---

## Importing into Quizlet

1. Quizlet → **Create** → **Import**
2. Paste the file contents
3. **Between term and definition** → *Custom* → `$$$`
4. **Between cards** → *Custom* → `###`
5. Check the preview card count against the agent's report, then import

---

## Install

Clone the repo, then wire it into whichever agent you use.

```bash
git clone https://github.com/FinDaHuman/quizlet-import-skill.git
```

**Claude Code / Claude.ai / Cowork** — copy the folder into your skills
directory:

```bash
cp -r quizlet-import-skill ~/.claude/skills/quizlet-import
```

Per-project instead: `.claude/skills/quizlet-import/`. The skill triggers on its
own when you mention Quizlet or flashcard import.

**Cursor** — copy the rule into your project and keep the repo reachable:

```bash
cp quizlet-import-skill/adapters/cursor.mdc .cursor/rules/quizlet-import.mdc
```

**Codex CLI, Gemini CLI, and other agents that read `AGENTS.md`** — keep the
repo in (or beside) the project. `AGENTS.md` at the repo root points at
`SKILL.md`.

**GitHub Copilot** —

```bash
cp quizlet-import-skill/adapters/copilot-instructions.md .github/copilot-instructions.md
```

**Any chat agent (ChatGPT, Gemini, Claude web)** — paste the contents of
`SKILL.md` into the conversation, attach your question file, and ask for the
Quizlet import file.

---

## Usage

Once installed, ask for it in plain language:

> Convert `de-cuong-cntt.docx` into a Quizlet import file.

The agent reads the whole source, builds the file next to the input as
`<name>-quizlet.txt`, validates it, and reports what it did:

```
Source: 47 question blocks found
Emitted: 46 cards  (47 base - 3 skipped + 2 split from alternate-form parentheticals)
Skipped: 3 - no correct answer found in source (source items 12, 29, 41)
Junk removed: 6 lines - page footer x4, ad phone number x2
Flagged: 1 - ambiguous parenthetical at source item 33
```

The report is required, and the numbers have to reconcile. It is the only way to
tell a run that read all 47 questions from a run that quietly processed the
first 20.

---

## Validating a file

```bash
python scripts/validate_quizlet.py my-cards-quizlet.txt
```

Exit code 0 means the file is safe to import. Failures name the check and the
card:

```
FAIL  my-cards-quizlet.txt  (12 cards parsed)
  error    check 2 : a newline immediately before ### (occurs 11 time(s)); cards
                     must be joined by ### with nothing between them
  error    check 9  (card 4): back line is not '<letter>. <option text>': 'B'
```

No dependencies beyond Python 3.7+. The twelve checks it runs are also written
out as a prose checklist in `SKILL.md` section 6, in the same order, so an agent
that cannot execute code gets the same result by hand.

---

## Repo layout

```
SKILL.md                    the skill itself - the only source of truth
AGENTS.md                   pointer for agents that auto-load AGENTS.md
adapters/                   Cursor and Copilot rule templates
references/edge-cases.md    messy-input catalogue, read on demand
scripts/validate_quizlet.py format validator
examples/                   a deliberately messy input, its exact expected
                            output, and the report that should accompany it
tests/                      broken files, each failing one specific check
```

`examples/messy-input.txt`, `examples/expected-output.txt` and
`examples/expected-report.txt` are a matched set that exercises every rule at
once — mixed numbering, three option-prefix conventions plus unprefixed options,
all three parenthetical cases, a true/false
item with no options, a multi-answer question, an end-of-file answer key,
embedded ads, and one question with no answer at all. They are the ground truth
for what correct output looks like.

Verify the repo itself:

```bash
python scripts/validate_quizlet.py examples/expected-output.txt   # exit 0
python scripts/validate_quizlet.py tests/bad-*.txt                # exit 1, each with its own check
```

---

## Contributing

The useful contribution is a **failing input**: a real question file whose shape
the skill mishandles. Add it to `examples/` or `tests/` with the output it should
have produced, and the fix follows from there.

## License

MIT. See [LICENSE](LICENSE).
