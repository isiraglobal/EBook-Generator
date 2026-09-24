#!/usr/bin/env python3
"""
Editorial Studio - AI Editorial Publishing Software
Main entry point for the application.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

import typer
from rich.console import Console

from editorial_studio.cli.main import app as cli_app
from editorial_studio.api.server import app as api_app
from editorial_studio.mcp_server.server import mcp as mcp_server
from editorial_studio.web.app import create_web_app

console = Console()


def main():
    """Main entry point - routes to CLI by default."""
    cli_app()


def run_api():
    """Run the FastAPI server."""
    import uvicorn
    from editorial_studio.core.config import load_config
    config = load_config().data
    uvicorn.run(api_app, host=config["api"]["host"], port=config["api"]["port"])


def run_web():
    """Run the web interface."""
    import uvicorn
    from editorial_studio.core.config import load_config
    config = load_config().data
    web_app = create_web_app()
    uvicorn.run(web_app, host=config["web"]["host"], port=config["web"]["port"])


def run_mcp():
    """Run the MCP server."""
    mcp_server.run()


if __name__ == "__main__":
    # Check for subcommands
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "api":
            sys.argv.pop(1)
            run_api()
        elif cmd == "web":
            sys.argv.pop(1)
            run_web()
        elif cmd == "mcp":
            sys.argv.pop(1)
            run_mcp()
        else:
            # Let typer handle it
            main()
    else:
        main()