# Image and video models

Image and video models run on their own pod, next to the chat pod. You can run one
of them or both. Each pod bills separately.

| | Chat pod | Image and video pod |
|---|---|---|
| Profiles | models with `chat`, `code`, `tools`, `vision` | models with `image` or `video` |
| Runtime | vLLM, llama.cpp, Bonsai | `diffusers` |
| Pod name | `gpuharbor-model` | `gpuharbor-media` |
| State file | `/data/state.json` | `/data/state-media.json` |

Starting a profile picks its pod automatically. Stop and delete act on the pod of the
selected profile. The idle timer runs per pod, and a pod that is rendering is not
stopped for being idle.

## Profiles

| Profile | Model | Pipeline | Volume |
|---|---|---|---|
| `wan22-ti2v-5b-video` | `Wan-AI/Wan2.2-TI2V-5B-Diffusers` | `wan22-ti2v` | 80 GB |
| `qwen-image-20b` | `Qwen/Qwen-Image` | `qwen-image` | 120 GB |

Both are `experimental` and `verified: false`: they have not run on a GPU yet. VRAM,
speed and cost per clip are not measured. Qwen-Image runs with CPU offload, so it is
slower than it would be with more VRAM.

The pipeline is chosen from a fixed list in `runtime/media_server.py`. A profile
cannot name an arbitrary class or run code from a model repository.

## API

Same base URL and inference token as the chat models.

```bash
# Image (OpenAI images API, base64 result)
curl -sk $BASE/v1/images/generations -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"model":"image","prompt":"a harbor at dawn","size":"1328x1328"}'

# Video is a job: create, poll, download
curl -sk $BASE/v1/videos -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"model":"video","prompt":"waves hitting a pier","seconds":5,"size":"1280x704"}'
curl -sk $BASE/v1/videos/video_ID -H "Authorization: Bearer $TOKEN"
curl -sk $BASE/v1/videos/video_ID/content -H "Authorization: Bearer $TOKEN" -o clip.mp4
```

Limits: sizes must be multiples of 32, video is at most 10 s at 24 fps and 1280x720
pixels, images at most 1664x1664. Optional fields: `seed`, `steps`.

## Apps

- **Open WebUI** uses the image pod for image generation (served name `image`),
  set up by `compose.openwebui.yml`. Video is not part of Open WebUI.
- **OpenHands** and **PI** only list chat models. Image and video profiles are left out
  on purpose.

## Runtime image

The `diffusers` image (about 6.4 GB, tag `0.1.7`) is referenced by digest in
`RUNTIME_IMAGE_DIFFUSERS` in `.env.example`. To build it yourself:

```bash
docker build -f runtime/Dockerfile.diffusers -t gpuharbor-runtime:diffusers-local runtime
./scripts/publish-runtime-images --only diffusers
# then set RUNTIME_IMAGE_DIFFUSERS=ghcr.io/<owner>/gpuharbor-runtime-diffusers@sha256:...
```

## Not covered yet

- Image-to-video input.
- Content filtering: the pipelines ship without a safety checker. Whether a model
  refuses or renders certain content is a property of its weights; GPUHarbor does not
  add or remove filters.
