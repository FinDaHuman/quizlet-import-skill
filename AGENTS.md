# AGENTS.md

This repository is a single skill: **converting a messy quiz or question bank
into a `.txt` file that imports into Quizlet.**

**Read [`SKILL.md`](SKILL.md) in full before doing that work.** It is the only
source of truth. This file exists so that agents which load `AGENTS.md`
automatically know the skill is here, and it repeats only the one rule that is
broken most often.

## The rule that gets broken

The output format is byte-exact. A file with three cards is exactly this:

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

Card N's answer and card N+1's question **share a line**. There is nothing —
no space, no newline — on either side of `###`. The file looks cramped and
wrong; that is what correct output looks like. Do not tidy it, and do not end
the file with a newline. A newline you add next to `###` is imported by Quizlet
as literal content inside a card.

Everything else — reading the whole input, stripping question numbers,
normalizing option prefixes to `A. B. C. D.`, the three rules for parenthetical
material, finding answers in an end-of-file answer key, removing ads and page
furniture, and the reconciliation report you owe the user — is in `SKILL.md`.

## Validating

```bash
python scripts/validate_quizlet.py <output.txt>
```

Exit code 0 means the file is safe to hand over. If you cannot execute code,
walk the identical checklist in `SKILL.md` section 6 by hand.
