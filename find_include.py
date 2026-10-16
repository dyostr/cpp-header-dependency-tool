
import argparse
import re
import shutil
import sys
from pathlib import Path

INCLUDE_RE = re.compile(
    r'^\s*#\s*include\s*([<"])([^">]+)[">]',
    re.MULTILINE
)


def read_text(path: Path) -> str:
    """Read a text file while tolerating encoding errors."""
    return path.read_text(encoding="utf-8-sig", errors="replace")


def find_include(
    name: str,
    quoted: bool,
    parent_dir: Path,
    include_dirs: list[Path],
) -> Path | None:
    """Resolve an include using the specified search directories."""
    candidates = []

    if quoted:
        candidates.append(parent_dir / name)

    candidates.extend(directory / name for directory in include_dirs)

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    return None


def scan_headers(
    root_header: Path,
    include_dirs: list[Path],
) -> tuple[list[Path], list[str]]:
    """Recursively collect header dependencies without duplicates."""
    visited = set()
    headers = []
    unresolved = []

    def visit(header: Path):
        header = header.resolve()

        if header in visited:
            return

        visited.add(header)
        headers.append(header)

        try:
            content = read_text(header)
        except OSError as error:
            unresolved.append(f"{header}: {error}")
            return

        for match in INCLUDE_RE.finditer(content):
            delimiter = match.group(1)
            name = match.group(2).strip()

            line_number = content.count("\n", 0, match.start()) + 1

            dependency = find_include(
                name=name,
                quoted=(delimiter == '"'),
                parent_dir=header.parent,
                include_dirs=include_dirs,
            )

            if dependency is None:
                unresolved.append(
                    f"{header}:{line_number}: {name}"
                )
                continue

            visit(dependency)

    visit(root_header)
    return headers, unresolved


def determine_root(
    root_header: Path,
    include_dirs: list[Path],
    explicit_root: str | None,
) -> Path:
    """Determine the root used to preserve directory structure."""
    if explicit_root:
        return Path(explicit_root).resolve()

    paths = [root_header.resolve()]
    paths.extend(directory.resolve() for directory in include_dirs)

    try:
        return Path(
            __import__("os").path.commonpath(
                [str(path) for path in paths]
            )
        ).resolve()
    except ValueError:
        return root_header.parent.resolve()


def copy_headers(
    headers: list[Path],
    source_root: Path,
    destination: Path,
) -> list[str]:
    """Copy headers while preserving paths relative to the source root."""
    copied = []
    destination = destination.resolve()

    for header in headers:
        try:
            relative_path = header.relative_to(source_root)
        except ValueError:
            print(
                f"WARNING: Skipping file outside source root: {header}",
                file=sys.stderr,
            )
            continue

        target = destination / relative_path

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(header, target)
            copied.append(str(target))
        except OSError as error:
            print(
                f"ERROR: Could not copy {header}: {error}",
                file=sys.stderr,
            )

    return copied


def main():
    parser = argparse.ArgumentParser(
        description="Recursively find and optionally copy C/C++ headers."
    )

    parser.add_argument(
        "header",
        help="Path to the header file to analyze",
    )
    parser.add_argument(
        "-I",
        dest="include_dirs",
        action="append",
        default=[],
        help="Include search directory; can be specified multiple times",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="File to save the dependency list",
    )
    parser.add_argument(
        "--copy-to",
        help="Destination directory for copying found headers",
    )
    parser.add_argument(
        "--root",
        help="Source root used to preserve relative directory structure",
    )

    args = parser.parse_args()

    root_header = Path(args.header).resolve()

    if not root_header.is_file():
        parser.error(f"Header file not found: {root_header}")

    include_dirs = [
        Path(directory).resolve()
        for directory in args.include_dirs
    ]

    for directory in include_dirs:
        if not directory.is_dir():
            print(
                f"WARNING: Include directory does not exist: {directory}",
                file=sys.stderr,
            )

    headers, unresolved = scan_headers(root_header, include_dirs)

    print("Found headers:")
    for header in headers:
        print(header)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "\n".join(str(header) for header in headers) + "\n",
            encoding="utf-8",
        )
        print(f"\nDependency list saved to: {output_path}")

    if args.copy_to:
        source_root = determine_root(
            root_header,
            include_dirs,
            args.root,
        )

        copied = copy_headers(
            headers,
            source_root,
            Path(args.copy_to),
        )

        print(f"\nSource root: {source_root}")
        print(f"Copied files: {len(copied)}")

        if copied:
            print(f"Destination: {Path(args.copy_to).resolve()}")

    if unresolved:
        print(
            "\nUnresolved includes:",
            file=sys.stderr,
        )
        for item in unresolved:
            print(f"  {item}", file=sys.stderr)

    print(f"\nTotal headers found: {len(headers)}")


if __name__ == "__main__":
    main()
