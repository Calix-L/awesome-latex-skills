"""Bound regular-file reads and detect changes during an individual read."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat

MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_METADATA_BYTES = 16 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024


def identity(info):
    # Windows stat/fstat can use different ctime semantics; compare ctime only
    # between observations made through the same interface.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def signature(info):
    return (*identity(info), info.st_ctime_ns)


def file_stat(path, limit):
    info = Path(path).lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"Input must be a regular file: {Path(path).name}")
    if info.st_size > limit:
        raise ValueError(f"Input exceeds the {limit}-byte size limit: {Path(path).name}")
    return info


@contextmanager
def source_stream(path, limit):
    """Nonblocking/no-follow flags avoid opening a substituted FIFO on POSIX."""
    path = Path(path)
    before = file_stat(path, limit)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode) or identity(opened) != identity(before):
            raise ValueError(f"Input changed before reading: {path.name}")
        yield stream
        if signature(os.fstat(stream.fileno())) != signature(opened) or signature(file_stat(path, limit)) != signature(before):
            raise ValueError(f"Input changed during reading: {path.name}")


def consume(path, limit, sink=None):
    digest = hashlib.sha256()
    size = 0
    with source_stream(path, limit) as stream:
        while True:
            chunk = stream.read(min(CHUNK_BYTES, limit - size + 1))
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                raise ValueError(f"Input exceeds the {limit}-byte size limit: {Path(path).name}")
            digest.update(chunk)
            if sink is not None:
                sink.write(chunk)
    return {"sha256": digest.hexdigest(), "bytes": size}


def fingerprint(path, limit=None):
    return consume(path, MAX_FILE_BYTES if limit is None else limit)


def read_bytes(path, limit):
    with source_stream(path, limit) as stream:
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError(f"Input exceeds the {limit}-byte size limit: {Path(path).name}")
    return data


def copy_file(source, target, limit=None):
    """Write a fresh target using the same bounded, checked read as hashing."""
    # Reject oversized/nonregular sources before creating any target.
    limit = MAX_FILE_BYTES if limit is None else limit
    file_stat(source, limit)
    with Path(target).open("xb") as output:
        return consume(source, limit, output)
