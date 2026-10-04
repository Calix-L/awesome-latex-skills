# Source review / 来源维护

[sources.json](sources.json) tracks twelve selected primary sources, their exact
claim scope, dependent files, review date and interval. The register
covers core venue corrections and selected package/API guidance; it does not
claim that every venue/year or every linked reference has been verified.
It also records the inspected LaTeX graphics source used for literal search
ordering. Review dates declare content review; the audit does not authenticate
who performed it.

```sh
python scripts/als.py --json sources
python scripts/als.py sources --validate-only
```

The audit is offline. `current` means a recorded content review is still within
its interval; `due` means it needs another review; `unverified` means no review
date; `entrypoint-only` means the URL identifies the source but its relevant
contents have not been reviewed. Entry-point records remain pending even when
dated. Exit 1 signals pending work; `--validate-only` checks catalog validity
without treating pending review as an execution failure. Future dates and missing
dependent files fail validation. Use a fixed `--as-of` when reproducing a report.

The main-branch Tests workflow has a separate source-review job. Each invocation
uses the current date (CI timezone Asia/Shanghai), retains its JSON audit, and
fails when review is due/unverified. The portable tests validate catalog
structure; the review job and release gate require pending work to be resolved.
The workflow does not renew dates, fetch links or create issues automatically.

## Review procedure

1. Read the official source and relevant author kit, checking year, track,
   stage and article type. For APIs/packages, check the applicable version.
2. Record the exact supported scope. Update dependent guidance and regression
   cases when requirements change; preserve distinctions between review/final
   and verified/unverified claims.
3. Update `checked_on` and `verification` only after actual content review.
   A successful HTTP request does not renew a review date.
4. Run validation, affected behavior checks and source audit. Commit the
   guidance and catalog together on `main`.

The bibliography entries record the reviewed package overviews, not arbitrary
venue styles or complete package manuals. Add sources as their specific claims
are reviewed; do not turn this catalog into blanket compliance assurance.

中文：维护的是“哪些内容在何时被核验过”，不是链接能否访问。新日期需要实际
复核官方内容；会议规则必须明确年份、赛道及阶段，不能沿用旧规则直接宣称合规。
