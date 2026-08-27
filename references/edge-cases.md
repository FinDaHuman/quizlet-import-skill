# Edge cases

Read this when the input contains something `SKILL.md` does not cover. Each
entry states the situation, the decision, and why.

## Contents

- [Junk catalogue](#junk-catalogue)
- [Question types](#question-types)
- [Options that fight the format](#options-that-fight-the-format)
- [Answer-key problems](#answer-key-problems)
- [Structural problems](#structural-problems)
- [Content you must not change](#content-you-must-not-change)

---

## Junk catalogue

The rule from `SKILL.md` section 9 is that junk is identified by **position and
repetition**, never by content type. This list is what that rule usually catches,
not a list of strings to delete on sight.

**Page furniture** — repeats at regular intervals through the file:

- `Trang 3/12`, `Page 3 of 12`, a bare number alone on a line
- document titles and subject headers reprinted on every page
- `-----`, `=====`, `___`, and other horizontal rules
- running headers naming the school, faculty, or subject
- exam-paper furniture: `Mã đề 132`, `Thời gian làm bài: 60 phút`, `(Không kể
  thời gian phát đề)`, `Họ và tên thí sinh: ....`

**Advertising and provenance** — sits outside any question block:

- tutoring-centre and course names, usually in capitals with a phone number
- `Hotline:`, `LH:`, `Zalo`, `Facebook`, `Fanpage`, `Telegram` lines
- `Downloaded by ... (email@example.com)`, `Studocu`, `Scribd`, `Course Hero`
  watermarks
- URLs and shortlinks on their own line
- `Chúc các bạn thi tốt!`, `Good luck!`, and other closing encouragement

**OCR debris**:

- a single stray character on its own line
- the same line duplicated immediately (a scan artifact)
- page-break hyphenation splitting a word across two lines — rejoin it rather
  than deleting

**What is not junk, even though it looks like it:**

- a phone number, URL, or company name that is *an option or part of a stem* —
  the same string is junk in a footer and content in an option
- `(Chọn 2 đáp án)`, `(Chọn đáp án đúng nhất)` — this is instruction, so it goes
  into the parentheses on the back, per Case C
- a section heading that groups questions (`PHẦN II: MẠNG MÁY TÍNH`) — not junk
  and not a card; it is context you drop from the output but should mention in
  the report if you used it to interpret anything

When you cannot decide, keep the line and flag it. A spurious card costs one
click; a dropped question is discovered during an exam.

---

## Question types

**Matching questions** (`Nối cột A với cột B`). One card per pair, not one card
for the whole exercise. Front is the item from the left column, back is its
match. The instruction line becomes the parenthetical on the back if it carries
anything useful. If the pairing is not stated anywhere in the source, this is an
unanswered question: skip it and report it.

**Ordering / sequencing questions.** Front is the prompt plus the shuffled items
as lettered options; back is the correct order as a sequence of letters with
their content, one per line, in the correct order rather than alphabetical order.
Note that this is the one case where a multi-line back is deliberately *not* in
letter order — say so in the report so the user knows it was intentional.

**Fill-in-the-blank.** Keep the blank in the front exactly as the source writes
it (`___`, `.....`, `(...)`). Back is the missing text with no letter prefix. If
one sentence has several blanks, keep it as one card and put the answers on the
back in order, one per line.

**Short answer and essay prompts.** Front is the prompt; back is the model answer
if the source supplies one. If the source supplies no answer, skip it — an essay
prompt with an invented answer is worse than no card.

**True/false.** If the source lists the two choices as a list, letter them
(`A. Đúng` / `B. Sai`). If the source is a bare statement with the verdict given
separately, the front has no options and the back is `Đúng` with no letter.

**Questions with sub-questions** (`Câu 5a`, `Câu 5b`). One card per sub-question.
If they share a common stem or passage, repeat the shared stem on each card —
Quizlet shuffles cards, so a card that depends on the previous one is broken.

**Questions attached to a shared passage or case study.** Same rule: repeat the
passage on every card that needs it. If the passage is long, summarize it to the
part the question actually needs, and flag in the report that you did.

**Questions containing an image.** Quizlet's text import cannot carry images.
Emit the card with a marker in the front — for example
`[hình: sơ đồ mạch điện]` — and list every such card in the report so the user
can attach the images by hand afterwards. Do not silently drop them.

**Questions containing a table.** Keep the table as plain-text lines inside the
front. It will look rough but stays legible. Do not introduce blank lines to
format it — blank lines are not allowed anywhere in the file.

---

## Options that fight the format

**More than 26 options.** Not a real case. If you compute a letter past `Z`, you
have mis-detected where the options stop — re-read the block.

**An option whose text contains `$$$` or `###`.** Extremely rare, but it would
break the import. Replace the literal separator inside the content with a
visually similar substitute (`＃＃＃`) and flag the card in the report.

**An option that spans multiple lines** (wrapped by the source's line width).
Join it into one line. An option is always exactly one line in the output;
otherwise the trailing lines are read as further options and the letter sequence
breaks.

**Options whose text already ends with a parenthesis**, e.g.
`A. Bộ nhớ trong (RAM)`. This is fine. The back is
`A. Bộ nhớ trong (RAM)`, and if it also needs an annotation it becomes
`A. Bộ nhớ trong (RAM) (Gợi ý: ...)`. The validator handles both.

**Duplicated option letters in the source** (`A. B. B. C.`). The source has a
typo. Renumber consecutively from `A` and flag the card.

**"All of the above" / "Tất cả các đáp án trên".** Treat as an ordinary option.
Because Quizlet shuffles cards but not the text inside a card, its meaning
survives.

**A question with only one option.** Almost always a parsing failure — an option
line was absorbed into the stem, or the block was cut off. Re-read it; do not
emit a one-option card.

---

## Answer-key problems

**Key numbering does not match question numbering.** Common when a file merges
two sources and numbering restarts at 1. Match by position within the block the
key covers, and if you cannot establish the mapping with confidence, skip the
affected questions and report them — a confidently mis-keyed card is the worst
possible output.

**Key and inline marker disagree.** Prefer the inline marker, and flag the
disagreement with the source position so the user can check.

**The key gives an answer letter that does not exist** (`Đáp án: E` for a
four-option question). Skip the card and report it.

**The key marks two letters for a question that reads as single-answer.** Treat
it as multi-answer and emit both on the back; flag it.

**Answers marked only by formatting** (bold, highlight, colour) in a `.docx` or
`.pdf`. If your extraction lost the formatting, the answers are gone even though
the text looks complete. Say so explicitly rather than guessing: report that the
source marks answers typographically and that the extraction did not preserve it,
and ask the user for a copy that keeps the markup.

---

## Structural problems

**The same question appears twice.** If both copies carry the same answer, emit
one card and note the deduplication. If they disagree, emit neither and flag both
positions.

**A question block is cut off** (the file ends mid-block, or a page break ate the
options). Skip it and report the position.

**Two questions run together on one line** because a line break was lost. Split
them. This is one of the reasons Step 1 forbids sampling — you only notice by
reading the surrounding text.

**The file mixes languages.** Keep every question in the language the source
wrote it in. Never translate: the user is studying for an exam in that language,
and a translated card tests the wrong thing.

**The file is not a question bank at all** (it is lecture notes, a glossary, a
definition list). A glossary converts cleanly — term on the front, definition on
the back, no options and therefore no letter prefixes. Say what you detected
before converting, so the user can redirect you if that was not the intent.

---

## Content you must not change

Keep the source's wording, spelling, capitalization, and diacritics exactly.
Specifically, do not:

- translate anything
- fix the source's typos or grammar — you cannot tell a typo from the exact
  string the exam will use, and a "corrected" card no longer matches the answer
  key the user is being graded against
- reorder options, which would invalidate the answer letters
- expand or contract abbreviations
- normalize Vietnamese tone-mark placement (`hòa` vs `hoà`) — both are valid and
  the user's answer key uses one of them

The one exception is mechanical repair of extraction damage: rejoining a word
split across a page break, collapsing a wrapped option onto one line, and
removing junk. Those restore the source rather than editing it.
