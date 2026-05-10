import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "JustStatics.OneClickApprove",

    async nodeCreated(node) {
        if (node.comfyClass === "LoadStaticAndCritique") {
            node.addWidget("button", "PREVIEW STATIC", null, async () => {
                await runPreviewStatic(node);
            });
        }
        if (node.comfyClass === "SaveStaging") {
            node.addWidget("button", "RUN ITERATION", null, async () => {
                await runChainIteration(node);
            });
        }
        if (node.comfyClass === "SaveOnApprove") {
            node.addWidget("button", "APPROVE & ADVANCE", null, async () => {
                await runApprovalFlow(node);
            });
        }
    }
});

function isImageGenerator(node) {
    const t = node.comfyClass || node.type || "";
    return t.includes("NanoBanana") || t === "MockImageGenerator";
}

function getChainComponent(startNode) {
    const graph = app.graph;
    const visited = new Set();
    const queue = [startNode];
    while (queue.length) {
        const n = queue.shift();
        if (visited.has(n.id)) continue;
        visited.add(n.id);
        for (const input of n.inputs || []) {
            if (input.link != null) {
                const link = graph.links?.[input.link];
                if (link) {
                    const src = graph.getNodeById(link.origin_id);
                    if (src) queue.push(src);
                }
            }
        }
        for (const output of n.outputs || []) {
            if (output.links) {
                for (const linkId of output.links) {
                    const link = graph.links?.[linkId];
                    if (link) {
                        const dest = graph.getNodeById(link.target_id);
                        if (dest) queue.push(dest);
                    }
                }
            }
        }
    }
    return visited;
}

function forceAllApproveFalse() {
    const graph = app.graph;
    const approveNodes = graph._nodes.filter(n => n.comfyClass === "SaveOnApprove");
    for (const an of approveNodes) {
        const w = an.widgets.find(w => w.name === "approve");
        if (w && w.value !== false) {
            w.value = false;
            if (typeof w.callback === "function") w.callback(false);
        }
    }
    graph.setDirtyCanvas(true, true);
}

function isOutputPreview(n, graph) {
    const t = n.comfyClass || n.type || "";
    if (t !== "PreviewImage") return false;
    const inputLink = n.inputs?.[0]?.link;
    if (inputLink == null) return false;
    const link = graph.links?.[inputLink];
    if (!link) return false;
    const sourceNode = graph.getNodeById(link.origin_id);
    return sourceNode && isImageGenerator(sourceNode);
}

async function runPreviewStatic(loadStaticNode) {
    const graph = app.graph;
    forceAllApproveFalse();
    const myChain = getChainComponent(loadStaticNode);
    const nodesToMute = graph._nodes.filter(n => {
        if (!myChain.has(n.id)) return true;
        const t = n.comfyClass || n.type || "";
        return isImageGenerator(n) || t === "SaveStaging" || t === "SaveOnApprove" || isOutputPreview(n, graph);
    });
    const originalModes = nodesToMute.map(n => n.mode);
    try {
        nodesToMute.forEach(n => { n.mode = 2; });
        graph.setDirtyCanvas(true, true);
        await app.queuePrompt(0);
        showToast("Preview loaded for this chain");
    } catch (err) {
        showToast("Preview failed: " + err.message, "error");
        console.error(err);
    } finally {
        nodesToMute.forEach((n, i) => { n.mode = originalModes[i]; });
        graph.setDirtyCanvas(true, true);
    }
}

async function runChainIteration(saveStagingNode) {
    const graph = app.graph;
    forceAllApproveFalse();
    const myChain = getChainComponent(saveStagingNode);
    const nodesToMute = graph._nodes.filter(n => !myChain.has(n.id));
    const originalModes = nodesToMute.map(n => n.mode);
    try {
        nodesToMute.forEach(n => { n.mode = 2; });
        graph.setDirtyCanvas(true, true);
        await app.queuePrompt(0);
        showToast("Iteration queued for this chain");
    } catch (err) {
        showToast("Run failed: " + err.message, "error");
        console.error(err);
    } finally {
        nodesToMute.forEach((n, i) => { n.mode = originalModes[i]; });
        graph.setDirtyCanvas(true, true);
    }
}

async function runApprovalFlow(approveNode) {
    const graph = app.graph;
    const myChain = getChainComponent(approveNode);
    const nodesToMute = graph._nodes.filter(n => {
        if (!myChain.has(n.id)) return true;
        const t = n.comfyClass || n.type || "";
        return isImageGenerator(n) || t === "SaveStaging" || isOutputPreview(n, graph);
    });
    const approveWidget = approveNode.widgets.find(w => w.name === "approve");
    if (!approveWidget) {
        showToast("Approve widget not found", "error");
        return;
    }
    const originalModes = nodesToMute.map(n => n.mode);
    try {
        nodesToMute.forEach(n => { n.mode = 2; });
        approveWidget.value = true;
        if (typeof approveWidget.callback === "function") approveWidget.callback(true);
        graph.setDirtyCanvas(true, true);
        await app.queuePrompt(0);
        approveWidget.value = false;
        if (typeof approveWidget.callback === "function") approveWidget.callback(false);
        graph.setDirtyCanvas(true, true);
        await app.queuePrompt(0);
        showToast("Approved + next loaded for this chain");
    } catch (err) {
        showToast("Approve failed: " + err.message, "error");
        console.error(err);
    } finally {
        nodesToMute.forEach((n, i) => { n.mode = originalModes[i]; });
        approveWidget.value = false;
        if (typeof approveWidget.callback === "function") approveWidget.callback(false);
        graph.setDirtyCanvas(true, true);
    }
}

function showToast(text, type = "success") {
    const toast = document.createElement("div");
    toast.textContent = text;
    const bg = type === "error" ? "#e74c3c" : "#2ecc71";
    toast.style.cssText = `
        position: fixed;
        top: 60px;
        right: 20px;
        background: ${bg};
        color: white;
        padding: 14px 22px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        max-width: 400px;
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}