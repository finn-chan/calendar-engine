"""Command-line interface for Calendar Engine."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="calendar-engine",
        description="Unified Google Calendar synchronization tool for Contacts and Tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync all enabled services
  python -m app

  # Sync only contacts
  python -m app --only contacts

  # Sync only tasks
  python -m app --only tasks

  # Use custom config file
  python -m app --config /path/to/config.yaml

  # Enable debug logging
  python -m app --log-level DEBUG
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file (default: ./config/config.yaml)",
        metavar="PATH",
    )

    parser.add_argument(
        "--only",
        type=str,
        choices=["contacts", "tasks"],
        help="Sync only specific service (default: sync all enabled services)",
        metavar="SERVICE",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override logging level from config (default: from config)",
        metavar="LEVEL",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Calendar Engine v1.0.0",
    )

    return parser


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of argument strings (default: sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = create_parser()
    return parser.parse_args(args)


def validate_args(args: argparse.Namespace) -> bool:
    """Validate parsed arguments.

    Args:
        args: Parsed arguments namespace

    Returns:
        True if valid, False otherwise
    """
    # Validate config file exists if provided
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(
                f"Error: Configuration file not found: {args.config}", file=sys.stderr
            )
            return False

    return True
