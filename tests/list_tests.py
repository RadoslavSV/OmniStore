from __future__ import annotations

import ast
from pathlib import Path

TESTS_DIR = Path("tests")


def iter_test_functions(py_file: Path):
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            yield node.name


def main():
    rows = []
    for py in sorted(TESTS_DIR.rglob("test_*.py")):
        for test_name in iter_test_functions(py):
            rows.append((test_name, py.name))

    # Print format suitable for thesis copy-paste
    cnt = 1;
    for test_name, file_name in rows:
        print(f"{cnt}) {test_name} ({file_name})")
        cnt = cnt + 1


if __name__ == "__main__":
    main()
