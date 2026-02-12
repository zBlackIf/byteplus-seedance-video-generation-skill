#!/usr/bin/env python3
"""
Create video generation task

Supports text-to-video (T2V) and image-to-video (I2V) modes.
Can automatically monitor and download video after task creation.
"""

import argparse
import base64
import os
import sys
import mimetypes
from typing import Optional, List, Dict, Any
from pathlib import Path

try:
    from seedance_client import (
        SeedanceClient,
        InvalidRequestError,
        TaskStatus,
        TimeoutError
    )
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from seedance_client import (
        SeedanceClient,
        InvalidRequestError,
        TaskStatus,
        TimeoutError
    )


def read_image_file(file_path: str) -> str:
    """
    Read image file and return Base64 encoded string

    Args:
        file_path: Image file path

    Returns:
        Base64 encoded string, format: "data:mime/type;base64,..."
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Get MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "image/jpeg"

    # Check file size (30MB limit)
    file_size = path.stat().st_size
    if file_size > 30 * 1024 * 1024:
        raise ValueError(f"Image file exceeds 30MB limit: {file_size / 1024 / 1024:.2f}MB")

    # Read and encode
    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{data}"


def build_content_array(
    prompt: Optional[str],
    image: Optional[str],
    last_frame: Optional[str],
    reference_images: Optional[List[str]],
    draft_task_id: Optional[str]
) -> List[Dict[str, Any]]:
    """
    Build content array

    Args:
        prompt: Text prompt
        image: First frame image path
        last_frame: Last frame image path
        reference_images: Reference image path list
        draft_task_id: Draft task ID

    Returns:
        content array
    """
    content = []

    # Text prompt
    if prompt:
        if len(prompt) > 500:
            print(f"Warning: Prompt exceeds 500 characters, truncating...")
            prompt = prompt[:500]
        content.append({"type": "text", "text": prompt})

    # Draft task
    if draft_task_id:
        content.append({"type": "draft_task", "draft_task_id": draft_task_id})
        return content

    # Image input
    if image:
        image_data = read_image_file(image)
        content.append({"type": "image", "image_url": image_data, "role": "first_frame"})

    if last_frame:
        if not image:
            raise ValueError("--last-frame requires --image to be specified")
        image_data = read_image_file(last_frame)
        content.append({"type": "image", "image_url": image_data, "role": "last_frame"})

    if reference_images:
        for ref_image in reference_images:
            image_data = read_image_file(ref_image)
            content.append({"type": "image", "image_url": image_data, "role": "reference_image"})

    return content


def parse_bool(value: str) -> bool:
    """Parse boolean value"""
    if value.lower() in ("true", "1", "yes", "y", "on"):
        return True
    elif value.lower() in ("false", "0", "no", "n", "off", ""):
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def get_output_dir(output_dir: Optional[str]) -> Path:
    """
    Get output directory

    Args:
        output_dir: Specified output directory

    Returns:
        Path object
    """
    if output_dir:
        path = Path(output_dir)
    else:
        # Default use output folder in current directory
        path = Path.cwd() / "output"

    # Create directory
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_filename(task_id: str, prompt: Optional[str] = None) -> str:
    """
    Generate filename

    Args:
        task_id: Task ID
        prompt: Text prompt (used to generate filename)

    Returns:
        Filename
    """
    # Extract suffix part of task ID
    task_suffix = task_id.split("-")[-1]

    if prompt:
        import re
        clean_prompt = re.sub(r'[^\w-]', '_', prompt[:20])
        return f"{clean_prompt}_{task_suffix}.mp4"

    return f"video_{task_suffix}.mp4"


def download_video(url: str, output_path: Path):
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

    file_size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"Video saved: {output_path} ({file_size_mb:.2f} MB)")


def poll_callback(task):
    """Poll callback function"""
    if task.status == TaskStatus.RUNNING:
        print(f"\rRunning... (Task: {task.id.id[:8]}...)", end="", flush=True)
    elif task.status == TaskStatus.QUEUED:
        print(f"\rQueued... (Task: {task.id[:8]}...)", end="", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Create a video generation task using Seedance API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Text-to-video
  python create_video.py --prompt "A cute kitten yawning in the sunlight"

  # Text-to-video with auto-download
  python create_video.py --prompt "A cute kitten yawning in the sunlight" --auto-download

  # Image-to-video
  python create_video.py --prompt "Camera slowly zooms out" --image cat.jpg

  # First and last frame
  python create_video.py --prompt "Smooth transition" --image first.jpg --last-frame last.jpg

  # With custom parameters
  python create_video.py \\
    --prompt "Seaside sunset, cinematic feel" \\
    --resolution 1080p \\
    --ratio 21:9 \\
    --duration 8
        """
    )

    # Required parameters (unless using draft-task-id)
    parser.add_argument(
        "--prompt",
        type=str,
        help="Text prompt for video generation"
    )

    # Model parameters
    parser.add_argument(
        "--model",
        type=str,
        default="seedance-1-5-pro-251215",
        help="Model ID (default: seedance-1-5-pro-251215)"
    )

    # Image parameters
    parser.add_argument(
        "--image",
        type=str,
        help="Path to first frame image (image-to-video)"
    )
    parser.add_argument(
        "--last-frame",
        type=str,
        help="Path to last frame image (first and last frame mode)"
    )
    parser.add_argument(
        "--reference-images",
        type=str,
        help="Comma-separated paths to reference images (1-4 images)"
    )

    # Output parameters
    parser.add_argument(
        "--resolution",
        type=str,
        choices=["480p", "720p", "1080p"],
        default="720p",
        help="Video resolution (default: 720p)"
    )
    parser.add_argument(
        "--ratio",
        type=str,
        choices=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"],
        default="16:9",
        help="Aspect ratio (default: 16:9)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=5,
        help="Video duration in seconds, 2-12 or -1 for auto (default: 5)"
    )

    # Advanced parameters
    parser.add.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--watermark",
        type=str,
        default="false",
        help="Include watermark (true/false, default: false)"
    )
    parser.add_argument(
        "--camera-fixed",
        type=str,
        default="false",
        help="Fix camera position (true/false, default: false)"
    )
    parser.add_argument(
        "--generate-audio",
        type=str,
        default="false",
        help="Generate audio (Seedance 1.5 pro only, true/false, default: false)"
    )
    parser.add_argument(
        "--draft",
        type=str,
        default="false",
        help="Generate draft preview (Seedance 1.5 pro only, true/false, default: false)"
    )
    parser.add_argument(
        "--draft-task-id",
        type=str,
        help="Generate final video from draft task ID"
    )
    parser.add_argument(
        "--service",
        type=str,
        choices=["default", "flex"],
        default="default",
        help="Service tier: default (online) or flex (offline, cheaper)"
    )
    parser.add_argument(
        "--return-last-frame",
        type=str,
        default="false",
        help="Return last frame image (true/false, default: false)"
    )

    # Authentication
    parser.add_argument(
        "--api-key",
        type=str,
        help="Override API Key (overrides ARK_API_KEY env variable)"
    )

    # Watch and download parameters
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch task until completion"
    )
    parser.add_argument(
        "--auto-download",
        action="store_true",
        help="Automatically download video after completion (implies --watch)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for downloaded videos (default: ./output)"
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between polls when watching (default: 5)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout in seconds when watching (default: 600)"
    )

    # Output format
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON"
    )

    args = parser.parse_args()

    # Validate parameters
    if args.draft_task_id:
        if args.prompt or args.image:
            parser.error("--draft-task-id cannot be used with --prompt or --image")
    else:
        if not args.prompt and not args.image:
            parser.error("--prompt or --image is required (unless using --draft-task-id)")

    if args.last_frame and not args.image:
        parser.error("--last-frame requires --image to be specified")

    if args.duration != -1 and (args.duration < 2 or args.duration > 12):
        parser.error("--duration must be between 2 and 12, or -1 for auto")

    # auto-download implies watch
    if args.auto_download:
        args.watch = True

    # Parse reference images
    reference_images = None
    if args.reference_images:
        reference_images = [p.strip() for p in args.reference_images.split(",")]
        if len(reference_images) > 4:
            parser.error("--reference-images supports maximum 4 images")

    # Build content array
    try:
        content = build_content_array(
            prompt=args.prompt,
            image=args.image,
            last_frame=args.last_frame,
            reference_images=reference_images,
            draft_task_id=args.draft_task_id
        )
    except Exception as e:
        print(f"Error processing images: {e}", file=sys.stderr)
        sys.exit(1)

    # Build request payload
    payload = {
        "model": args.model,
        "content": content,
        "resolution": args.resolution,
        "ratio": args.ratio,
        "duration": args.duration,
        "watermark": parse_bool(args.watermark),
        "service_tier": args.service,
        "return_last_frame": parse_bool(args.return_last_frame)
    }

    # Add optional parameters
    if args.seed is not None:
        payload["seed"] = args.seed

    if parse_bool(args.camera_fixed):
        payload["camera_fixed"] = True

    if parse_bool(args.generate_audio):
        payload["generate_audio"] = True

    if parse_bool(args.draft):
        payload["draft"] = True

    # Create client and send request
    try:
        client = SeedanceClient(api_key=args.api_key)

        # Create task
        task = client.create_task(payload)

        # Output creation result
        if args.json:
            import json
            result = {
                "id": task.id,
                "status": task.status.value,
                "model": task.model,
                "created_at": task.created_at,
                "resolution": task.resolution,
                "ratio": task.ratio,
                "duration": task.duration
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("Task created successfully!")
            print(f"   Task ID: {task.id}")
            print(f"   Status: {task.status.value}")
            print(f"   Model: {task.model}")
            print(f"   Created at: {task.created_at}")
            if task.resolution:
                print(f"   Resolution: {task.resolution}")
            if task.ratio:
                print(f"   Ratio: {task.ratio}")
            if task.duration:
                print(f"   Duration: {task.duration}s")

        # Watch mode
        if args.watch:
            print(f"\nWatching task: {task.id}")
            print(f"   Poll interval: {args.poll_interval}s, Timeout: {args.timeout}s")
            print()

            task = client.wait_for_completion(
                task_id=task.id,
                poll_interval=args.poll_interval,
                timeout=args.timeout,
                callback=poll_callback
            )

            # Clear progress display
            print("\r" + " " * 60 + "\r", end="", flush=True)

            # Output final status
            status_emoji = {
                TaskStatus.SUCCEEDED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.EXPIRED: "⏰",
                TaskStatus.CANCELLED: "🚫"
            }
            emoji = status_emoji.get(task.status, "❓")

            print(f"{emoji} Task completed!")
            print(f"   Status: {task.status.value}")
            if task.status == TaskStatus.FAILED and task.error_message:
                print(f"   Error: {task.error_message}")

            # Show success info
            if task.status == TaskStatus.SUCCEEDED:
                if task.usage:
                    input_tokens = task.usage.get("input_tokens", 0)
                    output_tokens = task.usage.get("output_tokens", 0)
                    print(f"   Usage: {input_tokens} input + {output_tokens} output tokens")

                # Auto download
                if task.video_url and args.auto_download:
                    output_dir = get_output_dir(args.output_dir)
                    filename = generate_filename(task.id, args.prompt)
                    output_path = output_dir / filename
                    download_video(task.video_url, output_path)
                elif task.video_url:
                    print(f"\nVideo URL: {task.video_url}")
                    print("   (URL valid for 24 hours)")

    except InvalidRequestError as e:
        print(f"API Error: {e}", file=sys.stderr)
        if e.response:
            print(f"   Details: {e.response}", file=sys.stderr)
        sys.exit(1)
    except TimeoutError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
