from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class DiffLine:
    content: str
    line_number: int  # line number in the new file
    kind: str  # "added", "removed", "context"


@dataclass
class DiffHunk:
    file_path: str
    start_line: int
    lines: list[DiffLine] = field(default_factory=list)

    @property
    def added_lines(self) -> list[DiffLine]:
        return [l for l in self.lines if l.kind == "added"]


_FILE_HEADER = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_diff(unified_diff: str) -> list[DiffHunk]:
    hunks: list[DiffHunk] = []
    current_file: str | None = None
    current_hunk: DiffHunk | None = None
    new_line_num = 0

    for raw_line in unified_diff.splitlines():
        file_match = _FILE_HEADER.match(raw_line)
        if file_match:
            current_file = file_match.group(1)
            current_hunk = None
            continue

        hunk_match = _HUNK_HEADER.match(raw_line)
        if hunk_match and current_file:
            new_line_num = int(hunk_match.group(1))
            current_hunk = DiffHunk(file_path=current_file, start_line=new_line_num)
            hunks.append(current_hunk)
            continue

        if current_hunk is None:
            continue

        if raw_line.startswith("+"):
            current_hunk.lines.append(DiffLine(raw_line[1:], new_line_num, "added"))
            new_line_num += 1
        elif raw_line.startswith("-"):
            current_hunk.lines.append(DiffLine(raw_line[1:], new_line_num, "removed"))
        else:
            current_hunk.lines.append(DiffLine(raw_line[1:] if raw_line else "", new_line_num, "context"))
            new_line_num += 1

    return hunks
