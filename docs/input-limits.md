# Input sizes and changing files

[简体中文](input-limits_CN.md) · [Project inspection](project.md) · [Review](review.md)

Project inspection, review evidence retention and offline verification use bounded
regular-file reads. An oversized or changing input produces an error instead of a
published partial inspection/review directory. Existing destinations remain protected.

| Input | Limit | When checked |
|---|---:|---|
| A source or `.als.json` | 2,000,000 bytes | Inventory and actual source reads |
| Review notes (`--notes`) | 2,000,000 bytes | Before staging the review |
| JSON metadata read/written by shared helpers | 16 MiB | Before parsing or writing |
| A hashed/copied asset or evidence file | 512 MiB | Before opening and while reading |
| Project inventory for each review side | 2 GiB, 5,000 files | Before hashing; actual snapshot byte total checked again |
| A sealed artifact inventory | 2 GiB, 20,000 files | Before sealing and during verification |

MiB and GiB mean powers of 1024. Equality is allowed. Notes/source limits count
UTF-8 bytes, including a BOM, rather than characters. These are tooling limits,
not TeX format limits. Source selection and the excluded-directory rules in
[inspection](project.md) and [review](review.md) still apply. The artifact total
is checked when sealing; it is not a disk quota for all intermediate build files.

For example, these review inputs are checked before publication:

```sh
als --json review --before original --after candidate --output ../review \
  --notes review-notes.txt --after-build candidate-build/build-report.json
```

Invalid review input returns exit code `2`; `--json` retains the error in `result.error`.
Reduce notes, remove unrelated inventoried files, or supply smaller relevant
assets/evidence before retrying with a new output directory. A missing optional
build report still means `unverified`, as before.

The file descriptor and pathname are checked for regular-file identity, size and
modification metadata before and after each read. Symlinks and special files are
refused by these helpers. On POSIX, nonblocking/no-follow open flags also protect
against a FIFO substituted between the initial check and opening. The copied
byte count and digest come from the same read; a build report's digest comes
from the exact bytes parsed. Originals and retained evidence are also rechecked
before publication.

These checks detect observed changes; they do not lock a project, prove producer
authenticity, catch every write that is fully reverted between observations, or
establish scientific correctness. Remote filesystem availability can still affect
I/O latency. Keep an unchanged original and make edits in a separate candidate.

[Tests](../tests/test_bounded_io.py) cover exact limits, actual stream growth,
file replacement, same-size edits, early refusal, notes encoding/escaping, parsed
report binding and publication cleanup. Native CI checks both POSIX and Windows
behavior; installed wheel and rebuilt-sdist checks exercise public limits from
outside the checkout. These are synthetic tooling controls.
