# Roadmap

## v1.0 (DONE)

- Single-chain workflow with PREVIEW STATIC + RUN ITERATION + APPROVE & ADVANCE
- Folder-based queue with claim pattern
- Sidecar JSON for client critique
- Mock generator for cost-free testing
- gokayfem fal.ai integration
- ComfyUI Partner Node integration

## v1.1 (CURRENT)

- 5-chain canvas layouts
- Per-chain claim isolation via `in_progress/chain_<N>/`
- Per-chain staging via `staging/chain_<N>/`
- JS connected-component muting for chain isolation
- Workflow JSONs for Mock, gokayfem fal.ai, Partner Node variants

## v1.5 (NEXT)

**Cloud migration + true multi-instance parallelism**

- Move ComfyUI to a cloud VPS (Hetzner CPX31 or similar, CPU-only since image generation is remote API)
- Mount Google Drive via rclone with service account auth → editor's `needs_edit/` and `approved/` folders are Drive-backed automatically
- Run 5 ComfyUI processes on ports 8001-8005 (one per chain)
- Each ComfyUI instance handles one chain via `chain_id` widget
- Editor opens 5 Chrome app-mode windows in screen quadrants pointing at different ports
- True per-chain parallelism: clicking RUN ITERATION on chain 1 in instance 1 doesn't block chain 2 in instance 2

## v2 (FUTURE)

**n8n integration**

Inbound (Monday → queue):
- Trigger on Monday status change to "needs_edit"
- Pull static URL + client_comment + kunde_id from item
- Download static, write image + sidecar JSON to Drive's `needs_edit/` folder
- rclone-mount on ComfyUI VPS sees new files → editor's queue updates

Outbound (approved → client delivery):
- Watcher on `approved/` folder picks up new files
- Match `<stem>` to Monday item via sidecar metadata
- Upload approved image to client's Drive folder (drive_folder_id from sidecar)
- Update Monday item status to "edit_done"
- Slack notify both editor and client

## Future ideas (not committed)

- **Keyboard shortcuts** for PREVIEW/RUN/APPROVE (faster editor flow)
- **Sidebar queue stats panel** (shows backlog and per-chain status without leaving canvas)
- **Auto seed-locking** for reproducible approve (no variance between iteration N's preview and approved output)
- **Brand DNA injection** for context-aware first prompts
- **Past approved gallery** per customer for editor reference