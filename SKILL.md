---
name: byteplus-seedance
description: |
  Create, query, and manage video generation tasks using BytePlus Seedance API.
  Supports text-to-video (T2V), image-to-video (I2V), and automatic video download.

  Use this skill when users need to:
  - Generate videos from text prompts
  - Generate videos from images
  - Monitor video generation tasks
  - Download generated videos
  - List/cancel video generation tasks

  Available models:
  - seedance-1-5-pro-251215: Seedance 1.5 Pro with video/audio
  - seedance-1-0-pro-250528: Seedance 1.0 Pro
  - seedance-1-0-pro-fast-251015: Seedance 1.0 Pro Fast
  - seedance-1-0-lite-t2v-250428: Seedance 1.0 Lite (Text-to-Video)
  - seedance-1-0-lite-i2v-250428: Seedance 1.0 Lite (Image-to-Video)
---

## Setup

Set API Key via environment variable:
```bash
export ARK_API_KEY=your_api_key_here
```

Or create `.env` file:
```
ARK_API_KEY=your_api_key_here
```

## Workflow

The skill uses Python scripts located in `scripts/` directory. Each script must be run from any working directory - they will automatically locate the `seedance_client.py` module.

### Creating Videos

Use `create_video.py` to generate videos:

```bash
# Text-to-video with auto-download
cd /Users/bytedance/.claude/skills/byteplus-seedance/scripts
python3 create_video.py --prompt "A cute kitten playing" --auto-download

# Image-to-video
python3 create_video.py --prompt "Camera zooms out" --image path/to/image.jpg --auto-download

# First and last frame mode
python3 create_video.py --prompt "Smooth transition" --image first.jpg --last-frame last.jpg --auto-download

# High-resolution cinematic video
python3 create_video.py --prompt "Drone shot over ocean waves at sunset" --resolution 1080p --ratio 21:9 --duration 8 --auto-download
```

### Querying Tasks

Use `query_video.py` to check task status:

```bash
# Query single task
python3 query_video.py <task_id>

# Watch until completion
python3 query_video.py --watch <task_id>

# Watch and download
python3 query_video.py --watch <task_id> --download output.mp4
```

### Listing Tasks

Use `list_videos.py` to list and filter tasks:

```bash
# List all tasks
python3 list_videos.py

# Filter by status
python3 list_videos.py --status succeeded

# Filter by model
python3 list_videos.py --model seedance-1-5-pro-251215

# Pagination
python3 list_videos.py --page-num 2 --page-size 20
```

### Canceling Tasks

Use `cancel_video.py` to cancel or delete tasks:

```bash
python3 cancel_video.py <task_id>
```

## Parameters

### Common Parameters

| Parameter | Values | Default |
|-----------|--------|---------|
| `--model` | Model ID | seedance-1-5-pro-251215 |
| `--resolution` | 480p, 720p, 1080p | 720p |
| `--ratio` | 16:9, 4:3, 1:1, 3:4, 9:16, 21:9, adaptive | 16:9 |
| `--duration` | 2-12 or -1 for auto | 5 |
| `--watermark` | true, false | false |

### Advanced Parameters

| Parameter | Description |
|-----------|-------------|
| `--seed` | Random seed for reproducibility |
| `--camera-fixed` | Fix camera position (true/false) |
| `--generate-audio` | Generate audio (Seedance 1.5 pro only) |
| `--draft` | Generate draft preview (Seedance 1.5 pro only) |
| `--draft-task-id` | Generate final video from draft task ID |
| `--service` | Service tier: default (online) or flex (offline, cheaper) |
| `--return-last-frame` | Return last frame image (true/false) |

### Watch/Download Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--watch` | Watch task until completion | - |
| `--auto-download` | Auto download after completion | - |
| `--output-dir` | Output directory for downloads | ./output |
| `--poll-interval` | Poll interval in seconds | 5 |
| `--timeout` | Timeout in seconds | 600 |

## Notes

- Video URLs are valid for 24 hours after generation
- Default output directory is `./output` (created automatically)
- Use `--json` flag for machine-readable output
- All scripts support `--api-key` parameter to override environment variable

## References

For detailed API documentation, see [references/byteplusAPI.md](references/byteplusAPI.md).
