"""Extract the listings the paper shows from the code that produces its numbers.

A region of a source file between sentinel comments

    # <<name
    ...
    # >>name

is written to snippets/name.tex as a verbatim block, dedented.  The paper
\\input{}s those files, so a listing in the text is the code that ran, not a
transcript of it.  Nothing keeps them in step by hand.
"""
from __future__ import annotations

import pathlib
import textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIDTH = 70          # verbatim lines wider than this overflow the text block


def regions(path: pathlib.Path) -> dict[str, str]:
    out: dict[str, str] = {}
    name: str | None = None
    body: list[str] = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("# <<"):
            name, body = stripped[4:], []
        elif stripped.startswith("# >>"):
            if name is None or stripped[4:] != name:
                raise ValueError(f"{path.name}: unbalanced sentinel {stripped}")
            out[name] = textwrap.dedent("\n".join(body))
            name = None
        elif name is not None:
            body.append(line)
    if name is not None:
        raise ValueError(f"{path.name}: {name} is never closed")
    return out


def write() -> int:
    target = ROOT / "snippets"
    target.mkdir(exist_ok=True)
    found: dict[str, pathlib.Path] = {}
    for source in sorted((ROOT / "code").glob("*.py")):
        if source.name == "snippets.py":
            continue          # its own docstring shows the form
        for name, body in regions(source).items():
            if name in found:
                raise ValueError(f"{name} defined twice: {found[name]}, {source}")
            found[name] = source
            long = [ln for ln in body.splitlines() if len(ln) > WIDTH]
            if long:
                raise ValueError(f"{source.name}/{name}: line over {WIDTH} "
                                 f"columns: {long[0]!r}")
            (target / f"{name}.tex").write_text(
                "\\begin{verbatim}\n" + body + "\n\\end{verbatim}\n")
    return len(found)


if __name__ == "__main__":
    print(f"wrote {write()} snippets")
