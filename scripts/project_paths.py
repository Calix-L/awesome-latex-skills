"""Resolve literal dependency paths relative to the selected main directory."""
from pathlib import Path, PurePosixPath, PureWindowsPath

from project_support import safe_path


def dependency_path(root, working_directory, *fragments):
    """Allow internal dot/parent traversal without relaxing manifest paths.

    Check each traversed component before normalization, including components
    later cancelled by '..'. Never follow a symlink or step outside the root.
    """
    root = Path(root).resolve()
    prefix = PurePosixPath(working_directory).as_posix()
    if prefix != ".":
        safe_path(root, prefix)
    parts = [] if prefix == "." else prefix.split("/")
    for fragment in fragments:
        if (not isinstance(fragment, str) or any(char in fragment for char in "\\:\x00\r\n")
                or PurePosixPath(fragment).is_absolute() or PureWindowsPath(fragment).drive):
            raise ValueError(f"Dependency must be a literal relative path: {fragment!r}")
        for component in fragment.split("/"):
            if component == "":
                continue
            current = root.joinpath(*parts)
            if component == ".":
                if not current.is_dir():
                    raise ValueError(f"Dot traversal requires an existing directory: {fragment}")
                continue
            if component == "..":
                if not parts:
                    raise ValueError(f"Dependency path leaves the project root: {fragment}")
                if not current.is_dir():
                    raise ValueError(f"Parent traversal requires an existing directory: {fragment}")
                parts.pop()
                continue
            parts.append(component)
            if root.joinpath(*parts).is_symlink():
                raise ValueError(f"Symlink in dependency path: {fragment}")
    if not parts:
        raise ValueError("Dependency path names the project root, not a file")
    return safe_path(root, "/".join(parts))
