#!/usr/bin/env python3
"""
Query video generation task status

Supports querying a single task and polling monitoring (watch mode).
"""

import os
import sys
import argparse

try:
    from seedance_client import (
        SeedanceClient,
        TaskStatus,
        TaskNotFoundError,
        TimeoutError
    )
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from seedance_client import (
        SeedanceClient,
        TaskStatus,
        TaskNotFoundError,
        TimeoutError
    )


def format_task_info(task) -> str:
    """
    Format task information as readable text

    Args:
        task: TaskInfo object

    Returns:
        Formatted string
    """
    status_emoji = {
        TaskStatus.QUEUED: "⏳",
        TaskStatus.RUNNING: "🔄",
        TaskStatus.SUCCEEDED: "✅",
        TaskStatus.FAILED: "❌",
        TaskStatus.EXPIRED: "⏰",
        TaskStatus.CANCELLED: "🚫"
    }

    emoji = status_emoji.get(task.status, "❓")

    lines = [
        f"{emoji} Task: {task.id}",
        f"  Status: {task.status.value}",
        f"  Model: {task.model}",
        f"  Created: {task.created_at}"
    ]

    if task.resolution:
        lines.append(f"  Resolution: {task.resolution}")
    if task.ratio:
        lines.append(f"  Ratio: {task.ratio}")
    if task.duration:
        lines.append(f"  Duration: {task.duration}s")

    # Add additional info based on status
    if task.status == TaskStatus.SUCCEEDED:
        if task.video_url:
            lines.append(f"  Video URL: {task.video_url}")
        if task.last_frame_url:
            lines.append(f"  Last Frame URL: {task.last_frame_url}")
        if task.usage:
            input_tokens = task.usage.get("input_tokens", 0)
            output_tokens = task.usage.get("output_tokens", 0)
            lines.append(f"  Usage: {input_tokens} input + {output_tokens} output tokens")
    elif task.status == TaskStatus.FAILED:
        if task.error_message:
            lines.append(f"  Error: {task.error_message}")

    return "\n".join(lines)


def poll_callback(task):
    """Poll callback function"""
    if task.status == TaskStatus.RUNNING:
        print(f"\rRunning... (Task: {task.id[:8]}...)", end="", flush=True)
    elif task.status == TaskStatus.QUEUED:
        print(f"\rQueued... (Task: {task.id[:8]}...)", end="", flush=True)


def download_video(url: str, output_path: str):
    """
    Download video file

    Args:
        url: Video download URL
        output_path: Output file path
    """
    try:
        import requests
        from tqdm import tqdm
    except ImportError:
        import requests
        tqdm = None

    print(f"\nDownloading video to: {output_path}")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get("content-length", 0))

    with open(output_path, "wb") as f:
        if tqdm:
            progress_bar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc="Downloading"
            )
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                progress_bar.update(len(chunk))
            progress_bar.close()
        else:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = downloaded / total_size * 100
                    print(f"\r{percent:.1f}%", end="", flush=True)
            print()

    print(f"Video saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Query status of a video generation task",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Query task status
  python query_video.py <task_id>

  # Watch task until completion
  python query_video.py --watch <task_id>

  # Watch with custom poll interval
  python query_video.py --watch <task_id> --poll-interval 10

  # Output as JSON
  python query_video.py --json <task_id>

  # Download completed video
  python query_video.py --watch <task_id> --download output.mp4
        """
    )

    parser.add_argument(
        "task_id",
        type=str,
        help="Task ID to query"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Poll until task completion with progress updates"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between polls (default: 5)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds (default: 600)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON"
    )
    parser.add_argument(
        "--download",
        type=str,
        metavar="PATH",
        help="Download completed video to specified path (only when watch mode succeeds)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Override API Key"
    )

    args = parser.parse_args()

    # Validate parameters
    if args.download and not args.watch:
        parser.error("--download requires --watch")

    try:
        client = SeedanceClient(api_key=args.api_key)

        if args.watch:
            # Watch mode
            print(f"Watching task: {args.task_id}")
            print(f"Poll interval: {args.poll_interval}s, Timeout: {args.timeout}s")
            print()

            task = client.wait_for_completion(
                task_id=args.task_id,
                poll_interval=args.poll_interval,
                timeout=args.timeout,
                callback=poll_callback
            )

            # Clear progress display
            print("\r" + " " * 50 + "\r", end="", flush=True)

            if args.json:
                import json
                result = {
                    "id": task.id,
                    "status": task.status.value,
                    "model": task.model,
                    "created_at": task.created_at,
                    "video_url": task.video_url,
                    "last_frame_url": task.last_frame_url,
                    "resolution": task.resolution,
                    "ratio": task.ratio,
                    "duration": task.duration,
                    "error_message": task.error_message,
                    "usage": task.usage
                }
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_task_info(task))

            # Download video
            if args.download and task.video_url:
                download_video(task.video_url, args.download)

        else:
            # Single query
            task = client.get_task(args.task_id)

            if args.json:
                import json
                result = {
                    "id": task.id,
                    "status": task.status.value,
                    "model": task.model,
                    "created_at": task.created_at,
                    "video_url": task.video_url,
                    "last_frame_url": task.last_frame_url,
                    "resolution": task.resolution,
                    "ratio": task.ratio,
                    "duration": task.duration,
                    "error_message": task.error_message,
                    "usage": task.usage
                }
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_task_info(task))

    except TaskNotFoundError:
        print(f"Error: Task not found: {args.task_id}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
