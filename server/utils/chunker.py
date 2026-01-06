import re
from typing import List

BULLET_RE = re.compile(r'^(\s*[-•*–]|\s*\d+\.)')

def is_table_line(line: str) -> bool:
    if '|' in line:
        return True
    if re.search(r'\s{2,}', line) and any(char.isdigit() for char in line):
        return True
    return False

def split_into_blocks(text: str) -> List[str]:
    lines = text.splitlines()
    blocks = []
    current = []

    def flush():
        if current:
            blocks.append("\n".join(current).strip())
            current.clear()

    in_table = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flush()
            in_table = False
            continue

        # Table block
        if is_table_line(stripped):
            current.append(stripped)
            in_table = True
            continue

        # Bullet block
        if BULLET_RE.match(stripped):
            current.append(stripped)
            continue

        # Normal text
        if in_table:
            flush()
            in_table = False

        current.append(stripped)

    flush()
    return blocks
