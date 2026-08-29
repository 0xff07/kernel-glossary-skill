# PAGE-03: Code-block provenance comments

> Was: 7l. Code-block provenance comments

**Rule:** Every fenced ` ```c ` block opens with a provenance comment naming the on-disk origin of the excerpt, in the exact form `/* path/from/tree/root.c:LINE */` on its own first line, where LINE is the number of the first reproduced line in the file at the documented version. A short annotation may follow the line number (`/* mm/vma.c:497 (in __split_vma()) */`). A block that stitches excerpts from several places (a caller plus its callee, two distant case labels, a struct field plus the helper that writes it) marks each excerpt's start with its own interior `/* path:line */` delimiter, and marks elided code with a standalone `...` line. Everything between delimiters is verbatim file content per 7e.

The provenance comment is what makes a page checkable: a reviewer opens the named file at the cited line and compares the unit directly (the 3c procedures), so a missing or wrong provenance line turns an on-disk match into a finding, and a silently drifted excerpt is caught on the first comparison. Non-code fences (ASCII figures, quoted commit-message tables, shell output) carry no provenance comment and are not diffed.
