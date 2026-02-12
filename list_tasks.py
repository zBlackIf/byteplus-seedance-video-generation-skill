#!/usr/bin/env python3
"""
List video generation tasks

Supports filtering by status, model, and task ID with pagination.
"""

import os
import sys
import argparse

try:
    from seedance_client import SeedanceClient
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from seedance_client import SeedanceClient


def format_task_list(data: dict) -> str:
    """
    Format task list as readable table

    Args:
        data: API returned data

    Returns:
        Formatted string
    """
    tasks = data.get("tasks", [])
    page_info = data.get("page", {})

    if not tasks:
        return "No tasks found."

    # Table header
    header = f"{'Status':<12} {'Model':<35} {'Task ID':<12} {'Created':<20}"
    separator = "-" * len(header)
    lines = [header, separator]

    # Task rows
    for task in tasks:
        status = task.get("status", "")
        model = task.get("model", "")
        task_id = task.get("id", "")
        created = task.get("created", "")[:19]  # Truncate to seconds

        # Truncate long model names
        if len(model) > 32:
            model = model[:29] + "..."

        # Truncate task ID
        if len(task_id) > 10:
            task_id = task_id[:8] + ".."

        lines.append(f"{status:<12} {model:<35} {task_id:<12} {created:<20}")

    # Pagination info
    lines.append("")
    page_num = page_info.get("page_num", 0)
    page_size = page_info.get("page_size", 0)
    total = page_info.get("total", 0)
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    lines.append(f"Page {page_num}/{total_pages} | Total tasks: {total}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="List video generation tasks with filtering and pagination",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all tasks
  python list_tasks.py

  # Filter by status
  python list_tasks.py --status succeeded

  # Filter by model
  python list_tasks.py --model doubao-seedance-1-5-pro-251215

  # Pagination
  python list_tasks.py --page-num 2 --page-size 20

  # Filter by specific task IDs
  python list_tasks.py --task-ids task1,task2,task3
        """
    )

    # Filter parameters
    parser.add_argument(
        "--status",
        type=str,
        choices=["queued", "running", "succeeded", "failed", "cancelled", "expired"],
        help="Filter by task status"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Filter by model ID"
    )
    parser.add_argument(
        "--task-ids",
        type=str,
        help="Comma-separated list of specific task IDs"
    )

    # Pagination parameters
    parser.add_argument(
        "--page-num",
        type=int,
        default=1,
        help="Page number (default: 1)"
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=10,
        help="Results per page, max 500 (default: 10)"
    )

    # Authentication
    parser.add_argument(
        "--api-key",
        type=str,
        help="Override API Key"
    )

    # Output format
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON"
    )

    args = parser.parse_args()

    # Validate parameters
    if args.page_num < 1:
        parser.error("--page-num must be >= 1")

    if args.page_size < 1 or args.page_size > 500:
        parser.error("--page-size must be between 1 and 500")

    # Parse task ID list
    task_ids = None
    if args.task_ids:
        task_ids = [tid.strip() for tid in args.task_ids.split(",")]

    try:
        client = SeedanceClient(api_key=args.api_key)
        data = client.list_tasks(
            page_num=args.page_num,
            page_size=args.page_size,
            status=args.status,
            model=args.model,
            task_ids=task_ids
        )

        if args.json:
            import json
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(format_task_list(data))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
