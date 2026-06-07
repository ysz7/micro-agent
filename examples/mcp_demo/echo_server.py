"""A tiny self-contained MCP server for demonstrating the MCP seam.

Exposes one stdio tool, ``shout``. Point an agent at it from ``settings.yaml``::

    mcp:
      - name: demo
        command: python            # or an absolute path to a python with `mcp`
        args: ["examples/mcp_demo/echo_server.py"]

Then ask the agent to use the ``demo_shout`` tool (the ``demo`` prefix comes from
the ``name:`` field). Run directly to sanity-check: ``uv run python
examples/mcp_demo/echo_server.py`` (it will wait for an MCP client on stdio).
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")


@mcp.tool()
def shout(text: str) -> str:
    """Return the given text upper-cased with emphasis."""
    return text.upper() + "!!!"


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
