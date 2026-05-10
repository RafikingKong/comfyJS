# Architecture

## Core insight: filesystem is the state store

Everything about who-owns-what is encoded as filesystem operations. No database, no Redis, no in-memory state. This makes the system trivially debuggable (look at the folders) and trivially scalable to multi-instance (separate ComfyUI processes share filesystem state).

## Folder layout

```
<base_dir>/
├── needs_edit/         shared FIFO queue
├── in_progress/
│   ├── chain_1/        per-chain workspace, max 1 file at a time
│   ├── chain_2/
│   └── ...
├── processed/          source files after approve (audit trail)
└── approved/           final approved deliveries
```

## Claim pattern

When a chain's `LoadStaticAndCritique` runs:

1. Look in `in_progress/chain_<N>/`
2. If non-empty → return that file (chain still working on its claim)
3. If empty → atomically move first file from `needs_edit/` to `in_progress/chain_<N>/`, then return it

Atomic file moves on the same filesystem are race-free at OS level. Multiple ComfyUI instances can claim from `needs_edit/` concurrently — only one wins per file.

## Approve pattern

When `SaveOnApprove` runs with `approve=true`:

1. Read `<staging>/chain_<N>/<stem>_latest.jpg` (the most recent iteration's output)
2. Copy to `approved/<stem>.jpg`
3. Move source files (image + JSON sidecar) from `in_progress/chain_<N>/` to `processed/`
4. Clean up staging file

Result: `in_progress/chain_<N>/` is now empty → next `PREVIEW STATIC` claims fresh from `needs_edit/` → queue advances.

## Sidecar JSON schema

Each static in `needs_edit/` has a paired `<stem>.json` sidecar:

```json
{
    "kunde_id": "kunde_a",
    "static_id": "static_001",
    "kunde_navn": "Brand Name",
    "critique": "Plain client feedback in any language",
    "drive_folder_id": "1abc...",
    "monday_item_id": "9876543210",
    "submitted_at": "2026-05-08T10:00:00Z",
    "iteration_number": 1
}
```

Only `critique` is needed for the editor canvas. Other fields are for downstream automation (n8n outbound updating Monday/Drive).

## JS isolation logic

`web/one_click_approve.js` injects three buttons on canvas (PREVIEW STATIC, RUN ITERATION, APPROVE & ADVANCE) and handles execution isolation via connected-component analysis:

1. From the clicked node, walk both upstream and downstream links to find all nodes in the same chain
2. For RUN ITERATION: mute everything OUTSIDE the chain
3. For PREVIEW STATIC: same plus mute image generators + saves INSIDE the chain (don't generate, just load metadata)
4. For APPROVE & ADVANCE: mute image generators + SaveStaging in chain, set approve=true, queue prompt, then queue auto-preview prompt with approve=false

ComfyUI takes a snapshot of muted state at queue-time. State is reset in JS finally-block immediately after queueing — backend processes the snapshotted prompts sequentially.

## Single-prompt vs multi-prompt parallelism

- ComfyUI's prompt queue is sequential. Two queued prompts run one after the other.
- WITHIN a single prompt, ComfyUI Partner Nodes can fire concurrent API calls.
- Our per-chain RUN ITERATION creates separate prompts → sequential execution.
- For true parallel chains: either fire all chains in one prompt (loses per-chain control) or use multi-instance ComfyUI (each chain runs in its own ComfyUI process).

See `docs/ROADMAP.md` for the multi-instance plan.