# Copilot instructions: Quizlet import files

When the task is converting a quiz, exam dump, or question bank into a file for
Quizlet import, follow `SKILL.md` from the quizlet-import-skill repository in
full. Read it before starting; the format is byte-exact and easy to get subtly
wrong.

The rule most often broken: cards are joined by `###` with zero characters on
either side, so card N's answer and card N+1's question share a line:

```
Question one
A. opt1
B. opt2$$$B. opt2###Question two
A. opt3
B. opt4$$$A. opt3
```

The output looks cramped and malformed. That is correct output. Do not add a
newline next to `###`, and do not end the file with a newline — Quizlet imports
that whitespace as literal card content.

Validate with `python scripts/validate_quizlet.py <output.txt>` before handing
the file over.
