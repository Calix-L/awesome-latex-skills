#!/usr/bin/env python3
"""Verify release archives, review or inspection bundles offline without extraction."""
import argparse
import gzip
import hashlib
from pathlib import Path
import re
import stat
import struct
import sys
import tarfile
import zipfile
import zlib

from artifact_integrity import (HASH, MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES,
                                MAX_METADATA_BYTES, portable_name, regular_files, validate_files)
from install import SKILLS
from project_support import parse_json


def bounded_file_hash(path):
    with path.open("rb") as stream:
        return streamed_hash(stream)


def metadata_bytes(path):
    if not path.is_file():
        raise ValueError(f"Metadata must be a regular file: {path.name}")
    if path.stat().st_size > MAX_METADATA_BYTES:
        raise ValueError(f"Metadata exceeds {MAX_METADATA_BYTES} bytes: {path.name}")
    with path.open("rb") as stream:
        data = stream.read(MAX_METADATA_BYTES + 1)
    if len(data) > MAX_METADATA_BYTES:
        raise ValueError(f"Metadata exceeds {MAX_METADATA_BYTES} bytes: {path.name}")
    return data


def metadata(path):
    return parse_json(metadata_bytes(path).decode("utf-8"))


def issue(result, code, name, message, severity="error"):
    result["findings"].append({"severity": severity, "code": code, "file": name, "message": message})


def report(root, kind):
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Verification target must be a directory")
    return root, {"schema": 1, "kind": "artifact_verification", "target_kind": kind,
                  "path": str(root), "status": "verified", "files_checked": 0, "archives_checked": 0,
                  "findings": [], "authentication": "not verified",
                  "interpretation": "Stored byte correspondence only; no producer authentication, TeX execution, model-quality or scientific-fidelity certification."}


def finish(result):
    severities = {item["severity"] for item in result["findings"]}
    result["status"] = "failed" if "error" in severities else "unverified" if severities else "verified"
    return result


def check_files(root, expected, result, exact=True, excluded=()):
    actual = regular_files(root)
    if exact:
        for name in sorted(set(actual) - set(expected) - set(excluded)):
            issue(result, "unexpected-file", name, "File is outside the stored inventory")
    for name, item in sorted(expected.items()):
        path = actual.get(name)
        if path is None:
            issue(result, "missing-file", name, "Inventoried file is missing")
            continue
        result["files_checked"] += 1
        if path.stat().st_size != item["bytes"] or bounded_file_hash(path) != item["sha256"]:
            issue(result, "changed-file", name, "Byte size or SHA-256 differs from the stored inventory")


def verify_review(root):
    root, result = report(root, "review")
    manifest_path = portable_name(root, "integrity.json")
    if not manifest_path.is_file():
        # Older reviews may bind retained build artifacts, but not HTML/JSON/diff.
        review = metadata(portable_name(root, "review.json"))
        if review.get("schema") != 1 or review.get("kind") != "project_review":
            raise ValueError("Expected a schema-1 project review")
        builds = review.get("builds")
        if not isinstance(builds, dict) or any(not isinstance(item, dict) for item in builds.values()):
            raise ValueError("Legacy review lacks structured build entries")
        rows = [row for build in builds.values() for row in build.get("retained_files", [])]
        if rows:
            check_files(root, validate_files(root, rows), result, exact=False)
        issue(result, "legacy-unsealed-review", "integrity.json", "No complete bundle manifest; retained artifacts alone cannot verify HTML, JSON or source diff. Regenerate the review for full coverage.", "unverified")
        result["scope"] = "legacy retained artifacts only"
        return finish(result)
    manifest_bytes = metadata_bytes(manifest_path)
    initial_manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = parse_json(manifest_bytes.decode("utf-8"))
    if manifest.get("schema") != 1 or manifest.get("kind") != "project_review_integrity":
        raise ValueError("Expected a schema-1 project-review integrity manifest")
    expected = validate_files(root, manifest.get("files"))
    if not {"review.json", "report.html", "changes.diff"}.issubset(expected) or "integrity.json" in expected:
        raise ValueError("Review manifest must cover HTML/JSON/diff and exclude itself")
    check_files(root, expected, result, excluded=("integrity.json",))
    if bounded_file_hash(portable_name(root, "integrity.json")) != initial_manifest_hash:
        issue(result, "changed-manifest", "integrity.json", "Manifest changed while verification was running")
    result["scope"] = "complete stored review file inventory; original project directories are not read"
    return finish(result)


