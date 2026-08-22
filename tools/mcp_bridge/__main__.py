# FC-ID: DCD-MCP-BRIDGE-001 | 入口：python -m mcp_bridge [--evidence DIR] [--caller ID]
import sys
from pathlib import Path

from .server import serve_stdio


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    ev, caller = Path("mcp-evidence"), "mcp-client"
    if "--evidence" in argv:
        ev = Path(argv[argv.index("--evidence") + 1])
    if "--caller" in argv:
        caller = argv[argv.index("--caller") + 1]
    serve_stdio(ev, caller)


if __name__ == "__main__":
    main()
