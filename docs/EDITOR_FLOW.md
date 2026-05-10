# Editor flow

## Single-chain (v1.0)

1. **Open ComfyUI canvas** — workflow loaded with one chain (LoadStatic + Image Generator + SaveStaging + SaveOnApprove + previews + ShowText for critique)

2. **Click PREVIEW STATIC on LoadStatic node**
   - Claims next file from `needs_edit/` to `in_progress/chain_1/`
   - Displays image in INPUT Preview
   - Shows critique text in KRITIK box
   - Shows customer name in KUNDE box
   - No image generation (cheap, instant)

3. **Read critique, type prompt on image generator node**
   - Editor uses critique as guidance, writes prompt in their own words

4. **Click RUN ITERATION on SaveStaging node**
   - Fires image generation API call (NB2 or Mock)
   - Output appears in OUTPUT Preview
   - Staging file written to disk

5. **Iterate steps 3-4** until output is good (5-20 times typical)

6. **Click APPROVE & ADVANCE on SaveOnApprove node**
   - Reads staging file (no re-generation)
   - Copies to `approved/`
   - Moves source from `in_progress/` to `processed/`
   - Auto-triggers a new PREVIEW STATIC for the next file in queue

## Multi-chain (v1.1)

Same as single-chain but 5 chains visible on canvas vertically. Each chain has its own `chain_id` (1-5) and own `in_progress/chain_<N>/` and `staging/chain_<N>/` folders.

Editor scrolls between chains. Per-chain operations are isolated — clicking on chain 1's buttons only affects chain 1.

Note: in single ComfyUI instance, RUN ITERATION clicks queue prompts sequentially. For true parallel iteration, see multi-instance setup in ROADMAP.md.

## Tips

- **MINIMAL thinking_level** during iteration → faster, cheaper. Switch to **HIGH** for the final approve-iteration if quality matters.
- **Lower resolution** (1K) during iteration, switch to 2K just before approve.
- **Keep prompts short** — the model resolves intent better from focused instructions than long paragraphs.
- **Approve iteration history is preserved** in `processed/` — you can pull old approved versions back for re-edits if client comes back.