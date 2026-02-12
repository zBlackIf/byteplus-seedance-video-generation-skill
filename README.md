# BytePlus Seedance Video Generation Skill

A Claude skill for generating videos using the [BytePlus Seedance API](https://console.byteplus.com/ark/region:ark+ap-southeast-1/experience/vision).

## Features

- **Text-to-Video (T2V)**: Generate videos from text prompts
- **Image-to-Video (I2V)**: Generate videos from images with optional prompts
- **First & Last Frame**: Generate transitions between two images
- **Automatic Download**: Download generated videos automatically
- **Task Monitoring**: Watch task progress with real-time updates
- **Multi-Model Support**: Work with all Seedance models

## Supported Models

| Model | Description |
|-------|-------------|
| `seedance-1-5-pro-251215` | Seedance 1.5 Pro with video/audio support |
| `seedance-1-0-pro-250528` | Seedance 1.0 Pro |
| `seedance-1-0-pro-fast-251015` | Seedance 1.0 Pro Fast |
| `seedance-1-0-lite-t2v-250428` | Seedance 1.0 Lite (Text-to-Video) |
| `seedance-1-0-lite-i2v-250428` | Seedance 1.0 Lite (Image-to-Video) |
| `seedance-2-0-260128` | Seedance 2.0 |

## Installation

1. Download the [latest `.skill` file](./blob/main/byteplus-seedance.skill)
2. Install it in Claude Code

## Setup

Set your API key via environment variable:

```bash
export ARK_API_KEY=your_api_key_here
```

Or create a `.env` file:

```
ARK_API_KEY=your_api_key_here
```

To get an API key, visit the [BytePlus Console](https://console.byteplus.com/ark/region:ark+ap-southeast-1/apiKey).

## Usage

### Generate a Video

```bash
# Text-to-video
python3 create_video.py --prompt "A cute kitten playing in sunlight"

# Text-to-video with auto-download
python3 create_video.py --prompt "A cute kitten playing" --auto-download

# Image-to-video
python3 create_video.py --prompt "Camera slowly zooms out" --image cat.jpg --auto-download

# First and last frame mode
python3 create_video.py --prompt "Smooth transition" --image first.jpg --last-frame last.jpg --auto-download

# High-resolution cinematic video
python3 create_video.py \
  --prompt "Drone shot over ocean waves at sunset" \
  --resolution 1080p \
  --ratio 21:9 \
  --duration 8 \
  --auto-download
```

### Query Task Status

```bash
# Query single task
python3 query_video.py <task_id>

# Watch until completion
python3 query_video.py --watch <task_id>

# Watch and download
python3 query_video.py --watch <task_id> --download output.mp4
```

### List Tasks

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

### Cancel Task

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
| `--generate-audio` | Generate audio (Seedance 1.5 Pro only) |
| `--draft` | Generate draft preview (Seedance 1.5 Pro only) |
| `--draft-task-id` | Generate final video from draft task ID |
| `--service` | Service tier: default (online) or flex (offline, cheaper) |
| `--return-last-frame` | Return last frame image (true/false) |

## Notes

- Video URLs are valid for 24 hours after generation
- Default output directory is `./output` (created automatically)
- Use `--json` flag for machine-readable output
- All scripts support `--api-key` parameter to override environment variable

## License

This project is provided as-is for use with the Claude platform.

## Links

- [BytePlus Console](https://console.byteplus.com/ark/region:ark+ap-southeast-1/experience/vision)
- [API Documentation](./blob/main/references/byteplusAPI.md)
