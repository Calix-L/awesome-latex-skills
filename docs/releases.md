# Releases and migration

`VERSION` and the five `metadata.version` values must agree. Releases use
semantic versions: patch for compatible fixes, minor for compatible additions,
major for breaking CLI/report/installation changes. Update the changelog and
migration notes before publishing.

## Build and publish

```sh
python -m pip install -r requirements-dev.txt
python scripts/als.py validate
python scripts/als.py evaluate validate
python scripts/als.py sources --validate-only
python -m unittest discover -s tests -v
python scripts/als.py examples run --output work/release-examples
python scripts/als.py paper --output work/release-paper
python -m pip install build
python -m build --outdir dist/package
python scripts/check_packages.py --directory dist/package --output work/package-verification
python scripts/als.py release --output dist/1.7.0 --distribution-dir dist/package
```

The default example run requires a real TeX engine. Portable mode is not a
substitute for the native release checks. The main-branch Tests workflow also
tests three operating systems, minimum/current Python and PyMuPDF, and real TeX
engines/backends. The manually dispatched [release packaging workflow](../.github/workflows/release.yml)
builds and uploads archives after its own validation, tests and native examples;
it does not publish a GitHub release automatically.

Packaging creates a full source ZIP, five individual skill ZIPs,
`release-manifest.json`, and `SHA256SUMS`. With `--distribution-dir`, it also
includes the wheel/source distribution after matching every bundled source
byte to the ZIP inventory. All eight archives are covered by the same manifest
and checksums. ZIP order, timestamps and permissions
are fixed; identical source bytes on the same Python/zlib runtime produce
identical archives. The manifest fingerprints every included file. Generated
logs and local installation receipts are excluded. Checksums establish
integrity, not authenticity.

After main's full CI passes, publish the archives using a version tag targeting
that **exact tested commit**, with the changelog as the release notes. Keep all
development on `main`; version tags do not introduce another development branch.
Download assets from [GitHub Releases](https://github.com/Calix-L/awesome-latex-skills/releases).

## 1.4.0 to 1.5.0

The installable CLI, project configuration, complete manuscript runner,
unified review and repeated-trial reporting are compatible additions.
Existing direct helpers, installation receipts and report schema numbers
remain supported. New schema-3 build reports add `pdf_sha256`; unified review
marks older reports without it as unverified for build-time PDF identity.

Use `python -m pip install .` or the release wheel for the new `als` entry point;
optional `pdf`/`validation` extras are described in the [package guide](install.md).
The main-branch source-review job now evaluates the current date rather than
a fixed reference date and can fail when an official-source review is due.
Dates still require an actual content review before renewal.

## 1.5.0 to 1.5.1

Repeated-trial reports now mark quality review as unverified when session reuse
rejects a pair, even if both rubric records exist. Underlying reviews stay in
the run records; no pair delta is inferred. Regenerate prepared tasks against
the current release before scoring them: a skill version change also changes
its context fingerprint. Keep the matching older CLI/batch together when
reproducing an older evaluation.

## 1.5.1 to 1.6.0

Direct helpers and schema-1 manual execution records remain compatible. New
batch catalogs add explicit `case_ids`; old catalogs still mean all ten cases.
Reports add measurement coverage and token totals without inventing missing
measurements. `benchmark run` is opt-in and executes the command you supply;
preparation and reporting still do not call a model. See the
[runner protocol](evaluation.md#execute-a-configured-command).

Runner-produced records bind all submitted file bytes. Preserve submissions
unchanged; put completed human reviews in the task's `human-review.json` rather
than editing the artifacts. Existing attempted tasks cannot be rerun in place.
Prepare a new task for a retry and keep the failed evidence. Blank review
templates do not count as human ratings. As with earlier updates, skill-version
changes require freshly prepared tasks or the matching older CLI and resources.

## 1.6.0 to 1.7.0

Project inspection remains schema 1 and adds `root_selection`,
`root_candidate_scope` and `configuration_sha256`. Explicit/configured roots
list candidates only for the selected main; automatic selection scans the full
supported inventory. Excluded `include` edges add `skipped: true` and
`exists: null`, since the target was not checked. Consumers must not interpret
null as a missing file.

The new `--html`/`--html-language` flags are optional. JSON output and native
exit codes stay supported. Invalid non-TeX/UTF-8/generated-directory main files
are now refused during initialization instead of creating an unusable config.
Inventory also prunes `.venv`, `venv` and `node_modules`; keep genuine manuscript
sources outside reserved generated trees. Full-paper artifacts add before/after
inspection HTML files. The [project guide](project.md) describes the supported
literal traversal and its limits. Skill metadata changes require fresh prepared
evaluation tasks or a matching older CLI/context when reproducing old runs.

## 1.3.x to 1.4.0

This is a compatible addition. Direct installer/build/extractor commands,
managed-install receipts, build schema 3 and extraction schema 2 are unchanged.
The project CLI envelope, evaluation, example and release manifests are schema 1.
The new project commands require the full checkout/archive; a selected skill
installation intentionally contains only its own resources.

```sh
git pull --ff-only
python scripts/als.py install --agent codex --update --dry-run
python scripts/als.py install --agent codex --update
```

Managed updates reject local changes, additions and deletions. Preserve your
edits and use a separate destination if you need both versions. For untracked
manual installs, only an exact match to the current source can be adopted;
keep differing copies backed up before moving them. See the
[installation guide](../README.md#quick-start).
