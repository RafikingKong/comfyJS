# HANDOFF: comfyJS / juststatics

Snapshot of progress for context-handoff between Claude sessions or accounts.
Last updated: 2026-05-10

## Project in one sentence

Queue-based static editor for ComfyUI using image generators (Nano Banana 2 / Gemini 3 Pro Image), targeting 50-500 ad edits per week with 5-20 prompt iterations each.

## What is live

| Component | Where | Status |
|---|---|---|
| **Public GitHub repo** | github.com/RafikingKong/comfyJS | Pushed, current as of last commit |
| **Linode VPS** | 139.162.152.35 (Frankfurt, Ubuntu 24.04, 4GB) | Running, $24/mo on $100 trial credit |
| **4 ComfyUI instances** | Linode ports 8001-8004 (systemd services `comfyui-chain-1..4`) | Running, --cpu mode |
| **Firewall (ufw)** | Locked to laptop IP 5.103.106.12 for ports 8001-8004 | Active |
| **Custom nodes** | `/opt/ComfyUI/custom_nodes/juststatics_nodes` (symlinked to `/opt/juststatics`) | Loaded |
| **Folder structure** | `/opt/juststatics-comfy/{needs_edit, in_progress/chain_1..4, processed, approved}` | Created |
| **Test data** | Uploaded to `/opt/juststatics-comfy/needs_edit/` via WinSCP | Present |
| **Local dev mirror** | `C:\Users\numre\Documents\ComfyUI\custom_nodes\juststatics_nodes\` (Windows ComfyUI Desktop) | Used for active dev |
| **Local repo** | `C:\Users\numre\Documents\juststatics\` | Tracks GitHub remote |

## Architecture decisions made (and why)

1. **Folder-based queue with claim pattern** — needs_edit/ is shared queue, each chain claims to in_progress/chain_<N>/. Filesystem is the state store. No DB.
2. **Chain isolation via JS connected-component analysis** — clicking RUN ITERATION on chain N mutes everything outside chain N's connected component before queueing.
3. **Multi-instance ComfyUI for true parallelism** — single ComfyUI processes prompts sequentially; 4 separate processes give per-chain parallelism without architectural rewrite.
4. **Hardcoded paths in nodes.py via config file** — `juststatics_config.json` next to nodes.py. Eliminated widget-shift bugs from Windows ComfyUI Desktop.
5. **Mock generator first, real NB2 second** — validate workflow mechanic without API cost. Mock node draws yellow band overlay so output is visibly different from input.
6. **Public repo (not private)** — saved having to set up GitHub Personal Access Tokens for clone on Linode.
7. **Linode over DigitalOcean** — DO signup failed for Peter; Linode succeeded with $100/60 day credit.
8. **--cpu flag on ComfyUI** — Linode has no GPU. NB2 is remote API, no compute needed locally. Saves overhead.
9. **WinSCP for file management** — Windows-native SFTP client with image previews. Used to upload test data to Linode and verify queue/processed/approved folders.
10. **No Drive integration yet** — Peter is moving away from Drive for unrelated reasons. Replace with R2 / S3 / direct API later if needed.

## Editor flow (the editor's daily UX)

```
PREVIEW STATIC  ->  RUN ITERATION  ->  RUN ITERATION  ->  ...  ->  APPROVE & ADVANCE
   (free)           (NB2 cost)          (NB2 cost)                    (free, instant)
