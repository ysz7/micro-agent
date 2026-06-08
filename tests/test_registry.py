"""Tool discovery: built-ins always present; tools/*.py auto-discovered."""

from agent.config import load_config
from agent.registry import discover_tools, tool_names

_TOOL_FILE = '''\
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


def no_doc(x: int) -> int:           # skipped: no docstring
    return x


def _private(x: int) -> int:         # skipped: underscore-prefixed
    """Should be ignored."""
    return x
'''


def test_builtins_always_registered(tmp_path):
    cfg = load_config(tmp_path)
    names = tool_names(discover_tools(cfg))
    for builtin in ("read_file", "write_file", "list_dir", "run_shell", "fetch_url"):
        assert builtin in names


def test_autodiscovery_rules(tmp_path):
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (tools_dir / "math_tools.py").write_text(_TOOL_FILE, encoding="utf-8")
    (tools_dir / "_example.py").write_text(  # whole file skipped (underscore)
        'def shadow(x: int) -> int:\n    """nope."""\n    return x\n', encoding="utf-8"
    )

    cfg = load_config(tmp_path)
    names = tool_names(discover_tools(cfg))

    assert "add" in names           # documented, type-hinted → registered
    assert "no_doc" not in names    # missing docstring
    assert "_private" not in names  # underscore function
    assert "shadow" not in names    # underscore file
