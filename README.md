# juststatics

Queue-based static editor for ComfyUI using image generators (Nano Banana 2 / Gemini 3 Pro Image, or any compatible model).

Editor sits in front of ComfyUI canvas. A shared queue of statics-needing-edits flows in from `needs_edit/`. Each chain claims one static, the editor iterates with prompts, then approves to ship and auto-advance to the next.

## What it solves

Manual ad-static editing at volume (50-500 edits/week) where each static needs 5-20 prompt iterations. Higgsfield-style UX (canvas, prompt iteration, approve) without the import/export friction of switching apps.

## Features

- **Folder-based queue** — `needs_edit/` is the source of truth, files move out via filesystem ops
- **Per-chain claim** — each chain has its own `in_progress/chain_<N>/` workspace, no collisions
- **Sidecar critique** — `<filename>.json` next to each static carries client feedback into the canvas
- **3-button editor flow** — PREVIEW STATIC, RUN ITERATION, APPROVE & ADVANCE on canvas widgets
- **JS isolation** — clicking RUN ITERATION on chain N only fires that chain's image generator
- **Auto-advance on approve** — file moves to `processed/`, next claim happens on next PREVIEW
- **Multi-instance ready** — designed for running multiple ComfyUI processes for true parallelism (v1.5)

## Folder structure under base_dir

```
<base_dir>/
├── needs_edit/         shared queue (image + .json sidecar pairs)
├── in_progress/
│   ├── chain_1/        chain 1's currently-claimed work
│   ├── chain_2/
│   └── ...
├── processed/          source files after approve
└── approved/           final approved deliveries
```

## Custom nodes

- `LoadStaticAndCritique` — claims next from `needs_edit/`, returns image + critique + metadata
- `MockImageGenerator` — drop-in for testing without API cost (yellow text overlay)
- `SaveStaging` — writes per-chain staging file
- `SaveOnApprove` — reads staging, copies to `approved/`, moves source to `processed/`

## Install

1. Clone this repo
2. Copy `custom_nodes/juststatics_nodes/` into your ComfyUI's `custom_nodes/` folder
3. Optionally copy `juststatics_config.example.json` to `juststatics_config.json` and edit `base_dir`
4. Run `scripts/setup-folders.ps1` to create the folder structure
5. Restart ComfyUI
6. Drag-drop a workflow JSON from `workflows/` onto the canvas

## Image generators

Three workflow variants ship in `workflows/`:

- `*-mock.json` uses `MockImageGenerator` for testing (instant, no API)
- `*-fal-gokayfem.json` uses gokayfem's fal.ai wrapper (`NanoBanana2_fal`, requires fal.ai key)
- `*-partner-node.json` uses ComfyUI's official Partner Node (`GeminiNanoBanana2`, requires ComfyUI account credits)

Partner Node enables unlimited parallel API calls within a single prompt. Use it for batched runs.

## Editor flow

1. **PREVIEW STATIC** on a chain — claims next from queue, displays image + critique + customer name
2. Type prompt on the image generator node
3. **RUN ITERATION** — fires this chain only, output appears in chain's OUTPUT preview
4. Iterate prompt as needed
5. **APPROVE & ADVANCE** — saves output to `approved/`, moves source to `processed/`, auto-loads next static

See `docs/EDITOR_FLOW.md` for the detailed flow with screenshots.

## Roadmap

- v1.5: Cloud migration with rclone-mounted Drive, multi-instance for true parallel iteration
- v2: n8n integration for inbound (Monday → queue) and outbound (approved → client Drive)

See `docs/ROADMAP.md`.

## License

MIT