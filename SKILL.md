---
name: quizlet-import
description: Convert any quiz, question bank, exam dump, or flashcard source (messy .txt, .docx, .md, OCR'd PDF, pasted text — in any language) into a Quizlet-importable .txt using the custom separators $$$ (term/definition) and ### (between cards). Use this skill whenever the user mentions Quizlet, importing flashcards, converting questions into cards, turning an exam or question bank into study material, or asks for a file with $$$ and ### separators — even if they never say the word "Quizlet". The output format is byte-exact and easy to get subtly wrong; always follow this skill rather than improvising a format.
---

# Quizlet Import Builder

Turn a messy question bank into a `.txt` file the user can paste straight into
Quizlet's **Import** box.

Two things make this harder than it looks:

1. **The output format is byte-exact.** A single extra newline silently corrupts a
   card. Quizlet does not warn you — it imports the whitespace as content.
2. **The input is never as clean as it first appears.** Question banks are OCR'd,
   copy-pasted, and stitched together from several sources. The numbering style
   changes halfway through, option prefixes disappear, and ad banners sit in the
   middle of a question block.

Read this whole file before you start. The format contract comes first because it
is the part that gets broken most often.

---

## 1. The output format, exactly

A file with three cards **is exactly this**, byte for byte:

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

Look closely at what that means:

> **Card N's answer and card N+1's question share a line.**
> `D. opt4$$$B. opt2###Question text two` is one single line of the file.

### The mistake this skill exists to prevent

The file above looks cramped and malformed. Your instinct will be to tidy it — to
give `###` its own line, or to put a blank line between cards so the output is
readable. **That instinct is the bug.** It is an aesthetic reflex rather than a
reasoning error, which is exactly why knowing the rule is not enough to avoid it.

Quizlet treats every character between the separators as card content. A newline
added before `###` becomes a trailing blank line inside the previous card's
answer. A newline after `###` becomes a leading blank line on the next card's
question. The import "succeeds" and every card is subtly wrong.

So: when the output looks wrong to you, that is the signal you formatted it
**correctly**. Do not fix it. Do not pretty-print it. Do not add a trailing
newline at the end of the file.

### The rules stated formally

- A card is `FRONT` + `$$$` + `BACK`.
- Cards are joined by `###` with **zero characters** between them — no space, no
  newline, no tab, on either side.
- `FRONT` = the question stem, then a single newline, then the options, one per
  line.
- Option prefix is a capital letter, a period, and one space: `A. `, `B. `,
  `C. ` and so on, running consecutively from `A`.
- `BACK` = **letter and content together** (`B. opt2`) whenever the question has
  options. Never a bare letter (`B`), never bare content (`opt2`). The user is
  studying the mapping between the two, so both halves belong on the card.
- If a question has **no** options (a true/false statement, a fill-in-the-blank,
  a short-answer item), `BACK` is just the content, with **no** letter prefix.
  Do not invent an `A.` for an answer that never had options.
- The file starts with the first character of the first question and ends with
  the last character of the last answer. No leading whitespace, **no trailing
  newline**, no trailing `###`.
- No blank lines anywhere in the file.
- Encoding: **UTF-8 without BOM**, **LF line endings only**. See section 7.

---

## 2. Workflow

### Step 1 — Read the entire input file

Do not sample. Do not `grep`, `head`, or `tail` your way to an understanding of
the structure. Do not infer the format from the first five questions and assume
it holds.

This matters because question banks are almost never internally consistent. A
file that starts with `Q1.` will switch to `Câu 12:` at the page where someone
pasted in a second source. Options prefixed `a) b) c)` become bare lines with no
prefix at all. Correct answers are marked inline for the first forty questions
and then only in a key at the end. Extrapolate from the beginning and you will
silently mangle the rest.

For a large file, read it sequentially in chunks that cover **every** line, and
overlap each chunk with the previous one by about 10 lines so a question
straddling a boundary is neither lost nor double-counted.

Do not trust the source's own numbering as a question count. Numbers repeat, skip,
restart at 1 mid-file, and go missing. Count the blocks you actually see.

**Human-authored variation warning.** Assume the input was assembled or edited
by people. The same instruction may appear with different capitalization,
spacing, punctuation, accents, brackets, wording, line wrapping, or typographic
formatting; a marker may also be absent from text but present as bold, italic,
underline, or highlight. Hard-coded searches and regular expressions are useful
for finding candidates, but they are not authoritative. Always inspect the
candidate's surrounding question block, option structure, document formatting,
and answer evidence before classifying, moving, or deleting it. After automated
normalization, scan the complete output for variants the search pattern may have
missed.

### Step 2 — Inventory

Walk the file once and classify every line as one of: question stem, option,
answer marker, parenthetical, or junk. Keep a running count of question blocks.
You need that number for the report in Step 8, and committing to it up front is
what stops you from quietly dropping questions later.

### Step 3 — Normalize

Two separate operations that are easy to confuse:

**Strip question numbering.** `Q7.`, `Câu 12:`, `3)`, `15.`, `Question 4 -` at the
start of a stem all go away. Quizlet shuffles cards, so a question number is
noise at best and misleading at worst.

But a number *inside* the prose is content. `Điều 15 của Luật ... quy định` keeps
its 15. `In 1945, which country ...` keeps its 1945. The test is whether the
number identifies the question or is part of what the question asks.

**Blank lines in the input are structure, not content.** Most question banks put
a blank line between blocks. That blank line tells you where a question ends; it
does not survive into the output, which has no blank lines anywhere.

**Renumber option prefixes.** Whatever the source uses — `a) b) c) d)`,
`1. 2. 3. 4.`, `-`, a bullet, or nothing at all — the output is always
`A. B. C. D.` running consecutively from `A`.

When options have no prefix, you add one. When they have a prefix, you replace
it. Either way, if the source's answer marker refers to the *old* label you must
translate it: an input that says `Đáp án: c` over options `a) b) c) d)` produces a
back of `C. <text of the third option>`.

### Step 4 — Resolve parentheticals

Material in `( )` attached to a question is one of three things. See section 3.

### Step 5 — Find the correct answer

See section 4. If a question's answer appears nowhere in the file, **skip that
card** and record it in the report. Do not supply it from your own knowledge — a
card that looks authoritative and is wrong is worse than a card the user knows is
missing.

### Step 6 — Serialize

Build the file to the contract in section 1. Write UTF-8 without BOM, LF only
(section 7).

### Step 7 — Validate

Run `scripts/validate_quizlet.py <output.txt>`. If you cannot execute code, walk
the identical checklist in section 6 by hand. Do not hand the file to the user
until it passes.

### Step 8 — Report

Print the reconciliation report from section 8.

---

## 3. Parentheticals: `(...)` attached to a question

Question banks carry a lot of material in parentheses: an alternative phrasing of
the question, a hint, a note about how many answers to choose, a reference to a
textbook section. What you do with it depends on whether it is an alternative
question form, and whether it brings its own options.

**Case A — an alternative question form WITH its own options.**
Split it into its own separate card, placed immediately after the base card. It
is a genuinely different question with a different answer, so it deserves to be
drilled separately. Its options get the same `A. B. C. D.` normalization, and its
own marked answer becomes its back.

**Case B — an alternative question form WITHOUT its own options.**
Do **not** make a new card. Append the alternative wording to the back, in
parentheses, after the answer:

```
B. Python (Kiểu hỏi khác: Ngôn ngữ nào sau đây KHÔNG phải hợp ngữ?)
```

**Case C — selection instructions.** Material such as `(Chọn 2 đáp án)`,
`( Chọn 3 )`, `(2 đáp án)`, `(Lựa chọn các đáp án đúng)`, and
`(Câu hỏi lựa chọn nhiều đáp án)`
belongs on the **front**, on its own line immediately after the question stem
and before the option lines. It tells the learner how to attempt the question
and must be visible before the answer is revealed. Serialize it as:

```
Question stem
(Chọn 2 đáp án)
A. first option
B. second option
```

**Case D — anything else** (hints, notes, references, clarifications).
Append it to the back in parentheses, exactly like Case B.

The rule that unifies the ordinary parenthetical cases: alternative wording,
hints, references, and clarifications never appear inside an option. Selection
instructions are the explicit front-side exception because they change how the
learner should attempt the question. Other material that would help the user
answer after they have tried belongs on the back.

For a multi-line back (a multi-answer question, section 5), append the
parenthetical to the **last** answer line.

---

## 4. Finding the correct answer

Sources mark answers in many ways, sometimes several ways in one file:

- an explicit line: `Đáp án: B`, `ĐA: 3`, `Answer: C`, `Key: b`
- a letter alone on the line after the options
- the correct option's **text** repeated rather than its letter — map it back to a
  letter yourself
- typographic marking: bold, underline, highlight, colour, `*`, a check mark, an
  arrow
- the answer restated inside a parenthetical on the stem
- **a consolidated answer key elsewhere in the file** — usually a compact block or
  table near the end: `1.B  2.A  3.D  4.C ...`, sometimes several such blocks
  covering different ranges

That last one is the case most often missed. If a question block has no inline
answer, do not conclude the answer is absent until you have checked the whole
file for a key. This is another reason Step 1 forbids sampling: the key is
usually the last thing in the file, and the questions that depend on it are at
the start.

When a key exists, match by the source's original question number — but watch for
numbering that restarts mid-file. If an inline marker and the key disagree, prefer
the inline marker and flag the disagreement in the report.

If after all of that a question has no answer anywhere: skip the card and list it
in the report with its source position.

---

## 5. Question types other than single-answer multiple choice

**Multiple correct answers.** Put each selected option on its own line in the
back, in letter order:

```
Những thành phần nào sau đây thuộc phần cứng máy tính? (Chọn 2 đáp án)
A. CPU
B. Hệ điều hành
C. RAM
D. Trình biên dịch$$$A. CPU
C. RAM
```

Note that the last back line is followed immediately by `###`, or by the end of
the file. A multi-line back is the single place you will most want to add a
newline before `###`. Don't.

**True/false, yes/no.** If the source lists the choices as a two-item list, treat
them as options and letter them (`A. Đúng` / `B. Sai`). If the source is a bare
statement with the verdict given separately, there are no options: the front is
the statement, and the back is `Đúng` with no letter.

**Fill-in-the-blank and short answer.** Front is the prompt with its blank intact;
back is the answer text, no letter.

Further cases — matching questions, items with images or tables, duplicated
questions, sub-questions, questions whose options contain their own parentheses —
are covered in `references/edge-cases.md`. Read it when you hit something this
file does not cover.

---

## 6. Validation checklist

Run `scripts/validate_quizlet.py <file>` if you can execute code. If you cannot,
check these by hand, in this order. They are the same checks in the same order, so
the two paths are interchangeable.

1. File decodes as UTF-8, has no byte-order mark (U+FEFF), and contains no
   carriage return anywhere.
2. The file contains no newline immediately before `###` and none immediately
   after it, and no space or tab adjacent to any `###`. Check the last line of
   every multi-line back specifically.
3. Splitting on `###` yields the expected number of cards, and none is empty.
4. Every card contains exactly one `$$$`.
5. No front or back has leading or trailing whitespace, and the file has no blank
   lines.
6. The file does not begin with whitespace and does not end with a newline or
   with `###`.
7. No front begins with leftover question numbering (`Q7.`, `Câu 12:`, `3)`).
8. Option lines match `A. `, `B. `, `C. ` — capital, period, single space —
   running consecutively from `A`, at least two of them wherever any exist, and
   contiguous at the end of the front. No line still carries an unnormalized
   prefix (`a)`, `b.`, `1.`, `2)`) or a bullet.
9. When a front has options, **every line** of the back is `<letter>. <exact text
   of that option>`, optionally followed by ` (annotation)`. Not a bare letter,
   not bare content, and the text must match the option it names. A multi-answer
   back runs in letter order, unless it is an ordering question, where answer
   order is the point.
10. When a front has no options, the back does not start with a bare letter
    prefix.
11. No two cards have identical fronts. A duplicate is usually a parsing error —
    check it rather than assuming the source repeated itself.
12. Selection instructions such as `(Chọn 2 đáp án)`, `( 2 đáp án)`, and
    `(Lựa chọn 3 đáp án)`
    appear in the question/term portion on their own line immediately after the
    stem, not appended to the stem and not in the definition/back. Do not move
    answer-specific notes such as `(Nếu không có A chọn C)` to the front.

---

## 7. Encoding and line endings

Quiz banks are frequently in languages with diacritics, and encoding damage there
is silent and ugly: `Đáp án` becomes `Ä‘Ã¡p Ã¡n`, and the user often does not
notice until the cards are already in Quizlet.

- Write **UTF-8 without BOM**. A BOM becomes an invisible character at the start
  of the very first term.
- Write **LF only**. A carriage return lands inside every card's front and
  imports as a stray character.

On Windows this needs care: PowerShell's `Out-File` and `Set-Content` default to
CRLF and frequently add a BOM. Prefer writing from Python
(`open(path, "w", encoding="utf-8", newline="")`) or another method you have
verified. The validator checks both, so if you are unsure, write the file and run
the validator.

---

## 8. The reconciliation report

After writing the file, report to the user:

```
Source: 47 question blocks found
Emitted: 46 cards  (47 base - 3 skipped + 2 split from alternate-form parentheticals)
Skipped: 3 - no correct answer found in source (source items 12, 29, 41)
Junk removed: 6 lines - page footer x4, ad phone number x2
Flagged: 1 - ambiguous parenthetical at source item 33
```

The numbers have to reconcile arithmetically. This is not bureaucracy: it is the
only thing that makes "I read the whole file" checkable by the user. Without it, a
run that quietly processed the first 20 questions of a 47-question file looks
exactly like a run that did the job.

Also tell the user the output path and the two separators to paste into Quizlet.

---

## 9. Removing junk

Question banks arrive wrapped in material that belongs to no question: page
headers and footers, watermarks, tutoring-centre ads, phone numbers, Zalo and
Facebook handles, `Trang 3/12`, `Downloaded by ...`, horizontal rules, bare page
numbers, and closing encouragement like "Chúc các bạn thi tốt".

**Identify junk by position and repetition, never by content type alone:**

- it repeats through the file at regular intervals (a header or footer), or
- it sits outside any question block.

The asymmetry that matters: *a phone number in a footer is junk; a phone number
that is an answer option is content.* The same string is one or the other
depending only on where it sits. So never apply a rule like "remove phone
numbers" — look at where the line is.

**When you are unsure, keep the line and flag it in the report.** The costs are
not symmetric. A spurious card takes one click to delete and the user sees it
immediately. A silently dropped question is nearly undetectable — they find out
during an exam.

---

## 10. Output file and Quizlet settings

Write to `<input-basename>-quizlet.txt` next to the input file, unless the user
asks for something else.

Tell the user how to import:

1. Quizlet, then **Create**, then **Import**
2. Paste the file contents
3. **Between term and definition**: choose *Custom* and enter `$$$`
4. **Between cards**: choose *Custom* and enter `###`
5. Check that the preview card count matches the report, then import

---

## 11. Worked example

`examples/messy-input.txt`, `examples/expected-output.txt` and
`examples/expected-report.txt` are a matched set: the input, the exact file it
should produce, and the reconciliation report that should accompany it.
The input deliberately exercises every rule in this file at once: mixed numbering
styles, three different option-prefix conventions plus unprefixed options, all
three parenthetical cases, a true/false item with no options, a multi-answer
question, an answer key at the end of the file, embedded ads and page furniture,
and one question with no answer at all.

If any part of this skill is ambiguous to you, read that pair. It is the ground
truth for what correct output looks like.