def verify_inspection(root):
    root, result = report(root, "inspection")
    manifest_path = portable_name(root, "integrity.json")
    manifest_bytes = metadata_bytes(manifest_path)
    manifest = parse_json(manifest_bytes.decode("utf-8"))
    if type(manifest.get("schema")) is not int or manifest["schema"] != 1 or manifest.get("kind") != "project_inspection_integrity":
        raise ValueError("Expected a schema-1 project-inspection integrity manifest")
    expected = validate_files(root, manifest.get("files"))
    if set(expected) != {"inspection.json", "report.html"}:
        raise ValueError("Inspection manifest must cover exactly inspection.json and report.html")
    check_files(root, expected, result, excluded=("integrity.json",))
    if bounded_file_hash(portable_name(root, "integrity.json")) != hashlib.sha256(manifest_bytes).hexdigest():
        issue(result, "changed-manifest", "integrity.json", "Manifest changed while verification was running")
    result["scope"] = "complete stored inspection file inventory; original manuscript paths are not read and current source correspondence is not checked"
    return finish(result)


def verify_example(root):
    """Check a moved example's complete bytes and source-copy receipt without reading source paths."""
    root, result = report(root, "example")
    manifest_path = portable_name(root, "integrity.json")
    manifest_bytes = metadata_bytes(manifest_path)
    manifest = parse_json(manifest_bytes.decode("utf-8"))
    if type(manifest.get("schema")) is not int or manifest["schema"] != 1 or manifest.get("kind") != "worked_example_integrity":
        raise ValueError("Expected a schema-1 worked-example integrity manifest")
    expected = validate_files(root, manifest.get("files"))
    generated = {"example.json", "README.md", "report.html"}
    if not generated.issubset(expected) or "LICENSE" not in expected or "integrity.json" in expected:
        raise ValueError("Example manifest must cover guide, receipt, license and sources, excluding itself")
    check_files(root, expected, result, excluded=("integrity.json",))
    receipt_path = portable_name(root, "example.json")
    if receipt_path.is_file():
        receipt_bytes = metadata_bytes(receipt_path)
        if (len(receipt_bytes) != expected["example.json"]["bytes"]
                or hashlib.sha256(receipt_bytes).hexdigest() != expected["example.json"]["sha256"]):
            issue(result, "changed-receipt", "example.json", "Receipt bytes differ from the stored manifest; no changed receipt is interpreted")
            if bounded_file_hash(manifest_path) != hashlib.sha256(manifest_bytes).hexdigest():
                issue(result, "changed-manifest", "integrity.json", "Manifest changed while verification was running")
            result["scope"] = "stored example file inventory; changed receipt was not interpreted"
            return finish(result)
        receipt = parse_json(receipt_bytes.decode("utf-8"))
        if (type(receipt.get("schema")) is not int or receipt["schema"] != 1 or receipt.get("kind") != "worked_example_export"
                or receipt.get("origin") != "synthetic-maintainer-authored"
                or not isinstance(receipt.get("language"), str) or receipt["language"] not in {"en", "zh"}
                or not isinstance(receipt.get("version"), str) or re.fullmatch(r"\d+\.\d+\.\d+", receipt["version"]) is None
                or not isinstance(receipt.get("case"), str) or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", receipt["case"]) is None):
            raise ValueError("Expected a schema-1 synthetic worked-example receipt")
        sources = validate_files(root, receipt.get("source_files"))
        if set(sources) != set(expected) - generated:
            raise ValueError("Example source receipt must cover exactly the copied sources and license")
        for name, row in sources.items():
            if name == "LICENSE":
                source_name = "LICENSE"
            elif name.startswith("case/"):
                source_name = f"examples/{receipt['case']}/{name[5:]}"
            else:
                raise ValueError("Copied example sources must stay under case/")
            if row.get("source") != source_name:
                raise ValueError(f"Example source mapping disagrees with the copied path: {name}")
            if any(row[field] != expected[name][field] for field in ("sha256", "bytes")):
                issue(result, "source-receipt-mismatch", name, "Source receipt differs from the stored integrity inventory")
        for field in ("input", "candidate", "decisions"):
            name = receipt.get(field)
            portable_name(root, name)
            if not name.startswith("case/") or name not in sources:
                raise ValueError(f"Example {field} must name an inventoried case source")
        if bounded_file_hash(receipt_path) != hashlib.sha256(receipt_bytes).hexdigest():
            issue(result, "changed-receipt", "example.json", "Receipt changed while verification was running")
        result.update(version=receipt["version"], case=receipt["case"])
    if bounded_file_hash(manifest_path) != hashlib.sha256(manifest_bytes).hexdigest():
        issue(result, "changed-manifest", "integrity.json", "Manifest changed while verification was running")
    result["scope"] = "complete initial example bytes and source-copy receipt; installed repository paths are not read and edits intentionally fail"
    return finish(result)


def streamed_hash(stream):
    digest = hashlib.sha256()
    read = 0
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        read += len(chunk)
        if read > MAX_FILE_BYTES:
            raise ValueError("Archive member exceeds the per-file byte limit")
        digest.update(chunk)
    return digest.hexdigest()


def zip_inventory(root, archive):
    items = archive.infolist()
    if len(items) > MAX_FILES:
        raise ValueError("ZIP entry count exceeds the limit")
    found, folded, total = {}, set(), 0
    for item in items:
        if item.orig_filename != item.filename:
            raise ValueError("ZIP contains a hidden or truncated raw member name")
        name = item.filename[:-1] if item.is_dir() else item.filename
        portable_name(root, name)
        if name.casefold() in folded:
            raise ValueError(f"Duplicate or case-colliding ZIP entry: {name}")
        mode = stat.S_IFMT(item.external_attr >> 16)
        if mode not in {0, stat.S_IFREG, stat.S_IFDIR} or bool(mode == stat.S_IFDIR) and not item.is_dir():
            raise ValueError(f"ZIP contains a link or special entry: {name}")
        total += item.file_size
        if item.file_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or item.flag_bits & 1:
            raise ValueError("ZIP exceeds byte limits or contains encrypted entries")
        folded.add(name.casefold())
        if not item.is_dir():
            found[name] = item
    return found


def zip_preflight(path):
    """Bound central-directory parsing before ZipFile allocates its member list."""
    size = path.stat().st_size
    with path.open("rb") as stream:
        stream.seek(max(0, size - 65557))
        tail = stream.read(65557)
    offset = tail.rfind(b"PK\x05\x06")
    if offset < 0 or len(tail) - offset < 22:
        raise ValueError("ZIP end record is missing or truncated")
    _, disk, start_disk, disk_count, count, directory_bytes, directory_offset, comment = struct.unpack("<4s4H2LH", tail[offset:offset + 22])
    if disk or start_disk or disk_count != count or count > MAX_FILES or count == 65535:
        raise ValueError("ZIP split/ZIP64/count metadata is outside supported bounds")
    if directory_bytes > MAX_METADATA_BYTES or directory_offset == 0xffffffff:
        raise ValueError("ZIP central directory exceeds supported metadata bounds")
    end_position = size - len(tail) + offset
    if offset + 22 + comment != len(tail) or directory_offset + directory_bytes > end_position:
        raise ValueError("ZIP end record offsets or trailing data are inconsistent")


def check_zip(root, path, sources, names, wheel=False, release_version=None):
    zip_preflight(path)
    with zipfile.ZipFile(path) as archive:
        entries = zip_inventory(root, archive)
        if not wheel and set(entries) != names:
            raise ValueError("ZIP file inventory differs from its expected source/bundle inventory")
        prefix = "awesome_latex_skills/data/" if wheel else ""
        if wheel and {name[len(prefix):] for name in entries if name.startswith(prefix)} != names:
            raise ValueError("Wheel resource inventory differs from release sources")
        for name in entries:
            # Read all members to verify CRCs, including wheel metadata and code.
            with archive.open(name) as stream:
                digest = streamed_hash(stream)
            source_name = name[len(prefix):] if wheel and name.startswith(prefix) else name if not wheel else None
            if source_name is not None and digest != sources[source_name]:
                raise ValueError(f"Archive member differs from source fingerprint: {source_name}")
        if release_version is not None:
            if entries["VERSION"].file_size > 64 or archive.read("VERSION").decode("utf-8").strip() != release_version:
                raise ValueError("Archive VERSION differs from release version")
        return len(entries)


class BoundedTarReader:
    """Bound uncompressed offsets and oversized PAX/metadata reads before parsing."""
    def __init__(self, stream):
        self.stream = stream

    def tell(self):
        return self.stream.tell()

    def read(self, size):
        if size < 0 or size > MAX_METADATA_BYTES or self.tell() + size > MAX_TOTAL_BYTES:
            raise ValueError("Tar stream exceeds metadata or expanded byte limits")
        return self.stream.read(size)

    def seek(self, offset, whence=0):
        target = offset if whence == 0 else self.tell() + offset if whence == 1 else -1
        if not 0 <= target <= MAX_TOTAL_BYTES:
            raise ValueError("Tar stream seek exceeds expanded byte limits")
        return self.stream.seek(target)


def check_sdist(root, path, current, sources):
    prefix = f"awesome_latex_skills-{current}/"
    seen, folded, found, total = set(), set(), set(), 0
    with gzip.open(path, "rb") as compressed, tarfile.open(fileobj=BoundedTarReader(compressed), mode="r:") as archive:
        for number, item in enumerate(archive, 1):
            if number > MAX_FILES:
                raise ValueError("Source archive entry count exceeds the limit")
            name = item.name.rstrip("/")
            if item.isfile() and item.name != name:
                raise ValueError("Noncanonical source archive file name")
            portable_name(root, name)
            if name in seen or name.casefold() in folded or not (item.isfile() or item.isdir()):
                raise ValueError("Source archive contains duplicate/link/special entries")
            if name != prefix[:-1] and not name.startswith(prefix):
                raise ValueError("Unexpected source archive root")
            seen.add(name)
            folded.add(name.casefold())
            total += item.size
            if item.size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                raise ValueError("Source archive exceeds byte limits")
            if item.isfile():
                source_name = name[len(prefix):]
                with archive.extractfile(item) as stream:
                    digest = streamed_hash(stream)
                if source_name in sources:
                    if digest != sources[source_name]:
                        raise ValueError(f"Source archive differs from source fingerprint: {source_name}")
                    found.add(source_name)
    if found != set(sources):
        raise ValueError("Source distribution omits release sources")


def verify_release(root):
    root, result = report(root, "release")
    manifest_path = portable_name(root, "release-manifest.json")
    checksums_path = portable_name(root, "SHA256SUMS")
    if not manifest_path.is_file() or not checksums_path.is_file():
        raise ValueError("Release requires regular release-manifest.json and SHA256SUMS files")
    manifest_bytes, checksum_bytes = metadata_bytes(manifest_path), metadata_bytes(checksums_path)
    initial = {"release-manifest.json": hashlib.sha256(manifest_bytes).hexdigest(), "SHA256SUMS": hashlib.sha256(checksum_bytes).hexdigest()}
    manifest = parse_json(manifest_bytes.decode("utf-8"))
    current = manifest.get("version")
    if manifest.get("schema") != 1 or not isinstance(current, str) or not re.fullmatch(r"\d+\.\d+\.\d+", current):
        raise ValueError("Release manifest needs schema 1 and a semantic version")
    rows = validate_files(root, manifest.get("archives"))
    zip_names = {f"awesome-latex-skills-{current}.zip", *(f"{skill}-{current}.zip" for skill in SKILLS)}
    dist_names = {f"awesome_latex_skills-{current}-py3-none-any.whl", f"awesome_latex_skills-{current}.tar.gz"}
    if set(rows) not in (zip_names, zip_names | dist_names):
        raise ValueError("Release must contain the complete six-ZIP set and optionally both wheel and source distribution")
    sources = manifest.get("source_files")
    if not isinstance(sources, dict) or not sources or len(sources) > MAX_FILES:
        raise ValueError("Release needs bounded source fingerprints")
    folded = set()
    for name, digest in sources.items():
        portable_name(root, name)
        if name.casefold() in folded or not isinstance(digest, str) or HASH.fullmatch(digest) is None:
            raise ValueError("Invalid or case-colliding release source fingerprints")
        folded.add(name.casefold())
    if not {"VERSION", "LICENSE", *(f"{skill}/SKILL.md" for skill in SKILLS)}.issubset(sources):
        raise ValueError("Release source fingerprints omit required bundle/version files")
    checksums = {}
    for line in checksum_bytes.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match or match[2] in checksums:
            raise ValueError("Malformed or duplicate SHA256SUMS entry")
        portable_name(root, match[2])
        checksums[match[2]] = match[1]
    if set(checksums) != set(rows) | {"release-manifest.json"}:
        raise ValueError("SHA256SUMS coverage differs from the release manifest")
    for name, item in rows.items():
        if checksums[name] != item["sha256"]:
            issue(result, "checksum-disagreement", name, "SHA256SUMS and release manifest disagree")
    if checksums["release-manifest.json"] != initial["release-manifest.json"]:
        issue(result, "changed-file", "release-manifest.json", "Manifest does not match SHA256SUMS")
    check_files(root, rows, result, excluded=("release-manifest.json", "SHA256SUMS"))
    for name, item in sorted(rows.items()):
        path = portable_name(root, name)
        if not path.is_file() or any(row["file"] == name and row["severity"] == "error" for row in result["findings"]):
            continue
        try:
            if name in zip_names:
                skill = next((skill for skill in SKILLS if name == f"{skill}-{current}.zip"), None)
                expected = {source for source in sources if source.startswith(skill + "/")} | {"LICENSE"} if skill else set(sources)
                count = check_zip(root, path, sources, expected, release_version=current if skill is None else None)
                if type(item.get("entries")) is not int or item["entries"] != count:
                    raise ValueError("ZIP member count differs from the manifest")
            elif name.endswith(".whl"):
                check_zip(root, path, sources, set(sources), wheel=True)
            else:
                check_sdist(root, path, current, sources)
            if bounded_file_hash(path) != item["sha256"]:
                raise ValueError("Archive changed during verification")
            result["archives_checked"] += 1
        except (OSError, ValueError, KeyError, RuntimeError, EOFError, zlib.error, zipfile.BadZipFile, tarfile.TarError) as exc:
            issue(result, "invalid-archive", name, str(exc))
    for name, digest in initial.items():
        if bounded_file_hash(portable_name(root, name)) != digest:
            issue(result, "changed-manifest", name, "Metadata changed during verification")
    result.update(version=current, scope="complete stored release file inventory and archive source fingerprints; no extraction or execution")
    return finish(result)


def main(argv=None):
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="kind", required=True)
    verifiers = {"release": verify_release, "review": verify_review, "inspection": verify_inspection, "example": verify_example}
    for kind in verifiers:
        command = sub.add_parser(kind)
        command.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        result = verifiers[args.kind](args.directory)
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            print(f"{args.kind} integrity: {result['status']}; {result['files_checked']} files, {result['archives_checked']} archives checked")
            for item in result["findings"]:
                print(f"[{item['severity']}] {item['file']}: {item['message']}")
            print("Verification is relative to the stored manifest; producer authenticity is not verified.")
        return 0 if result["status"] == "verified" else 1
    except (OSError, ValueError, TypeError, UnicodeError, KeyError, zipfile.BadZipFile, tarfile.TarError) as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
