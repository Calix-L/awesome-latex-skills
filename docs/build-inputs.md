# Keep selected local inputs consistent during a build

[中文](build-inputs_CN.md) · [Build helper details](../latex-rescue/references/build-check.md) · [Review workflow](review.md)

Select local bibliography databases, styles or other resources whose bytes
must stay consistent while the build runs. For example:

```sh
als build path/to/paper/main.tex --backend bibtex --output work/guarded-build --until-stable --require-resolved --watch-input references.bib --watch-input styles/local.bst
```

For an existing `.als.json`, use `--project path/to/paper` instead of the source
argument; select watched files in the same way. Standalone installed skills
support the same options through `latex-rescue/scripts/check_build.py`.

**Paths are relative to the selected main file's directory**, including when it
is nested within a configured project. They are not relative to the shell's
working directory or necessarily the configuration file. Use `/` separators;
quote names containing spaces. A filename starting with `-` can be passed as
`--watch-input=--refs.bib`. Repeat the flag for each selected file.

## Evidence and outcomes

| Stage | Evidence |
|---|---|
| Before creating build output | Validate paths and hash every selected file; invalid/missing files create no build directory and launch no native tools |
| After each engine/backend process | Hash selected files again, even when a process fails or times out normally |
| End of a normally completed build attempt | Check selected files again with the existing local-input final observations |

An otherwise successful native build fails if a selected file changes, becomes
unreadable, disappears or is replaced by a symlink. The tool preserves the
author's current files, retains logs and the failed JSON evidence, and does not
present its PDF as a verified success. A process failure retains its own cause.
Preflight failures use exit `2`; an inconsistent completed build uses exit `1`.

Schema-3 `input_tracking.watched_inputs` lists explicit selections.
Each corresponding `local_inputs` entry starts with a `preflight` observation,
then records step names, SHA-256, byte size and errors. Recorder overlap is
deduplicated per step. Native recorder coverage remains separately listed in
`input_tracking.recorder_steps`. Omitting the flag preserves the existing
recorder-based scope and adds an empty watched-input list.

## Attach the evidence to review

```sh
als review --before path/to/original --after path/to/paper --after-build work/guarded-build/build-report.json --output work/guarded-review
als verify review work/guarded-review
```

The review report lists **Explicitly watched inputs** beside the supplied build.
It rechecks all recorded hashes, including starting observations, and retains
the build report. A later bibliography edit makes the old evidence stale and
prevents review publication; rebuild the current candidate into fresh output.
Failed inconsistent-input evidence can be read directly without attaching it
as evidence for the current source. Do not restore old author files just to
satisfy a stale report.

## Limits

- Select existing regular files inside the main file's directory tree. Absolute,
  traversing and nonportable paths, symlinks and selections inside build output
  are refused. No wildcard or automatic backend dependency discovery is implied.
- At most 128 selector arguments; duplicate file selections are deduplicated.
  Each selected file is limited to 64 MiB at preflight and each later read;
  the initial selected set is limited to 256 MiB. Hashing streams the bytes.
- Selection does not prove that BibTeX/Biber consumed that file. Unselected
  bibliography/system resources remain outside this explicit guard unless the
  engine independently records them in its local-input scope.
- Point-in-time hashes do not lock editors or snapshot the build. Changes reverted
  between observations, transient redirection races, interruptions and evidence
  I/O failures can leave consistency unverified. Scientific content, publisher
  authenticity and complete environment reproducibility need separate evidence.

The complete [English/Chinese synthetic manuscript](../examples/full-paper/README.md)
now watches its local bibliography and style during native builds. Its exported
offline guide includes the same selected-input commands.

## Explicit relative BibTeX resources

For literal `./`/`../` database or style names in generated reachable AUX files,
BibTeX receives staged aliases inside the output directory. `prepared_inputs`
records copied bytes and source-resource binding; preparation does not change
source files or original AUX. Ordinary invocations remain unchanged. This is
separate from recorder inputs and strict main-directory watch selectors.
[Scope, limits and review retention](relative-paths.md).