```

- PREVIEW STATIC on LoadStatic node: claims next from `needs_edit/`, displays image + critique + customer name. No image generation.
- RUN ITERATION on SaveStaging node: fires the chain's image generator only. Uses connected-component analysis to mute other chains.
- APPROVE & ADVANCE on SaveOnApprove node: reads staging file from disk, copies to `approved/`, moves source from `in_progress/` to `processed/`, then auto-queues a follow-up prompt that loads the next static. Editor sees next static + critique immediately.

## Active blockers (next session priorities)

1. **Mock yellow band not rendering on Linode**
   - On Linode, RUN ITERATION fires Mock but output looks unchanged (no yellow overlay band visible)
   - Last action before handoff: ask Peter to `git pull` in `/opt/juststatics` and `systemctl restart comfyui-chain-{1..4}`
   - Diagnostic if still broken: `grep -A 1 "draw.rectangle" /opt/ComfyUI/custom_nodes/juststatics_nodes/nodes.py`
   - Possible cause: workflow's INPUT preview being mistaken for OUTPUT, or wiring issue, or older nodes.py version cached

2. **NB2 not configured on Linode yet**
   - Linode has only Mock + ComfyUI-Custom-Scripts custom nodes
   - To enable real NB2: clone gokayfem/ComfyUI-fal-API into custom_nodes (requires fal.ai key in config.ini) OR use ComfyUI Partner Node (requires ComfyUI account credits, billing different from Sub-Produce's fal.ai key)
   - Decision pending which path

3. **Workflow JSONs misnamed in repo**
   - `v10-single-chain-mock.json` actually uses NanoBanana2_fal (gokayfem) not MockImageGenerator
   - Same for `v11-five-chains-mock.json` and `v11-two-chains-mock.json`
   - Fix: rebuild these JSONs to actually use MockImageGenerator, push to repo
   - Workaround: editor manually swaps NanoBanana2_fal -> MockImageGenerator on canvas after loading

## Open architecture questions

- **Storage backend for v2 n8n integration**: Drive was the original plan but Peter is moving away. Alternatives: Cloudflare R2 (S3-compatible, cheap), AWS S3, OneDrive, Dropbox. Not yet decided.
- **Authentication for ComfyUI on Linode**: currently relies on ufw IP-restriction. If editors access from multiple locations, need either reverse-proxy auth (nginx + basic auth, Caddy + auth), Tailscale VPN, or Cloudflare Tunnel.

## File / path inventory

### On Linode (139.162.152.35)
- ComfyUI: `/opt/ComfyUI/`
- Python venv: `/opt/ComfyUI/.venv/`
- Custom nodes pack: `/opt/juststatics/` (git-clone of repo)
- Symlinked into ComfyUI: `/opt/ComfyUI/custom_nodes/juststatics_nodes -> /opt/juststatics/custom_nodes/juststatics_nodes`
- Config: `/opt/ComfyUI/custom_nodes/juststatics_nodes/juststatics_config.json` (sets `base_dir: /opt/juststatics-comfy`)
- Queue base: `/opt/juststatics-comfy/`
- Systemd services: `/etc/systemd/system/comfyui-chain-{1..4}.service`

### On Peter's Windows laptop
- Local ComfyUI Desktop user data: `C:\Users\numre\Documents\ComfyUI\`
- Active dev custom nodes: `C:\Users\numre\Documents\ComfyUI\custom_nodes\juststatics_nodes\`
- Local repo clone: `C:\Users\numre\Documents\juststatics\`
- Local queue (Windows): `C:\juststatics-comfy\`
- Test images source: `C:\Users\numre\Desktop\Claude\Test images\`
- SSH key: `C:\Users\numre\.ssh\id_ed25519_do` (private), `id_ed25519_do.pub`, `id_ed25519_do.ppk` (WinSCP)
- WinSCP saved site: "Linode juststatics" (or similar) pointing at 139.162.152.35

## Access / credentials reference

- GitHub account: RafikingKong (Daniel Madsen)
- gh CLI: authed and logged in
- Linode root password: set during droplet creation, used for console-fallback access (SSH key is primary)
- fal.ai API key: lives in n8n's Sub-Produce workflow credentials (NOT in this repo). Reuse same key for gokayfem fal-API node when enabling NB2 on Linode.
- ComfyUI account credits: not yet purchased, needed if going Partner Node route for NB2 on Linode

## Repo structure

```
comfyJS/
├── README.md
├── LICENSE (MIT)
├── .gitignore
├── HANDOFF.md (this file)
├── custom_nodes/juststatics_nodes/
│   ├── __init__.py
│   ├── nodes.py (LoadStaticAndCritique, MockImageGenerator, SaveStaging, SaveOnApprove)
│   ├── juststatics_config.example.json
│   └── web/one_click_approve.js (PREVIEW/RUN/APPROVE buttons + chain isolation)
├── workflows/
│   ├── v10-single-chain-mock.json (MIS-NAMED: actually uses NanoBanana2_fal)
│   ├── v11-five-chains-mock.json (MIS-NAMED: actually uses NanoBanana2_fal)
│   ├── v11-two-chains-mock.json (MIS-NAMED: actually uses NanoBanana2_fal)
│   ├── v11-five-chains-fal-gokayfem.json (correct: gokayfem fal-API)
│   └── v11-five-chains-partner-node.json (correct: GeminiNanoBanana2 Partner Node)
├── scripts/
│   ├── setup-folders.ps1
│   ├── generate-test-data.ps1
│   ├── open-comfy-quad.ps1
│   └── start-instances.ps1
└── docs/
    ├── ARCHITECTURE.md
    ├── EDITOR_FLOW.md
    └── ROADMAP.md
```

## How to verify everything is still running (sanity check)

```bash
# SSH to Linode
ssh -i ~/.ssh/id_ed25519_do root@139.162.152.35

# Check all 4 services
systemctl status comfyui-chain-{1..4} --no-pager -l | head -40

# Check ports listening
ss -tlnp | grep -E ":(8001|8002|8003|8004)"

# Check juststatics symlink and config
ls -la /opt/ComfyUI/custom_nodes/juststatics_nodes/
cat /opt/ComfyUI/custom_nodes/juststatics_nodes/juststatics_config.json

# Check folder structure
ls /opt/juststatics-comfy/

# Pull latest repo changes
cd /opt/juststatics && git pull
systemctl restart comfyui-chain-{1..4}
```

```powershell
# From Windows laptop, verify firewall lets you in
curl http://139.162.152.35:8001/object_info | Select-Object -First 100
```

## Next concrete steps when resuming

1. Resolve Mock yellow-band issue (verify nodes.py version on Linode, verify wiring on canvas)
2. Validate parallel execution across 4 instances with a real timing test (Mock is instant so 4x parallel vs 4x sequential is invisible — needs NB2 with real latency to confirm)
3. Decide on NB2 route (gokayfem reusing fal.ai key vs Partner Node with new ComfyUI credits)
4. Configure NB2 on Linode and validate first real edit end-to-end
5. Fix mis-named workflow JSONs in repo
6. Add HANDOFF.md to repo (this file)

## How to brief the next Claude session

Tell new Claude:
1. "Read C:\Users\numre\Desktop\Claude\CLAUDE.md for project context."
2. "Read https://github.com/RafikingKong/comfyJS/blob/main/HANDOFF.md for current state."
3. "Last blocker before pause: Mock yellow band not rendering on Linode. We were debugging if it was a stale nodes.py version (git pull pending) or canvas wiring."