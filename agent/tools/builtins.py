"""The irreducible set of built-in tools, registered on every agent.

``read_file`` · ``write_file`` · ``list_dir`` · ``run_shell`` (the workhorse) ·
``fetch_url``. Each is a plain function with a docstring + type hints; Pydantic
AI derives the JSON schema from the signature, so there is no schema code of our
own. Tools that need shared state take ``RunContext[AgentDeps]`` as the first
parameter and reach the http client / store / settings via ``ctx.deps``.

Relative paths resolve inside the agent's ``workspace/`` sandbox; absolute paths
are honored as given.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from pydantic_ai import RunContext

from ..runtime.context import AgentDeps


def _resolve(ctx: RunContext[AgentDeps], path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (ctx.deps.workspace / p)


def read_file(ctx: RunContext[AgentDeps], path: str) -> str:
    """Read and return the text contents of a file.

    Args:
        path: File path. Relative paths are resolved inside the workspace.
    """
    target = _resolve(ctx, path)
    if not target.exists():
        return f"Error: file not found: {target}"
    try:
        return target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"Error: {target} is not a UTF-8 text file."


def write_file(ctx: RunContext[AgentDeps], path: str, content: str) -> str:
    """Write text to a file, creating parent directories as needed.

    Args:
        path: Destination path. Relative paths are written inside the workspace.
        content: The full text to write (overwrites any existing file).
    """
    target = _resolve(ctx, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} chars to {target}"


def list_dir(ctx: RunContext[AgentDeps], path: str = ".") -> list[str]:
    """List the entries of a directory (directories are suffixed with '/').

    Args:
        path: Directory path. Relative paths are resolved inside the workspace.
    """
    target = _resolve(ctx, path)
    if not target.exists():
        return [f"Error: directory not found: {target}"]
    if not target.is_dir():
        return [f"Error: not a directory: {target}"]
    return sorted(
        f"{e.name}/" if e.is_dir() else e.name for e in target.iterdir()
    )


def run_shell(ctx: RunContext[AgentDeps], command: str, timeout: int = 120) -> str:
    """Run a shell command in the workspace and return its combined output.

    The workhorse tool: use it for builds, tests, git, file manipulation, and
    anything not covered by a dedicated tool.

    Args:
        command: The shell command line to execute.
        timeout: Seconds before the command is killed (default 120).
    """
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=str(ctx.deps.workspace),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    out = (proc.stdout or "") + (proc.stderr or "")
    out = out.strip() or "(no output)"
    if proc.returncode != 0:
        out = f"[exit {proc.returncode}]\n{out}"
    return out[:20000]


def fetch_url(ctx: RunContext[AgentDeps], url: str) -> str:
    """Fetch a URL and return its body text (truncated to ~20k chars).

    Args:
        url: The http(s) URL to GET.
    """
    try:
        resp = ctx.deps.http.get(url)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001 - surface any transport error to the model
        return f"Error fetching {url}: {exc}"
    text = resp.text
    return text[:20000] + ("…(truncated)" if len(text) > 20000 else "")


#: The built-in tool functions, in registration order.
BUILTIN_TOOLS = [read_file, write_file, list_dir, run_shell, fetch_url]
