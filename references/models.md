# Available Seedance Models

Based on [BytePlus API Documentation](byteplusAPI.md), these are the available models:

## Seedance 1.5 Pro

| Model ID | Description | Features |
|-----------|-------------|----------|
| `seedance-1-5-pro-251215` | Seedance 1.5 Pro | Video with Audio, Draft mode, First+Last Frame, First Frame, Text-to-Video |

## Seedance 1.0 Series

| Model ID | Description | Features |
|-----------|-------------|----------|
| `seedance-1-0-pro-250528` | Seedance 1.0 Pro | First+Last Frame, First Frame, Text-to-Video |
| `seedance-1-0-pro-fast-251015` | Seedance 1.0 Pro Fast | First Frame, Text-to-Video |
| `seedance-1-0-lite-t2v-250428` | Seedance 1.0 Lite (Text-to-Video) | Text-to-Video |
| `seedance-1-0-lite-i2v-250428` | Seedance 1.0 Lite (Image-to-Video) | Reference Images, First+Last Frame, First Frame |

## Feature Support Summary

| Feature | 1.5 Pro | 1.0 Pro | 1.0 Pro Fast | 1.0 Lite T2V | 1.0 Lite I2V |
|---------|---------|--------|------------|-------------|-------------|
| Text-to-Video | ✅ | ✅ | ✅ | ✅ | ❌ |
| Image-to-Video (First Frame) | ✅ | ✅ | ✅ | ❌ | ✅ |
| Image-to-Video (First+Last Frame) | ✅ | ✅ | ❌ | ❌ | ✅ |
| Image-to-Video (Reference Images) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Video with Audio | ✅ | ❌ | ❌ | ❌ | ❌ |
| Draft Mode | ✅ | ❌ | ❌ | ❌ | ❌ |
| service_tier Parameter | ✅ | ✅ | ✅ | ❌ | ❌ |

## Notes

- `service_tier` parameter is NOT supported by Seedance 1.0 Lite models
- For models that don't support `service_tier`, client automatically removes this parameter
- Video URLs are valid for 24 hours after generation
