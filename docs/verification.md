# Verify a downloaded release or a transferred review

The verifier uses the Python standard library, reads local files, does not
contact the network, and does not extract or execute archive entries. Its
target directory is not modified. Checksums establish correspondence to the
stored manifest; release/tag/producer authentication and scientific fidelity
must be assessed separately.

## Release assets

Download **all assets from one release** into a dedicated directory, keeping
published filenames. Six ZIPs, `release-manifest.json` and `SHA256SUMS` are
required; if distributions are included, both wheel and source archive are
required too.

```sh
als verify release path/to/release-assets
als --json verify release path/to/release-assets
# From a trusted source checkout, without installing the CLI:
python scripts/als.py verify release path/to/release-assets
```

Checks cover file sizes/SHA-256, exact checksum coverage and agreement,
source/skill ZIP membership, source-file fingerprints, version, ZIP member
counts/CRCs and optional wheel/source-package resource correspondence.
Package metadata is covered by the outer archive hash, not a source fingerprint.

Unexpected files fail the inventory check. Keep notes, verification output
and extracted projects elsewhere. Do not mix versions or rename assets.
Obtain a fresh copy when a file is missing or changed; do not edit checksums
to make a damaged release pass.

## Review bundles

New review outputs include `integrity.json`, covering every file except itself:
HTML, JSON, diff, supplied logs/PDFs and generated page previews. Keep the
directory together when transferring it.

```sh
als verify review path/to/review-bundle
als --json verify review path/to/review-bundle
```

The check is portable: original project directories and build-machine paths
are not read. Missing, changed or extra files fail. The HTML/JSON/diff files
must all be inventoried. The manifest is not self-authenticating: someone who
can change both it and the contents can create a matching inventory.

Older reviews without the complete manifest remain **unverified**. Available
`retained_files` fingerprints are checked, and changed artifacts fail; HTML,
JSON and diff identity cannot be inferred. Regenerate a review for full
coverage. The verifier never adds, repairs or overwrites manifests.

## Results and limits

| Exit code | Meaning |
|---|---|
| `0` | Stored integrity checks passed; `verified` |
| `1` | File/archive mismatch or incomplete legacy coverage; inspect `failed` / `unverified` findings |
| `2` | Invalid metadata, unsafe paths, unsupported top-level bounds or arguments |

Archive structure failures are located `invalid-archive` findings with code 1;
malformed top-level inventories return 2. Symlinks, traversal/noncanonical
paths, duplicate/case-colliding names, archive links/special entries, encrypted
ZIPs and split/ZIP64 central-directory metadata are refused. Ordinary ZIP64
member headers remain supported within normal central-directory bounds.

Limits: 20,000 files/members, 512 MiB per file/member, 2 GiB per inventory/archive,
16 MiB for JSON/checksum/ZIP-directory metadata and individual tar metadata
reads. ZIP directory limits are checked before member-list parsing; gzip/tar
expanded offsets and reads are bounded. Keep inputs unchanged during these
point-in-time checks. No TeX, package installation, OCR or model is run.

See [releases](releases.md), [review](review.md) and the
[Chinese guide](verification_CN.md).
