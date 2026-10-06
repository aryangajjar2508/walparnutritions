// Walpar Formula OCR & Ingredient Extractor (Multi-Engine & Zero Price)

let appState = {
    image: null,
    imageSrc: null,
    currentFile: null,
    currentSample: null,
    ocrLines: [],
    ingredients: [],
    masterIngredients: [],
    showBoxes: true,
    activeEngine: "ollama"
};

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    initDragAndDrop();
    initFileInput();
    initClipboardPaste();
    loadMasterIngredients();
});

// Load Master Ingredients
async function loadMasterIngredients() {
    try {
        const res = await fetch("/api/ingredients");
        const data = await res.json();
        appState.masterIngredients = data.ingredients || [];
        renderModalIngredients(appState.masterIngredients);
        const countBadge = document.getElementById("search-count-badge");
        if (countBadge) {
            countBadge.innerText = `${appState.masterIngredients.length} Items`;
        }
    } catch (e) {
        console.error("Failed to load master ingredients:", e);
    }
}

// OCR Engine Selector Change
function onEngineChange() {
    const sel = document.getElementById("engine-select");
    appState.activeEngine = sel.value;
    
    const noteEl = document.getElementById("engine-note");
    if (appState.activeEngine === "ollama") {
        noteEl.innerText = "Walpar Neural Engine (Local Ollama Gemma 3): 100% private offline intelligence model built from local weights. Zero APIs, zero quota limits.";
    } else if (appState.activeEngine === "gemini") {
        noteEl.innerText = "Walpar Cloud Vision Engine: Cloud neural model backup.";
    } else if (appState.activeEngine === "rapidocr") {
        noteEl.innerText = "Walpar High-Speed Engine (Local ONNX): 100% offline local deep learning model. Ultra-fast table parsing.";
    } else if (appState.activeEngine === "easyocr") {
        noteEl.innerText = "Walpar Mobile Lens Engine (Local PyTorch): Optimized for mobile camera photos and rotated text.";
    } else if (appState.activeEngine === "paddleocr") {
        noteEl.innerText = "Walpar Layout Engine (Local PP-OCR): Comprehensive layout and textline orientation detection.";
    } else if (appState.activeEngine === "tesseract") {
        noteEl.innerText = "Walpar Standard Engine (Local Tesseract 5.5): Classical layout and document character recognizer.";
    } else if (appState.activeEngine === "ensemble") {
        noteEl.innerText = "Walpar Multi-Engine Fusion: Cross-verifies formula across multiple neural pipelines.";
    }

    // Show re-run button if image is already present
    if (appState.currentFile || appState.currentSample) {
        document.getElementById("re-run-box").classList.remove("hidden");
    }
}

// Re-run with currently selected engine
function reRunCurrentEngine() {
    if (appState.currentSample) {
        loadSample(appState.currentSample);
    } else if (appState.currentFile) {
        handleFileUpload(appState.currentFile);
    }
}

// Drag & Drop Handling
function initDragAndDrop() {
    const dropZone = document.getElementById("drop-zone");

    // Prevent default browser behavior on window to prevent opening dropped files as tabs
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        window.addEventListener(eventName, (e) => {
            e.preventDefault();
        }, false);
    });

    if (!dropZone) return;
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("border-walpar-600", "bg-sky-50");
        });
    });

    ['dragleave'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("border-walpar-600", "bg-sky-50");
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("border-walpar-600", "bg-sky-50");
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleFileUpload(files[0], true);   // Direct instant scan & upload
        }
    });
}

function initFileInput() {
    const fileInput = document.getElementById("file-input");
    if (fileInput) {
        fileInput.addEventListener("change", function(e) {
            if (this.files && this.files.length > 0) {
                handleFileUpload(this.files[0], true);   // Direct instant scan & upload
            }
            this.value = ""; // Reset so same file or next change always triggers
        });
    }

    const cropFileInput = document.getElementById("crop-file-input");
    if (cropFileInput) {
        cropFileInput.addEventListener("change", function(e) {
            if (this.files && this.files.length > 0) {
                openCropModal(this.files[0]);   // Document scanner with crop corners
            }
            this.value = "";
        });
    }

    const cameraInput = document.getElementById("camera-input");
    if (cameraInput) {
        cameraInput.addEventListener("change", function(e) {
            if (this.files && this.files.length > 0) {
                handleFileUpload(this.files[0], true);
            }
            this.value = "";
        });
    }
}

// Click on dropzone area triggers file picker
function onDropZoneClick(e) {
    if (e && e.target && (e.target.closest('#btn-camera') || e.target.closest('button'))) {
        return;
    }
    const fi = document.getElementById('file-input');
    if (fi) fi.click();
}

// Clipboard Paste (Ctrl+V)
function initClipboardPaste() {
    window.addEventListener("paste", (e) => {
        if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) {
            return;
        }
        const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
        if (!items) return;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf("image") !== -1) {
                const blob = items[i].getAsFile();
                if (blob) {
                    handleFileUpload(blob, true);
                    break;
                }
            }
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  WALPAR DOCUMENT SCANNER — 4-Corner Perspective Crop Widget
// ══════════════════════════════════════════════════════════════
const docScanner = {
    modalEl: null,
    stageEl: null,
    imgCanvas: null,
    overlayCanvas: null,
    loupeEl: null,
    loupeCanvas: null,
    
    sourceImage: null,
    sourceFile: null,
    rotation: 0,
    
    // Normalized coordinates (0.0 to 1.0) relative to CURRENT rotated image width & height
    corners: {
        tl: [0.06, 0.06],
        tr: [0.94, 0.06],
        br: [0.94, 0.94],
        bl: [0.06, 0.94]
    },
    
    imgDisplay: { x: 0, y: 0, width: 0, height: 0, scale: 1, imgW: 0, imgH: 0 },
    
    activeHandle: null,
    pointerId: null,
    dragStartPos: { x: 0, y: 0 },
    dragStartCorners: null,
    isInitialized: false,

    init() {
        if (this.isInitialized) return;
        this.modalEl = document.getElementById('crop-modal');
        this.stageEl = document.getElementById('scanner-stage');
        this.imgCanvas = document.getElementById('scanner-img-canvas');
        this.overlayCanvas = document.getElementById('scanner-overlay-canvas');
        this.loupeEl = document.getElementById('scanner-loupe');
        this.loupeCanvas = document.getElementById('scanner-loupe-canvas');

        if (!this.overlayCanvas) return;

        // Unified event handlers for mouse, stylus & multi-touch
        const handleStart = (e) => {
            if (e.cancelable) e.preventDefault();
            this.onDragStart(e);
        };
        const handleMove = (e) => {
            if (this.activeHandle) {
                if (e.cancelable) e.preventDefault();
                this.onDragMove(e);
            }
        };
        const handleEnd = (e) => {
            if (this.activeHandle) {
                if (e.cancelable) e.preventDefault();
                this.onDragEnd(e);
            }
        };

        // Pointer Events
        this.overlayCanvas.addEventListener('pointerdown', handleStart, { passive: false });
        this.overlayCanvas.addEventListener('pointermove', handleMove, { passive: false });
        this.overlayCanvas.addEventListener('pointerup', handleEnd, { passive: false });
        this.overlayCanvas.addEventListener('pointercancel', handleEnd, { passive: false });

        // Native Touch Events for guaranteed mobile Safari & Chrome support
        this.overlayCanvas.addEventListener('touchstart', handleStart, { passive: false });
        this.overlayCanvas.addEventListener('touchmove', handleMove, { passive: false });
        this.overlayCanvas.addEventListener('touchend', handleEnd, { passive: false });
        this.overlayCanvas.addEventListener('touchcancel', handleEnd, { passive: false });

        // Resize & Orientation Change
        window.addEventListener('resize', () => {
            if (this.modalEl && !this.modalEl.classList.contains('hidden') && this.sourceImage) {
                this.render();
            }
        });
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                if (this.modalEl && !this.modalEl.classList.contains('hidden') && this.sourceImage) {
                    this.render();
                }
            }, 100);
        });

        this.isInitialized = true;
    },

    open(file) {
        if (!file) return;
        const isDoc = file.type === "application/pdf" || /\.(pdf|docx?|xlsx?|csv|txt)$/i.test(file.name || '');
        if (isDoc) {
            handleFileUpload(file, true);
            return;
        }
        try {
            this.init();
            this.sourceFile = file;
            this.rotation = 0;
            this.resetCorners();

            const objUrl = URL.createObjectURL(file);
            const img = new Image();
            let hasLoaded = false;

            const timeoutId = setTimeout(() => {
                if (!hasLoaded) {
                    console.warn("[DocScanner] Canvas preview took too long, uploading directly.");
                    if (this.modalEl) this.modalEl.classList.add('hidden');
                    handleFileUpload(file, true);
                }
            }, 3000);

            img.onload = () => {
                hasLoaded = true;
                clearTimeout(timeoutId);
                this.sourceImage = img;
                if (this.modalEl) {
                    this.modalEl.classList.remove('hidden');
                }
                if (window.lucide) window.lucide.createIcons();

                setTimeout(() => {
                    this.render();
                    this.autoDetect();
                }, 60);
            };

            img.onerror = (err) => {
                hasLoaded = true;
                clearTimeout(timeoutId);
                console.warn("[DocScanner] Preview render error, falling back to direct upload:", err);
                if (this.modalEl) this.modalEl.classList.add('hidden');
                handleFileUpload(file, true);
            };

            img.src = objUrl;
        } catch (err) {
            console.error("[DocScanner] Modal error, uploading directly:", err);
            handleFileUpload(file, true);
        }
    },

    resetCorners() {
        this.corners = {
            tl: [0.06, 0.06],
            tr: [0.94, 0.06],
            br: [0.94, 0.94],
            bl: [0.06, 0.94]
        };
    },

    render() {
        if (!this.stageEl || !this.sourceImage) return;

        const rot = this.rotation;
        const isRotated90 = (rot === 90 || rot === 270);
        const imgW = isRotated90 ? this.sourceImage.naturalHeight : this.sourceImage.naturalWidth;
        const imgH = isRotated90 ? this.sourceImage.naturalWidth : this.sourceImage.naturalHeight;

        const stageRect = this.stageEl.getBoundingClientRect();
        let stageW = Math.floor(stageRect.width);
        let stageH = Math.floor(stageRect.height);

        // Mobile fallback if stage layout has not finished
        if (!stageW || stageW < 100) stageW = Math.min(window.innerWidth || 360, 560);
        if (!stageH || stageH < 100) stageH = Math.max(220, Math.floor(window.innerHeight * 0.45));

        const scale = Math.min((stageW - 16) / imgW, (stageH - 16) / imgH);
        const dw = Math.floor(imgW * scale);
        const dh = Math.floor(imgH * scale);
        const dx = Math.floor((stageW - dw) / 2);
        const dy = Math.floor((stageH - dh) / 2);

        this.imgDisplay = {
            x: dx,
            y: dy,
            width: dw,
            height: dh,
            scale: scale,
            imgW: imgW,
            imgH: imgH
        };

        this.imgCanvas.width = stageW;
        this.imgCanvas.height = stageH;
        this.overlayCanvas.width = stageW;
        this.overlayCanvas.height = stageH;

        // Render base rotated image
        const ctx = this.imgCanvas.getContext('2d');
        ctx.clearRect(0, 0, stageW, stageH);
        ctx.save();
        ctx.translate(dx + dw / 2, dy + dh / 2);
        ctx.rotate((rot * Math.PI) / 180);
        const origW = this.sourceImage.naturalWidth;
        const origH = this.sourceImage.naturalHeight;
        ctx.drawImage(this.sourceImage, -origW * scale / 2, -origH * scale / 2, origW * scale, origH * scale);
        ctx.restore();

        this.renderOverlay();
    },

    getScreenPoint(u, v) {
        const d = this.imgDisplay;
        return {
            x: d.x + u * d.width,
            y: d.y + v * d.height
        };
    },

    renderOverlay() {
        if (!this.overlayCanvas) return;
        const ctx = this.overlayCanvas.getContext('2d');
        const w = this.overlayCanvas.width;
        const h = this.overlayCanvas.height;
        ctx.clearRect(0, 0, w, h);

        const d = this.imgDisplay;
        if (!d.width || !d.height) return;

        const tl = this.getScreenPoint(this.corners.tl[0], this.corners.tl[1]);
        const tr = this.getScreenPoint(this.corners.tr[0], this.corners.tr[1]);
        const br = this.getScreenPoint(this.corners.br[0], this.corners.br[1]);
        const bl = this.getScreenPoint(this.corners.bl[0], this.corners.bl[1]);

        // 1. Semi-transparent dark mask over non-selected area
        ctx.save();
        ctx.fillStyle = 'rgba(2, 6, 23, 0.68)';
        ctx.fillRect(d.x, d.y, d.width, d.height);

        ctx.globalCompositeOperation = 'destination-out';
        ctx.beginPath();
        ctx.moveTo(tl.x, tl.y);
        ctx.lineTo(tr.x, tr.y);
        ctx.lineTo(br.x, br.y);
        ctx.lineTo(bl.x, bl.y);
        ctx.closePath();
        ctx.fill();
        ctx.restore();

        // 2. Interior rule-of-thirds alignment grid
        ctx.save();
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.25)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        for (let i = 1; i <= 2; i++) {
            const f = i / 3;
            const p1 = { x: tl.x + (bl.x - tl.x) * f, y: tl.y + (bl.y - tl.y) * f };
            const p2 = { x: tr.x + (br.x - tr.x) * f, y: tr.y + (br.y - tr.y) * f };
            ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke();
            const p3 = { x: tl.x + (tr.x - tl.x) * f, y: tl.y + (tr.y - tl.y) * f };
            const p4 = { x: bl.x + (br.x - bl.x) * f, y: bl.y + (br.y - bl.y) * f };
            ctx.beginPath(); ctx.moveTo(p3.x, p3.y); ctx.lineTo(p4.x, p4.y); ctx.stroke();
        }
        ctx.restore();

        // 3. Quad outline (Vibrant Walpar blue with outer glow)
        ctx.save();
        ctx.strokeStyle = '#0284c7';
        ctx.lineWidth = 3;
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.moveTo(tl.x, tl.y);
        ctx.lineTo(tr.x, tr.y);
        ctx.lineTo(br.x, br.y);
        ctx.lineTo(bl.x, bl.y);
        ctx.closePath();
        ctx.stroke();

        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([6, 5]);
        ctx.shadowBlur = 0;
        ctx.stroke();
        ctx.restore();

        // 4. Edge Midpoint Handles (MT, MR, MB, ML)
        const midpoints = [
            { id: 'mt', x: (tl.x + tr.x) / 2, y: (tl.y + tr.y) / 2 },
            { id: 'mr', x: (tr.x + br.x) / 2, y: (tr.y + br.y) / 2 },
            { id: 'mb', x: (bl.x + br.x) / 2, y: (bl.y + br.y) / 2 },
            { id: 'ml', x: (tl.x + bl.x) / 2, y: (tl.y + bl.y) / 2 },
        ];

        midpoints.forEach(m => {
            ctx.save();
            ctx.fillStyle = '#ffffff';
            ctx.strokeStyle = '#0284c7';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.arc(m.x, m.y, 7, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();
            ctx.restore();
        });

        // 5. Four Corner Pins (TL, TR, BR, BL)
        const cornersList = [
            { id: 'tl', p: tl, label: 'TL' },
            { id: 'tr', p: tr, label: 'TR' },
            { id: 'br', p: br, label: 'BR' },
            { id: 'bl', p: bl, label: 'BL' }
        ];

        cornersList.forEach(c => {
            const isActive = (this.activeHandle === c.id);
            ctx.save();

            // Glow ring when active / dragging
            if (isActive) {
                ctx.strokeStyle = 'rgba(56, 189, 248, 0.7)';
                ctx.lineWidth = 3.5;
                ctx.beginPath();
                ctx.arc(c.p.x, c.p.y, 22, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Outer white ring
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(c.p.x, c.p.y, 12, 0, Math.PI * 2);
            ctx.fill();

            // Inner core
            ctx.fillStyle = isActive ? '#0284c7' : '#0369a1';
            ctx.beginPath();
            ctx.arc(c.p.x, c.p.y, 8.5, 0, Math.PI * 2);
            ctx.fill();

            // Center dot
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(c.p.x, c.p.y, 2.5, 0, Math.PI * 2);
            ctx.fill();

            // Corner tag badge
            ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
            ctx.font = 'bold 9px monospace';
            const offset = (c.id === 'tl' || c.id === 'bl') ? -26 : 12;
            const offsetY = (c.id === 'tl' || c.id === 'tr') ? -14 : 18;
            ctx.fillRect(c.p.x + offset - 2, c.p.y + offsetY - 8, 18, 12);
            ctx.fillStyle = '#38bdf8';
            ctx.fillText(c.label, c.p.x + offset + 1, c.p.y + offsetY + 1);

            ctx.restore();
        });
    },

    getEventPos(e) {
        const rect = this.overlayCanvas.getBoundingClientRect();
        let clientX = 0, clientY = 0;
        if (e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        } else if (e.changedTouches && e.changedTouches.length > 0) {
            clientX = e.changedTouches[0].clientX;
            clientY = e.changedTouches[0].clientY;
        } else {
            clientX = e.clientX;
            clientY = e.clientY;
        }

        // Scale factors convert screen CSS pixels to canvas internal coordinates
        const scaleX = (rect.width > 0) ? (this.overlayCanvas.width / rect.width) : 1;
        const scaleY = (rect.height > 0) ? (this.overlayCanvas.height / rect.height) : 1;

        return {
            canvasX: (clientX - rect.left) * scaleX,
            canvasY: (clientY - rect.top) * scaleY,
            cssX: clientX - rect.left,
            cssY: clientY - rect.top,
            scaleX: scaleX,
            scaleY: scaleY
        };
    },

    hitTest(canvasX, canvasY, scaleX = 1) {
        const tl = this.getScreenPoint(this.corners.tl[0], this.corners.tl[1]);
        const tr = this.getScreenPoint(this.corners.tr[0], this.corners.tr[1]);
        const br = this.getScreenPoint(this.corners.br[0], this.corners.br[1]);
        const bl = this.getScreenPoint(this.corners.bl[0], this.corners.bl[1]);

        const dist = (p1, p2) => Math.hypot(p1.x - p2.x, p1.y - p2.y);
        const p = { x: canvasX, y: canvasY };

        // Corner hit radius: at least 44 CSS pixels on physical screen
        const cornerThreshold = Math.max(44 * scaleX, 40);
        if (dist(p, tl) <= cornerThreshold) return 'tl';
        if (dist(p, tr) <= cornerThreshold) return 'tr';
        if (dist(p, br) <= cornerThreshold) return 'br';
        if (dist(p, bl) <= cornerThreshold) return 'bl';

        // Edge midpoints hit radius: at least 32 CSS pixels
        const mt = { x: (tl.x + tr.x) / 2, y: (tl.y + tr.y) / 2 };
        const mr = { x: (tr.x + br.x) / 2, y: (tr.y + br.y) / 2 };
        const mb = { x: (bl.x + br.x) / 2, y: (bl.y + br.y) / 2 };
        const ml = { x: (tl.x + bl.x) / 2, y: (tl.y + bl.y) / 2 };

        const edgeThreshold = Math.max(32 * scaleX, 30);
        if (dist(p, mt) <= edgeThreshold) return 'mt';
        if (dist(p, mr) <= edgeThreshold) return 'mr';
        if (dist(p, mb) <= edgeThreshold) return 'mb';
        if (dist(p, ml) <= edgeThreshold) return 'ml';

        // Quad body drag
        if (this.isInsideQuad(p, tl, tr, br, bl)) return 'body';

        return null;
    },

    isInsideQuad(p, p1, p2, p3, p4) {
        const pts = [p1, p2, p3, p4];
        let inside = false;
        for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
            const xi = pts[i].x, yi = pts[i].y;
            const xj = pts[j].x, yj = pts[j].y;
            const intersect = ((yi > p.y) !== (yj > p.y)) &&
                (p.x < (xj - xi) * (p.y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }
        return inside;
    },

    onDragStart(e) {
        const pos = this.getEventPos(e);
        const hit = this.hitTest(pos.canvasX, pos.canvasY, pos.scaleX);
        if (!hit) return;

        this.activeHandle = hit;
        this.pointerId = e.pointerId || null;
        try {
            if (e.pointerId && this.overlayCanvas.setPointerCapture) {
                this.overlayCanvas.setPointerCapture(e.pointerId);
            }
        } catch (err) {}

        this.dragStartPos = { x: pos.canvasX, y: pos.canvasY };
        this.dragStartCorners = JSON.parse(JSON.stringify(this.corners));

        this.updateLoupe(pos);
        this.renderOverlay();
    },

    onDragMove(e) {
        if (!this.activeHandle) return;

        const pos = this.getEventPos(e);
        const d = this.imgDisplay;
        if (!d.width || !d.height) return;

        const du = (pos.canvasX - this.dragStartPos.x) / d.width;
        const dv = (pos.canvasY - this.dragStartPos.y) / d.height;

        const clamp = (val) => Math.max(0, Math.min(1, val));
        const init = this.dragStartCorners;

        if (this.activeHandle === 'tl') {
            this.corners.tl = [clamp(init.tl[0] + du), clamp(init.tl[1] + dv)];
        } else if (this.activeHandle === 'tr') {
            this.corners.tr = [clamp(init.tr[0] + du), clamp(init.tr[1] + dv)];
        } else if (this.activeHandle === 'br') {
            this.corners.br = [clamp(init.br[0] + du), clamp(init.br[1] + dv)];
        } else if (this.activeHandle === 'bl') {
            this.corners.bl = [clamp(init.bl[0] + du), clamp(init.bl[1] + dv)];
        } else if (this.activeHandle === 'mt') {
            this.corners.tl = [clamp(init.tl[0] + du), clamp(init.tl[1] + dv)];
            this.corners.tr = [clamp(init.tr[0] + du), clamp(init.tr[1] + dv)];
        } else if (this.activeHandle === 'mr') {
            this.corners.tr = [clamp(init.tr[0] + du), clamp(init.tr[1] + dv)];
            this.corners.br = [clamp(init.br[0] + du), clamp(init.br[1] + dv)];
        } else if (this.activeHandle === 'mb') {
            this.corners.bl = [clamp(init.bl[0] + du), clamp(init.bl[1] + dv)];
            this.corners.br = [clamp(init.br[0] + du), clamp(init.br[1] + dv)];
        } else if (this.activeHandle === 'ml') {
            this.corners.tl = [clamp(init.tl[0] + du), clamp(init.tl[1] + dv)];
            this.corners.bl = [clamp(init.bl[0] + du), clamp(init.bl[1] + dv)];
        } else if (this.activeHandle === 'body') {
            const newTlU = init.tl[0] + du, newTlV = init.tl[1] + dv;
            const newTrU = init.tr[0] + du, newTrV = init.tr[1] + dv;
            const newBrU = init.br[0] + du, newBrV = init.br[1] + dv;
            const newBlU = init.bl[0] + du, newBlV = init.bl[1] + dv;

            const minU = Math.min(newTlU, newTrU, newBrU, newBlU);
            const maxU = Math.max(newTlU, newTrU, newBrU, newBlU);
            const minV = Math.min(newTlV, newTrV, newBrV, newBlV);
            const maxV = Math.max(newTlV, newTrV, newBrV, newBlV);

            let adjU = du, adjV = dv;
            if (minU < 0) adjU -= minU;
            if (maxU > 1) adjU -= (maxU - 1);
            if (minV < 0) adjV -= minV;
            if (maxV > 1) adjV -= (maxV - 1);

            this.corners.tl = [clamp(init.tl[0] + adjU), clamp(init.tl[1] + adjV)];
            this.corners.tr = [clamp(init.tr[0] + adjU), clamp(init.tr[1] + adjV)];
            this.corners.br = [clamp(init.br[0] + adjU), clamp(init.br[1] + adjV)];
            this.corners.bl = [clamp(init.bl[0] + adjU), clamp(init.bl[1] + adjV)];
        }

        this.updateLoupe(pos);
        this.renderOverlay();
    },

    onDragEnd(e) {
        if (!this.activeHandle) return;
        try {
            if (this.pointerId !== null && this.overlayCanvas.releasePointerCapture) {
                this.overlayCanvas.releasePointerCapture(this.pointerId);
            }
        } catch (err) {}
        this.activeHandle = null;
        this.pointerId = null;
        this.hideLoupe();
        this.renderOverlay();
    },

    updateLoupe(pos) {
        if (!this.loupeEl || !this.loupeCanvas || !this.sourceImage) return;
        const cornerKeys = ['tl', 'tr', 'br', 'bl'];
        if (!cornerKeys.includes(this.activeHandle)) {
            this.hideLoupe();
            return;
        }

        const cornerCoords = this.corners[this.activeHandle];
        const sp = this.getScreenPoint(cornerCoords[0], cornerCoords[1]);

        // Position loupe in Screen CSS pixels so it floats accurately above finger on mobile
        const loupeSize = 100;
        const cssHandleX = (pos && pos.scaleX > 0) ? (sp.x / pos.scaleX) : sp.x;
        const cssHandleY = (pos && pos.scaleY > 0) ? (sp.y / pos.scaleY) : sp.y;

        let loupeX = cssHandleX;
        let loupeY = cssHandleY - 80;

        const stageRect = this.stageEl.getBoundingClientRect();
        if (loupeY - loupeSize / 2 < 10) loupeY = cssHandleY + 80; // Flip below if near top
        loupeX = Math.max(loupeSize / 2 + 5, Math.min(stageRect.width - loupeSize / 2 - 5, loupeX));

        this.loupeEl.style.left = `${loupeX}px`;
        this.loupeEl.style.top = `${loupeY}px`;
        this.loupeEl.classList.remove('hidden');

        // Draw 2.5x zoomed view
        this.loupeCanvas.width = loupeSize;
        this.loupeCanvas.height = loupeSize;
        const ctx = this.loupeCanvas.getContext('2d');
        ctx.clearRect(0, 0, loupeSize, loupeSize);

        const zoom = 2.5;
        const origW = this.sourceImage.naturalWidth;
        const origH = this.sourceImage.naturalHeight;
        const rot = this.rotation;
        const isRotated90 = (rot === 90 || rot === 270);
        const curImgW = isRotated90 ? origH : origW;
        const curImgH = isRotated90 ? origW : origH;

        const targetX = cornerCoords[0] * curImgW;
        const targetY = cornerCoords[1] * curImgH;

        ctx.save();
        ctx.translate(loupeSize / 2, loupeSize / 2);
        ctx.scale(zoom, zoom);
        ctx.rotate((rot * Math.PI) / 180);

        let origTargetX = targetX;
        let origTargetY = targetY;
        if (rot === 90) {
            origTargetX = targetY;
            origTargetY = origH - targetX;
        } else if (rot === 180) {
            origTargetX = origW - targetX;
            origTargetY = origH - targetY;
        } else if (rot === 270) {
            origTargetX = origW - targetY;
            origTargetY = targetX;
        }

        ctx.drawImage(this.sourceImage, -origTargetX, -origTargetY);
        ctx.restore();
    },

    hideLoupe() {
        if (this.loupeEl) this.loupeEl.classList.add('hidden');
    },

    rotate(deg) {
        this.rotation = (this.rotation + deg + 360) % 360;
        this.render();
    },

    fullImage() {
        this.corners = {
            tl: [0.0, 0.0],
            tr: [1.0, 0.0],
            br: [1.0, 1.0],
            bl: [0.0, 1.0]
        };
        this.renderOverlay();
    },

    reset() {
        this.resetCorners();
        this.renderOverlay();
    },

    async autoDetect() {
        if (!this.sourceFile) return;
        try {
            const formData = new FormData();
            formData.append('file', this.sourceFile);
            const res = await fetch('/api/detect-corners', {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            if (data.success && data.corners) {
                this.corners = data.corners;
                this.renderOverlay();
            }
        } catch (err) {
            console.warn('[DocScanner] Auto-detect notice:', err);
        }
    },

    confirmCrop() {
        const file = this.sourceFile;
        const corners = JSON.parse(JSON.stringify(this.corners));
        const rot = this.rotation;
        this.close();
        if (file) {
            handleFileUpload(file, true, corners, rot);
        }
    },

    skip() {
        const file = this.sourceFile;
        this.close();
        if (file) {
            handleFileUpload(file, true, null, 0);
        }
    },

    close() {
        if (this.modalEl) this.modalEl.classList.add('hidden');
        this.hideLoupe();
        this.activeHandle = null;
        this.pointerId = null;
    }
};

// Global helper wrappers called from HTML onclick handlers
function openCropModal(file) {
    docScanner.open(file);
}

function cropSkip() {
    docScanner.skip();
}

function cropConfirm() {
    docScanner.confirmCrop();
}

function cropRotate(degrees) {
    docScanner.rotate(degrees);
}

function cropReset() {
    docScanner.reset();
}

// ══════════════════════════════════════════════════════════════
//  Upload file with instant preview & progress
// ══════════════════════════════════════════════════════════════
// skipCrop=true means direct upload and scan without mandatory crop modal
async function handleFileUpload(file, skipCrop = true, cropCorners = null, rotation = 0) {
    if (!file) return;

    // Check if it's an image or document (PDF, Word, Excel, CSV, TXT)
    const isDoc = file.type === "application/pdf" || /\.(pdf|docx?|xlsx?|csv|txt)$/i.test(file.name || '');
    const isImage = file.type.startsWith("image/") || /\.(jpe?g|png|webp|bmp|jfif|tiff?|heic|heif)$/i.test(file.name || '');
    if (!isImage && !isDoc) {
        alert("Please select a valid formula document or image file (PDF, Excel, Word, CSV, PNG, JPG, WEBP, BMP, HEIC).");
        return;
    }

    // If caller specifically requested crop modal first (skip for flat documents)
    if (!skipCrop && !isDoc) {
        openCropModal(file);
        return;
    }

    // Instant Local Image Preview (User sees their photo immediately)
    if (!isDoc) {
        try {
            const previewUrl = URL.createObjectURL(file);
            const previewImg = new Image();
            previewImg.onload = () => {
                appState.image = previewImg;
                drawCanvas();
                const viewerCard = document.getElementById("image-viewer-card");
                if (viewerCard) viewerCard.classList.remove("hidden");
                const scanningOverlay = document.getElementById("scanning-overlay");
                if (scanningOverlay) scanningOverlay.classList.remove("hidden");
            };
            previewImg.src = previewUrl;
        } catch (prevErr) {
            console.warn("Local preview notice:", prevErr);
        }
    } else {
        const viewerCard = document.getElementById("image-viewer-card");
        if (viewerCard) viewerCard.classList.remove("hidden");
        const scanningOverlay = document.getElementById("scanning-overlay");
        if (scanningOverlay) scanningOverlay.classList.remove("hidden");
    }

    showLoading(true);
    appState.currentFile = file;
    appState.currentSample = null;
    const engineEl = document.getElementById("engine-select");
    const engine = engineEl ? engineEl.value : "ollama";

    const formData = new FormData();
    formData.append("file", file, file.name || "formula_upload.jpg");
    formData.append("engine", engine);

    // Pass 4-corner perspective crop coordinates and rotation if user cropped
    if (cropCorners) {
        formData.append("crop_corners", JSON.stringify(cropCorners));
        formData.append("rotation", rotation || 0);
    }

    try {
        const res = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });
        const resText = await res.text();
        let data;
        try {
            data = JSON.parse(resText);
        } catch (parseErr) {
            if (res.status === 502) {
                throw new Error("Server was temporarily busy or restarting. Please re-upload in a few moments.");
            } else if (res.status === 413) {
                throw new Error("File size too large. Please upload an image under 10MB.");
            } else if (res.status === 401 || res.status === 403) {
                window.location.href = "/login?error=Session+expired.+Please+log+in+again";
                return;
            } else {
                throw new Error(`Server returned HTTP ${res.status}`);
            }
        }

        if (data && data.success) {
            processExtractionResult(data);
        } else {
            alert("Error running OCR: " + ((data && data.error) || "Unknown error"));
        }
    } catch (err) {
        console.error("Upload error:", err);
        alert("Upload notice: " + (err.message || "Failed to process formula photo"));
    } finally {
        showLoading(false);
        const scanningOverlay = document.getElementById("scanning-overlay");
        if (scanningOverlay) scanningOverlay.classList.add("hidden");
    }
}

// Function to crop current active image or select new one for cropping
function cropCurrentImage() {
    if (appState.currentFile) {
        openCropModal(appState.currentFile);
    } else {
        const fi = document.getElementById("crop-file-input") || document.getElementById("file-input");
        if (fi) fi.click();
    }
}


// Quick Sample Loader
async function loadSample(sampleName) {
    showLoading(true);
    appState.currentSample = sampleName;
    appState.currentFile = null;
    const engine = document.getElementById("engine-select").value;

    try {
        const res = await fetch(`/api/sample/${sampleName}?engine=${engine}`, {
            method: "POST"
        });
        const resText = await res.text();
        let data;
        try {
            data = JSON.parse(resText);
        } catch (parseErr) {
            if (res.status === 502) {
                throw new Error("Server temporarily busy. Please retry.");
            } else {
                throw new Error(`Server returned HTTP ${res.status}`);
            }
        }

        if (data && data.success) {
            processExtractionResult(data);
        } else {
            alert("Error loading sample: " + ((data && data.error) || "Unknown error"));
        }
    } catch (err) {
        alert("Notice: " + err.message);
    } finally {
        showLoading(false);
    }
}

// Process OCR Response
function processExtractionResult(data) {
    appState.imageSrc = data.image_url;
    appState.ocrLines = data.ocr_lines || [];
    appState.ingredients = data.ingredients || [];

    // Show re-run button
    document.getElementById("re-run-box").classList.remove("hidden");

    // Load image onto canvas
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
        appState.image = img;
        drawCanvas();
        const viewerCard = document.getElementById("image-viewer-card");
        if (viewerCard) viewerCard.classList.remove("hidden");
    };
    img.onerror = () => {
        console.warn("Server image URL reload warning, drawing current preview");
        drawCanvas();
        const viewerCard = document.getElementById("image-viewer-card");
        if (viewerCard) viewerCard.classList.remove("hidden");
    };
    img.src = data.image_url;

    // Render summary banner
    const summaryBanner = document.getElementById("summary-banner");
    if (summaryBanner) {
        summaryBanner.classList.remove("hidden");
        const matched = data.matched_count || 0;
        const total = data.total_count || appState.ingredients.length;
        document.getElementById("matched-status-text").innerText = `${matched} of ${total} ingredients matched with Walpar master database`;
        const pct = total > 0 ? Math.round((matched / total) * 100) : 0;
        const badge = document.getElementById("match-rate-badge");
        badge.innerText = `${pct}% Matched`;
        if (pct >= 80) {
            badge.className = "px-2.5 py-1 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full flex-shrink-0";
        } else {
            badge.className = "px-2.5 py-1 bg-amber-100 text-amber-800 text-xs font-bold rounded-full flex-shrink-0";
        }

        const engineBadge = document.getElementById("engine-used-badge");
        if (engineBadge) {
            engineBadge.innerText = data.engine_used || appState.activeEngine;
        }
    }

    // Set evaluation if present
    if (data.evaluation) {
        appState.evaluation = data.evaluation;
    }

    // Render tables and lines
    renderRawOcrLines(appState.ocrLines);
    renderIngredientsTable();

    // Render Scientific Formula Evaluation & AI Suggestions
    if (appState.evaluation) {
        renderFormulaEvaluation(appState.evaluation);
    } else {
        evaluateActiveFormula();
    }

    lucide.createIcons();
}

// Draw Image and OCR Bounding Boxes on Canvas
function drawCanvas() {
    const canvas = document.getElementById("ocr-canvas");
    if (!canvas || !appState.image) return;
    const ctx = canvas.getContext("2d");

    canvas.width = appState.image.width;
    canvas.height = appState.image.height;

    // Draw background image
    ctx.drawImage(appState.image, 0, 0);

    // Draw bounding boxes if enabled
    if (appState.showBoxes && appState.ocrLines) {
        const strokeW = Math.max(2, Math.round(canvas.width / 450));
        const fontSize = Math.max(11, Math.round(canvas.width / 75));
        const badgeH = Math.round(fontSize * 1.6);

        appState.ocrLines.forEach(line => {
            const bbox = line.bbox;
            if (bbox && bbox.length === 4) {
                const [minX, minY, maxX, maxY] = bbox;
                const width = maxX - minX;
                const height = maxY - minY;

                // Box stroke & fill
                ctx.strokeStyle = "#0284c7";
                ctx.lineWidth = strokeW;
                ctx.strokeRect(minX, minY, width, height);

                ctx.fillStyle = "rgba(2, 132, 199, 0.12)";
                ctx.fillRect(minX, minY, width, height);

                // Small badge
                const badgeW = Math.min(width, fontSize * 9);
                ctx.fillStyle = "#0369a1";
                ctx.fillRect(minX, Math.max(0, minY - badgeH), badgeW, badgeH);
                ctx.fillStyle = "#ffffff";
                ctx.font = `bold ${fontSize}px sans-serif`;
                ctx.fillText(`OCR: ${(line.confidence * 100).toFixed(0)}%`, minX + 4, Math.max(fontSize, minY - 4));
            }
        });
    }
}

function toggleBoxes() {
    appState.showBoxes = document.getElementById("toggle-boxes").checked;
    drawCanvas();
}

// Raw OCR Lines Drawer
function toggleRawOcr() {
    const drawer = document.getElementById("raw-ocr-drawer");
    const chevron = document.getElementById("raw-ocr-chevron");
    const isHidden = drawer.classList.contains("hidden");
    if (isHidden) {
        drawer.classList.remove("hidden");
        chevron.classList.add("rotate-180");
    } else {
        drawer.classList.add("hidden");
        chevron.classList.remove("rotate-180");
    }
}

function renderRawOcrLines(lines) {
    const drawer = document.getElementById("raw-ocr-drawer");
    const countEl = document.getElementById("raw-ocr-count");
    countEl.innerText = `View Raw OCR Lines (${lines.length})`;
    
    drawer.innerHTML = lines.map((l, i) => `
        <div class="flex items-center justify-between py-1 border-b border-slate-100 last:border-0">
            <span class="text-slate-700 truncate mr-2">${i+1}. ${escapeHtml(l.text)}</span>
            <span class="text-[10px] text-sky-600 bg-sky-50 px-1 rounded flex-shrink-0 font-sans">${(l.confidence*100).toFixed(0)}%</span>
        </div>
    `).join("");
}

// High-precision Pharmaceutical IU <-> mg Potency Conversion Factors
function getIuToMgFactor(name) {
    const n = (name || "").toLowerCase().trim();
    // 1. Vitamin D family (D3 Cholecalciferol, D2 Ergocalciferol): 1 IU = 0.025 mcg = 0.000025 mg
    if (/\b(vitamin\s*d|vit\s*d|d3|d2|cholecalciferol|ergocalciferol|calciferol)\b/i.test(n) || n.includes('cholecalciferol') || n.includes('calciferol') || n.includes('vitamin d') || n.includes('vit d') || n.includes('d3')) {
        return 0.000025;
    }
    // 2. Vitamin A family (Retinol, Retinyl Acetate, Retinyl Palmitate, Beta-Carotene): 1 IU = 0.3 mcg = 0.0003 mg
    if (/\b(vitamin\s*a|vit\s*a|retinol|retinyl|carotene)\b/i.test(n) || n.includes('retinol') || n.includes('retinyl') || n.includes('vitamin a') || n.includes('vit a')) {
        return 0.0003;
    }
    // 3. Vitamin E family (dl-alpha-tocopheryl acetate, d-alpha-tocopherol): 1 IU = 0.67 mg
    if (/\b(vitamin\s*e|vit\s*e|tocopher|tocopheryl)\b/i.test(n) || n.includes('tocopher') || n.includes('vitamin e') || n.includes('vit e')) {
        return 0.67;
    }
    // Default fallback: Vitamin D3 standard (0.000025 mg / IU)
    return 0.000025;
}

function getMgToIuFactor(name) {
    const factor = getIuToMgFactor(name);
    return factor > 0 ? (1.0 / factor) : 40000;
}

// Render Ingredients Table (Strictly NO PRICES)
function renderIngredientsTable() {
    const tbody = document.getElementById("ingredients-table-body");
    const footerActions = document.getElementById("table-footer-actions");
    const itemCountText = document.getElementById("item-count-text");

    if (!appState.ingredients || appState.ingredients.length === 0) {
        tbody.innerHTML = `
            <tr id="empty-state-row">
                <td colspan="5" class="text-center py-10 text-slate-400">
                    <p class="font-medium text-slate-600">No formula loaded yet</p>
                    <p class="text-[11px] text-slate-400 mt-0.5">Upload a formula photo on the left or select a sample</p>
                </td>
            </tr>
        `;
        if (footerActions) footerActions.classList.add("hidden");
        const bmrTrigger = document.getElementById("batch-master-trigger-card");
        if (bmrTrigger) bmrTrigger.classList.add("hidden");
        return;
    }

    if (footerActions) {
        footerActions.classList.remove("hidden");
        itemCountText.innerText = `${appState.ingredients.length} Ingredients listed`;
    }
    const bmrTrigger = document.getElementById("batch-master-trigger-card");
    if (bmrTrigger) bmrTrigger.classList.remove("hidden");

    tbody.innerHTML = appState.ingredients.map((item, idx) => {
        let matchBadge = "";
        if (item.is_matched) {
            matchBadge = `
                <div class="flex items-center space-x-1.5">
                    <span class="inline-flex items-center text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
                        <i data-lucide="check" class="w-3 h-3 mr-1 text-emerald-600"></i> Matched (${item.match_score || 100}%)
                    </span>
                    <span class="text-[10px] text-slate-400 truncate max-w-[140px]" title="Database: ${escapeHtml(item.db_raw_name || '')}">
                        ${escapeHtml(item.db_raw_name || '')}
                    </span>
                </div>
            `;
        } else {
            matchBadge = `
                <span class="inline-flex items-center text-[10px] font-semibold text-slate-600 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
                    Custom Active
                </span>
            `;
        }

        // Rate Database Status: Show RED warning or User-Estimated Input if not in rate avg database
        const isDbRate = item.is_rate_available && !item.is_user_estimated && Number(item.rate) > 0;
        const isUserEstimated = Boolean(item.is_user_estimated) && Number(item.rate) > 0;
        let rateBadge = "";

        if (isUserEstimated) {
            rateBadge = `
                <div class="mt-1 flex flex-col space-y-1">
                    <div class="flex items-center space-x-1.5 flex-wrap">
                        <span class="inline-flex items-center text-[10px] font-bold text-amber-800 bg-amber-100 border border-amber-300 px-1.5 py-0.5 rounded shadow-2xs">
                            <i data-lucide="edit-3" class="w-3 h-3 mr-1 text-amber-600"></i> User Estimated:
                        </span>
                        <div class="relative flex items-center">
                            <span class="absolute left-1.5 text-[10px] text-slate-500 font-bold">₹</span>
                            <input type="number" step="0.01" min="0" value="${item.rate}" 
                                   onchange="onUserEstimatedRateChange(${idx}, this.value)"
                                   class="w-24 pl-4 pr-1 py-0.5 text-xs font-mono font-bold border border-amber-400 rounded bg-amber-50/80 text-slate-900 focus:bg-white focus:ring-1 focus:ring-amber-500">
                            <span class="ml-1 text-[10px] text-slate-600 font-semibold">/ kg</span>
                        </div>
                    </div>
                    <span class="text-[9px] text-amber-700/80 font-sans italic">Audited in Admin (Not saved to official DB)</span>
                </div>
            `;
        } else if (!isDbRate) {
            rateBadge = `
                <div class="mt-1 flex flex-col space-y-1">
                    <div class="flex items-center space-x-1.5">
                        <span class="inline-flex items-center font-extrabold text-rose-700 bg-rose-100 border border-rose-300 px-1.5 py-0.5 rounded shadow-2xs text-[10px]" title="Not available in official database (rate avg.xlsx)">
                            <i data-lucide="alert-triangle" class="w-3 h-3 mr-1 text-rose-600"></i> Not in Rate Database
                        </span>
                    </div>
                    <div class="flex items-center space-x-1.5 pt-0.5">
                        <span class="text-[10px] font-bold text-slate-700">Fill Estimated Rate:</span>
                        <div class="relative flex items-center">
                            <span class="absolute left-1.5 text-[10px] text-slate-500 font-bold">₹</span>
                            <input type="number" step="0.01" min="0" placeholder="₹ / kg"
                                   value="${item.user_estimated_rate || ''}"
                                   onchange="onUserEstimatedRateChange(${idx}, this.value)"
                                   class="w-24 pl-4 pr-1 py-0.5 text-xs font-mono border border-slate-300 rounded bg-white text-slate-900 focus:border-amber-500 focus:ring-1 focus:ring-amber-500">
                            <span class="ml-1 text-[10px] text-slate-500 font-medium">/ kg</span>
                        </div>
                    </div>
                </div>
            `;
        } else {
            rateBadge = `
                <div class="mt-1 flex items-center space-x-1.5">
                    <span class="inline-flex items-center text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                        <i data-lucide="shield-check" class="w-3 h-3 mr-1 text-emerald-600"></i> Official DB Rate
                    </span>
                </div>
            `;
        }

        const evalItem = appState.evaluation && appState.evaluation.item_evaluations 
            ? appState.evaluation.item_evaluations.find(e => e.name.toLowerCase() === item.name.toLowerCase()) 
            : null;

        let examinePill = "";
        if (evalItem && evalItem.examine_matched) {
            const gColor = evalItem.evidence_grade === 'A' ? 'text-emerald-700 bg-emerald-50 border-emerald-200' : 'text-sky-700 bg-sky-50 border-sky-200';
            examinePill = `
                <div class="flex items-center space-x-1 mt-1">
                    <span class="inline-flex items-center text-[10px] font-semibold ${gColor} border px-1.5 py-0.2 rounded" title="Standard Clinical Dose: ${escapeHtml(evalItem.clinical_standard_dose)}">
                        <i data-lucide="award" class="w-3 h-3 mr-1"></i> Grade ${evalItem.evidence_grade} Evidence
                    </span>
                    <span class="text-[10px] text-slate-500 truncate max-w-[170px]" title="${escapeHtml(evalItem.clinical_standard_dose)}">
                        Std: ${escapeHtml(evalItem.clinical_standard_dose)}
                    </span>
                </div>
            `;
        }

        let saltPill = "";
        if (item.salt_element_calc) {
            const sc = item.salt_element_calc;
            const rdaBadge = sc.standard_adult_rda_pct > 0 
                ? `<span class="inline-flex items-center text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.2 rounded ml-1">${sc.standard_adult_rda_pct}% Adult RDA</span>` 
                : "";
            const secBadge = sc.secondary 
                ? `<span class="text-[10px] text-slate-500 font-sans ml-1">(+ ${sc.secondary.amount_mg}mg ${sc.secondary.name})</span>` 
                : "";
            const optionsCount = sc.element_options_count || (sc.element_options ? sc.element_options.length : 0);
            const optionsBadge = optionsCount > 0
                ? `<span class="inline-flex items-center text-[10px] font-extrabold text-teal-800 bg-teal-100/80 border border-teal-300 px-1.5 py-0.2 rounded ml-1 hover:bg-teal-200 shadow-2xs">⚡ ${optionsCount} Salt Options</span>`
                : `<span class="inline-flex items-center text-[10px] font-extrabold text-teal-800 bg-teal-100/80 border border-teal-300 px-1.5 py-0.2 rounded ml-1 hover:bg-teal-200 shadow-2xs">⚡ Options & RDA</span>`;

            saltPill = `
                <div class="mt-1 flex flex-wrap items-center gap-1 cursor-pointer hover:opacity-95 transition" 
                     onclick="openSaltRdaForIngredient('${escapeHtml(sc.salt_name || item.name)}', ${item.dosage || 100}, '${item.unit || 'mg'}')" 
                     title="Click to view full Elemental Salt &amp; RDA breakdown and compare all salt form options">
                    <span class="inline-flex items-center text-[10px] font-bold text-teal-800 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded shadow-2xs">
                        <i data-lucide="flask-conical" class="w-3 h-3 mr-1 text-teal-600"></i>
                        ${sc.is_elemental_specification ? `Target: ${sc.elemental_amount_mg} mg Elemental ${sc.parent_nutrient}` : `Elemental: ${sc.elemental_amount_mg} mg ${sc.parent_nutrient} (${sc.salt_percentage}%)`}
                    </span>
                    ${secBadge}
                    ${rdaBadge}
                    ${optionsBadge}
                </div>
            `;
        }

        const hasAnyRate = isDbRate || isUserEstimated;
        const rowBorder = hasAnyRate ? "hover:bg-slate-50/80 transition group" : "bg-rose-50/25 border-l-4 border-l-rose-500 hover:bg-rose-50/50 transition group";
        const rateMissingTag = hasAnyRate ? (isUserEstimated ? `<span class="inline-flex items-center text-[9px] font-bold text-amber-800 bg-amber-100 border border-amber-300 px-1.5 py-0.2 rounded ml-1.5">Estimated</span>` : "") : `<span class="inline-flex items-center text-[9px] font-extrabold text-rose-700 bg-rose-100 border border-rose-300 px-1.5 py-0.2 rounded ml-1.5 uppercase">Rate Missing</span>`;

        return `
            <tr class="${rowBorder}">
                <td class="py-2.5 px-3 font-medium text-slate-800">
                    <div class="flex items-center">
                        <input type="text" value="${escapeHtml(item.name)}" 
                               onchange="updateIngredientName(${idx}, this.value)"
                               class="w-full bg-transparent border-0 border-b border-transparent hover:border-slate-300 focus:border-walpar-500 focus:bg-white focus:ring-0 text-xs py-0.5 rounded font-semibold text-slate-800">
                        ${rateMissingTag}
                    </div>
                    ${item.raw_text ? `<span class="text-[10px] text-slate-400 block truncate max-w-xs">OCR: ${escapeHtml(item.raw_text)}</span>` : ''}
                    ${examinePill}
                    ${saltPill}
                </td>
                <td class="py-2.5 px-3">
                    <input type="number" step="any" value="${item.dosage}" 
                           oninput="updateIngredientDose(${idx}, this.value)"
                           class="w-24 text-xs bg-slate-50 border border-slate-300 rounded px-2 py-1 font-mono font-semibold text-slate-900 focus:ring-walpar-500 focus:border-walpar-500">
                    ${(() => {
                        const nameLower = (item.name || "").toLowerCase();
                        const isIuSubstance = /\b(vitamin\s*d|vit\s*d|d3|d2|cholecalciferol|ergocalciferol|calciferol|vitamin\s*a|vit\s*a|retinol|retinyl|carotene|vitamin\s*e|vit\s*e|tocopher)\b/i.test(nameLower) || nameLower.includes('d3') || nameLower.includes('cholecalciferol');
                        const dNum = parseFloat(item.dosage) || 0;
                        if (item.unit && item.unit.toUpperCase() === 'IU') {
                            const equivMg = dNum * getIuToMgFactor(item.name);
                            const disp = equivMg < 0.001 ? equivMg.toFixed(6) : (equivMg < 0.1 ? equivMg.toFixed(4) : equivMg.toFixed(2));
                            return `<span class="text-[10px] text-teal-700 font-semibold block mt-0.5" title="International Units equivalent weight">≈ ${disp} mg</span>`;
                        } else if (item.unit && item.unit.toLowerCase() === 'mg' && isIuSubstance && dNum > 0) {
                            const equivIu = Math.round(dNum * getMgToIuFactor(item.name));
                            return `<span class="text-[10px] text-teal-700 font-semibold block mt-0.5" title="International Units potency">≈ ${equivIu.toLocaleString()} IU</span>`;
                        } else if (item.unit && item.unit.toLowerCase() === 'mcg') {
                            return `<span class="text-[10px] text-slate-400 font-medium block mt-0.5">≈ ${(dNum / 1000).toFixed(3)} mg</span>`;
                        } else if (item.unit && item.unit.toLowerCase() === 'g') {
                            return `<span class="text-[10px] text-slate-400 font-medium block mt-0.5">≈ ${(dNum * 1000).toFixed(1)} mg</span>`;
                        }
                        return '';
                    })()}
                </td>
                <td class="py-2.5 px-3">
                    <select onchange="updateIngredientUnit(${idx}, this.value)" 
                            class="text-xs bg-slate-50 border border-slate-300 rounded px-1.5 py-1 focus:ring-walpar-500 font-medium">
                        <option value="mg" ${item.unit.toLowerCase() === 'mg' ? 'selected' : ''}>mg</option>
                        <option value="mcg" ${item.unit.toLowerCase() === 'mcg' ? 'selected' : ''}>mcg</option>
                        <option value="IU" ${item.unit.toUpperCase() === 'IU' ? 'selected' : ''}>IU</option>
                        <option value="g" ${item.unit.toLowerCase() === 'g' ? 'selected' : ''}>g</option>
                        <option value="%" ${item.unit === '%' ? 'selected' : ''}>%</option>
                        <option value="Billion CFU" ${item.unit.toLowerCase().includes('cfu') ? 'selected' : ''}>Billion CFU</option>
                        <option value="ml" ${item.unit.toLowerCase() === 'ml' ? 'selected' : ''}>ml</option>
                    </select>
                </td>
                <td class="py-2.5 px-3">
                    ${matchBadge}
                    ${rateBadge}
                </td>
                <td class="py-2.5 px-3 text-center">
                    <button onclick="removeIngredient(${idx})" title="Remove ingredient" 
                            class="text-slate-300 hover:text-rose-600 p-1 rounded transition opacity-80 group-hover:opacity-100">
                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join("");

    lucide.createIcons();
}

// User-Estimated Rate Entry (Audited in Admin Panel, NEVER written to official DB)
function onUserEstimatedRateChange(idx, val) {
    if (!appState.ingredients || !appState.ingredients[idx]) return;
    const rateNum = parseFloat(val) || 0;
    const item = appState.ingredients[idx];
    if (rateNum > 0) {
        item.rate = rateNum;
        item.user_estimated_rate = rateNum;
        item.is_user_estimated = true;
        item.is_rate_available = true;
        
        // Log to server (maintained in Admin Panel missing_rate_requests, NOT added to database)
        fetch("/api/batch-master/log-estimated-rate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                ingredient_name: item.name,
                estimated_rate: rateNum,
                product_type: "Tablet"
            })
        }).catch(err => console.warn("Failed to log user estimated rate:", err));
    } else {
        item.rate = 0;
        item.user_estimated_rate = 0;
        item.is_user_estimated = false;
        item.is_rate_available = false;
    }
    renderIngredientsTable();
}

// Inline updates
function updateIngredientDose(idx, val) {
    const num = parseFloat(val);
    if (!isNaN(num) && num >= 0) {
        appState.ingredients[idx].dosage = num;
        debouncedEvaluate();
    }
}

function updateIngredientUnit(idx, unit) {
    if (!appState.ingredients[idx]) return;
    const prevUnit = (appState.ingredients[idx].unit || "mg").toUpperCase();
    const newUnit = (unit || "mg").toUpperCase();
    const name = appState.ingredients[idx].name || "";
    let currentDose = parseFloat(appState.ingredients[idx].dosage) || 0;

    // Smart automatic calculation when switching between units (IU <-> mg <-> mcg <-> g)
    if (prevUnit !== newUnit && currentDose > 0) {
        if (prevUnit === 'IU' && newUnit === 'MG') {
            const factor = getIuToMgFactor(name);
            const val = currentDose * factor;
            appState.ingredients[idx].dosage = val < 0.001 ? parseFloat(val.toFixed(6)) : (val < 0.1 ? parseFloat(val.toFixed(4)) : parseFloat(val.toFixed(2)));
        } else if (prevUnit === 'MG' && newUnit === 'IU') {
            const factor = getMgToIuFactor(name);
            appState.ingredients[idx].dosage = Math.round(currentDose * factor);
        } else if (prevUnit === 'IU' && newUnit === 'MCG') {
            const factor = getIuToMgFactor(name) * 1000.0;
            const val = currentDose * factor;
            appState.ingredients[idx].dosage = parseFloat(val.toFixed(3));
        } else if (prevUnit === 'MCG' && newUnit === 'IU') {
            const factor = getMgToIuFactor(name) / 1000.0;
            appState.ingredients[idx].dosage = Math.round(currentDose * factor);
        } else if (prevUnit === 'MCG' && newUnit === 'MG') {
            appState.ingredients[idx].dosage = parseFloat((currentDose / 1000.0).toFixed(4));
        } else if (prevUnit === 'MG' && newUnit === 'MCG') {
            appState.ingredients[idx].dosage = parseFloat((currentDose * 1000.0).toFixed(2));
        } else if (prevUnit === 'G' && newUnit === 'MG') {
            appState.ingredients[idx].dosage = parseFloat((currentDose * 1000.0).toFixed(2));
        } else if (prevUnit === 'MG' && newUnit === 'G') {
            appState.ingredients[idx].dosage = parseFloat((currentDose / 1000.0).toFixed(4));
        } else if (prevUnit === 'G' && newUnit === 'IU') {
            const mgVal = currentDose * 1000.0;
            appState.ingredients[idx].dosage = Math.round(mgVal * getMgToIuFactor(name));
        } else if (prevUnit === 'IU' && newUnit === 'G') {
            const mgVal = currentDose * getIuToMgFactor(name);
            appState.ingredients[idx].dosage = parseFloat((mgVal / 1000.0).toFixed(6));
        }
    }

    appState.ingredients[idx].unit = unit;
    renderIngredientsTable();
    debouncedEvaluate();
}

let rateCheckTimeout = null;
async function refreshMissingRates() {
    if (!appState.ingredients || appState.ingredients.length === 0) return;
    const missing = appState.ingredients.filter(it => it.is_rate_available === undefined || (!it.is_rate_available && (!it.rate || it.rate <= 0)));
    if (missing.length === 0) return;

    const names = missing.map(it => it.name);
    try {
        const res = await fetch("/api/batch-master/check-rates", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ingredients: names })
        });
        const data = await res.json();
        if (data.success && data.results) {
            let updated = false;
            appState.ingredients.forEach(it => {
                const rInfo = data.results[it.name];
                if (rInfo && rInfo.available && Number(rInfo.rate) > 0) {
                    it.is_rate_available = true;
                    it.rate = Number(rInfo.rate);
                    it.rate_matched_name = rInfo.matched_name;
                    updated = true;
                }
            });
            if (updated) {
                renderIngredientsTable();
            }
        }
    } catch (e) {
        console.warn("Could not check rates:", e);
    }
}

function updateIngredientName(idx, name) {
    if (name.trim()) {
        appState.ingredients[idx].name = name.trim();
        appState.ingredients[idx].is_rate_available = undefined;
        appState.ingredients[idx].rate = undefined;
        debouncedEvaluate();
        clearTimeout(rateCheckTimeout);
        rateCheckTimeout = setTimeout(refreshMissingRates, 350);
    }
}

function removeIngredient(idx) {
    appState.ingredients.splice(idx, 1);
    renderIngredientsTable();
    evaluateActiveFormula();
}

function clearAllIngredients() {
    if (confirm("Are you sure you want to clear all ingredients?")) {
        appState.ingredients = [];
        renderIngredientsTable();
        const evalCard = document.getElementById("evaluation-card");
        if (evalCard) evalCard.classList.add("hidden");
    }
}

// Add ingredient from 518 Master Database
function addMasterIngredient(id) {
    const master = appState.masterIngredients.find(m => m.id === id);
    if (!master) return;

    const rateVal = Number(master.rate || master._rate || 0);
    const hasRate = (master.is_rate_available !== undefined ? master.is_rate_available : true) && rateVal > 0;

    appState.ingredients.push({
        id: master.id,
        name: master.name,
        db_raw_name: master.raw_name,
        dosage: master.default_dose || 100,
        unit: master.default_unit || "mg",
        is_matched: true,
        match_score: 100.0,
        confidence: 1.0,
        raw_text: `Added from DB: ${master.raw_name}`,
        is_rate_available: hasRate,
        rate: rateVal,
        rate_matched_name: master.rate_matched_name || master.raw_name || master.name
    });

    closeIngredientsModal();
    renderIngredientsTable();
    evaluateActiveFormula();
    refreshMissingRates();
}

// Master Ingredients Modal (NO PRICES)
function openIngredientsModal() {
    document.getElementById("ingredients-modal").classList.remove("hidden");
    renderModalIngredients(appState.masterIngredients);
    lucide.createIcons();
}

function closeIngredientsModal() {
    document.getElementById("ingredients-modal").classList.add("hidden");
}

function renderModalIngredients(items) {
    const list = document.getElementById("modal-ingredients-list");
    if (!items || items.length === 0) {
        list.innerHTML = `<p class="text-xs text-slate-400 col-span-2 text-center py-8">No ingredients matched your search.</p>`;
        return;
    }

    list.innerHTML = items.map(item => `
        <div class="p-3 bg-white border border-slate-200 rounded-lg hover:border-walpar-500 hover:shadow-sm transition flex items-center justify-between">
            <div class="truncate mr-3">
                <h4 class="text-xs font-bold text-slate-800 truncate">${escapeHtml(item.name)}</h4>
                <p class="text-[10px] text-slate-400 truncate">Source: ${escapeHtml(item.raw_name)}</p>
                <span class="text-[10px] text-slate-500 font-mono">Default: ${item.default_dose} ${item.default_unit}</span>
            </div>
            <button onclick="addMasterIngredient('${item.id}')" 
                    class="px-2.5 py-1.5 bg-walpar-600 hover:bg-walpar-700 text-white rounded text-xs font-medium flex items-center space-x-1 shadow-sm flex-shrink-0 transition">
                <i data-lucide="plus" class="w-3.5 h-3.5"></i>
                <span>Add</span>
            </button>
        </div>
    `).join("");
}

function filterModalIngredients() {
    const q = document.getElementById("modal-search").value.toLowerCase().trim();
    if (!q) {
        renderModalIngredients(appState.masterIngredients);
        document.getElementById("search-count-badge").innerText = `${appState.masterIngredients.length} Items`;
        lucide.createIcons();
        return;
    }
    const filtered = appState.masterIngredients.filter(item => 
        item.name.toLowerCase().includes(q) || 
        item.raw_name.toLowerCase().includes(q) ||
        (item.aliases && item.aliases.some(a => a.toLowerCase().includes(q)))
    );
    renderModalIngredients(filtered);
    document.getElementById("search-count-badge").innerText = `${filtered.length} Items`;
    lucide.createIcons();
}

// Copy Formulation as JSON
function copyFormulaJson() {
    const exportData = appState.ingredients.map(item => ({
        name: item.name,
        dosage: item.dosage,
        unit: item.unit,
        database_match: item.db_raw_name || "Custom"
    }));
    navigator.clipboard.writeText(JSON.stringify(exportData, null, 2)).then(() => {
        alert("Formulation ingredients copied to clipboard as JSON!");
    });
}

// Helpers
function showLoading(show) {
    const spinner = document.getElementById("loading-spinner");
    if (!spinner) return;
    if (show) {
        spinner.classList.remove("hidden");
    } else {
        spinner.classList.add("hidden");
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Scientific Formula Evaluation & AI Suggestions (કેવું છે evaluation & suggestions)
let evalDebounceTimer = null;
function debouncedEvaluate() {
    clearTimeout(evalDebounceTimer);
    evalDebounceTimer = setTimeout(() => {
        evaluateActiveFormula();
    }, 400);
}

async function evaluateActiveFormula() {
    const evalCard = document.getElementById("evaluation-card");
    if (!appState.ingredients || appState.ingredients.length === 0) {
        if (evalCard) evalCard.classList.add("hidden");
        return;
    }

    try {
        const res = await fetch("/api/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                ingredients: appState.ingredients,
                dosage_form: "tablets"
            })
        });
        const data = await res.json();
        if (data.success && data.evaluation) {
            appState.evaluation = data.evaluation;
            renderFormulaEvaluation(data.evaluation);
        }
    } catch (e) {
        console.error("Evaluation error:", e);
    }
}

function renderFormulaEvaluation(evaluation) {
    const card = document.getElementById("evaluation-card");
    if (!card || !evaluation) return;
    card.classList.remove("hidden");

    // Quality Score
    const score = evaluation.score || 80;
    const scoreCircle = document.getElementById("eval-score-circle");
    const statusBadge = document.getElementById("eval-status-badge");

    if (scoreCircle) {
        scoreCircle.innerText = score;
        if (score >= 85) {
            scoreCircle.className = "w-11 h-11 rounded-full border-2 border-emerald-500 flex items-center justify-center font-extrabold text-sm text-emerald-700 bg-emerald-50 shadow-inner";
            statusBadge.className = "text-xs font-bold text-emerald-600";
            statusBadge.innerText = `Excellent (${score}/100)`;
        } else if (score >= 70) {
            scoreCircle.className = "w-11 h-11 rounded-full border-2 border-sky-500 flex items-center justify-center font-extrabold text-sm text-sky-700 bg-sky-50 shadow-inner";
            statusBadge.className = "text-xs font-bold text-sky-600";
            statusBadge.innerText = `Good (${score}/100)`;
        } else {
            scoreCircle.className = "w-11 h-11 rounded-full border-2 border-amber-500 flex items-center justify-center font-extrabold text-sm text-amber-700 bg-amber-50 shadow-inner";
            statusBadge.className = "text-xs font-bold text-amber-600";
            statusBadge.innerText = `Needs Attention (${score}/100)`;
        }
    }

    // Weight and Feasibility
    const activeWeightEl = document.getElementById("eval-active-weight");
    if (activeWeightEl) {
        activeWeightEl.innerText = `${evaluation.total_active_mg || 0} mg`;
    }

    const recFormEl = document.getElementById("eval-form-recommendation");
    if (recFormEl && evaluation.form_feasibility) {
        const formName = evaluation.form_feasibility.recommended_form_name || "Tablet / Capsule";
        recFormEl.innerHTML = `<i data-lucide="pill" class="w-3.5 h-3.5 mr-1 text-walpar-600"></i><span>Optimal Delivery: ${escapeHtml(formName)}</span>`;
    }

    // AI Suggestions (સુધારા / AI Suggestions with 1-click apply button)
    const suggestionsList = document.getElementById("eval-suggestions-list");
    if (suggestionsList) {
        const items = evaluation.suggestions || [];
        if (items.length === 0) {
            suggestionsList.innerHTML = `
                <div class="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg flex items-center space-x-2 text-xs text-emerald-800">
                    <i data-lucide="sparkles" class="w-4 h-4 text-emerald-600 flex-shrink-0"></i>
                    <span>Formulation is balanced. No critical gaps or missing enhancers identified!</span>
                </div>
            `;
        } else {
            suggestionsList.innerHTML = items.map(s => `
                <div class="p-3 bg-amber-50/70 border border-amber-200/80 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div class="space-y-0.5">
                        <div class="flex items-center space-x-2">
                            <span class="font-bold text-amber-950">${escapeHtml(s.title)}</span>
                            <span class="bg-amber-200/70 text-amber-900 text-[10px] font-semibold px-2 py-0.5 rounded">
                                +${s.suggested_dose}${s.suggested_unit}
                            </span>
                        </div>
                        <p class="text-slate-600 text-[11px] leading-relaxed">${escapeHtml(s.description)}</p>
                    </div>
                    <button onclick="applySuggestion('${escapeHtml(s.suggested_ingredient)}', ${s.suggested_dose}, '${escapeHtml(s.suggested_unit)}')"
                            class="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg font-semibold text-xs flex items-center space-x-1.5 transition shadow-sm flex-shrink-0">
                        <i data-lucide="plus-circle" class="w-3.5 h-3.5"></i>
                        <span>Apply Suggestion</span>
                    </button>
                </div>
            `).join("");
        }
    }

    // Active Synergies (ખાસિયતો / Synergies)
    const synergiesList = document.getElementById("eval-synergies-list");
    if (synergiesList) {
        const synergies = evaluation.synergies || [];
        if (synergies.length === 0) {
            synergiesList.innerHTML = `
                <div class="col-span-2 p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500">
                    Add synergistic partners (e.g. Piperine with Curcumin, Zinc with Vitamin C, or K2 with Calcium) to unlock enhanced bio-activity.
                </div>
            `;
        } else {
            synergiesList.innerHTML = synergies.map(syn => `
                <div class="p-3 bg-emerald-50/60 border border-emerald-200 rounded-lg text-xs space-y-1">
                    <div class="flex items-center justify-between">
                        <span class="font-bold text-emerald-950 flex items-center space-x-1">
                            <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-600"></i>
                            <span>${escapeHtml(syn.title)}</span>
                        </span>
                        <span class="bg-emerald-200/80 text-emerald-900 text-[10px] font-bold px-1.5 py-0.5 rounded">
                            ${escapeHtml(syn.badge)}
                        </span>
                    </div>
                    <p class="text-[11px] text-slate-600 leading-snug">${escapeHtml(syn.description)}</p>
                </div>
            `).join("");
        }
    }

    // Clinical Human Effect Matrix (Examine.com database)
    const evidenceSec = document.getElementById("eval-evidence-section");
    const evidenceList = document.getElementById("eval-evidence-list");
    if (evidenceSec && evidenceList) {
        const matrix = evaluation.human_effect_matrix || [];
        if (matrix.length === 0) {
            evidenceSec.classList.add("hidden");
        } else {
            evidenceSec.classList.remove("hidden");
            evidenceList.innerHTML = matrix.map(m => {
                const gradeBadge = m.grade === 'A' 
                    ? '<span class="bg-emerald-100 text-emerald-800 text-[10px] font-bold px-1.5 py-0.5 rounded border border-emerald-300">Grade A RCT</span>'
                    : '<span class="bg-sky-100 text-sky-800 text-[10px] font-bold px-1.5 py-0.5 rounded border border-sky-300">Grade B Evidence</span>';
                
                return `
                    <div class="p-3 bg-white border border-slate-200 rounded-lg text-xs space-y-1 shadow-xs hover:border-indigo-200 transition">
                        <div class="flex items-start justify-between gap-1">
                            <span class="font-bold text-slate-800 text-xs flex items-center space-x-1">
                                <i data-lucide="check" class="w-3.5 h-3.5 text-walpar-600 flex-shrink-0"></i>
                                <span>${escapeHtml(m.outcome)}</span>
                            </span>
                            ${gradeBadge}
                        </div>
                        <div class="flex items-center space-x-2 text-[10px] text-slate-500 font-medium">
                            <span class="text-indigo-600 font-semibold">${escapeHtml(m.ingredient)}</span>
                            <span>•</span>
                            <span class="text-slate-600">${escapeHtml(m.magnitude)}</span>
                        </div>
                        ${m.notes ? `<p class="text-[11px] text-slate-500 leading-snug line-clamp-2">${escapeHtml(m.notes)}</p>` : ''}
                    </div>
                `;
            }).join("");
        }
    }

    // Conflicts / Alerts
    const conflictsSec = document.getElementById("eval-conflicts-section");
    const conflictsList = document.getElementById("eval-conflicts-list");
    if (conflictsSec && conflictsList) {
        const conflicts = evaluation.conflicts || [];
        if (conflicts.length > 0) {
            conflictsSec.classList.remove("hidden");
            conflictsList.innerHTML = conflicts.map(c => `
                <div class="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-900 flex items-start space-x-2">
                    <i data-lucide="alert-circle" class="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5"></i>
                    <div>
                        <strong class="block text-rose-950">${escapeHtml(c.title)}</strong>
                        <p class="text-[11px] text-slate-600 mt-0.5">${escapeHtml(c.description)}</p>
                    </div>
                </div>
            `).join("");
        } else {
            conflictsSec.classList.add("hidden");
        }
    }

    lucide.createIcons();
}

// 1-Click Apply AI Suggestion
function applySuggestion(name, dose, unit) {
    const lowerName = name.toLowerCase();
    const match = appState.masterIngredients.find(m => 
        m.name.toLowerCase().includes(lowerName) || 
        lowerName.includes(m.name.toLowerCase()) ||
        (m.aliases && m.aliases.some(a => a.toLowerCase().includes(lowerName) || lowerName.includes(a.toLowerCase())))
    );

    appState.ingredients.push({
        id: match ? match.id : `suggested_${Date.now()}`,
        name: match ? match.name : name,
        db_raw_name: match ? match.raw_name : name,
        dosage: parseFloat(dose) || 10,
        unit: unit || "mg",
        is_matched: !!match,
        match_score: match ? 100.0 : 90.0,
        confidence: 1.0,
        raw_text: `AI Recommended: ${name} ${dose}${unit}`
    });

    renderIngredientsTable();
    evaluateActiveFormula();
}

// Phone / Mobile QR Modal
function openPhoneModal() {
    const m = document.getElementById("phone-modal");
    if (m) m.classList.remove("hidden");
    lucide.createIcons();
}

function closePhoneModal() {
    const m = document.getElementById("phone-modal");
    if (m) m.classList.add("hidden");
}

function copyPhoneUrl() {
    const txt = document.getElementById("phone-url-text");
    if (txt) {
        const url = txt.innerText.trim();
        navigator.clipboard.writeText(url).then(() => {
            const btn = document.getElementById("copy-phone-btn-text");
            if (btn) {
                btn.innerText = "Copied!";
                setTimeout(() => { btn.innerText = "Copy"; }, 2000);
            }
        }).catch(() => {
            prompt("Copy this URL:", url);
        });
    }
}

// ══════════════════════════════════════════════════════════════
//  BATCH MASTER CARD & BMR FLOW (12.py Integration)
// ══════════════════════════════════════════════════════════════

let bmrState = {
    currentStep: 1,
    productType: "Tablet",
    excipients: [],
    activeIngredients: [],
    lastPayload: null,
    lastResult: null
};

// Open Batch Master Wizard
async function openBatchMasterWizard() {
    const modal = document.getElementById("batch-master-modal");
    if (!modal) return;
    modal.classList.remove("hidden");

    // Initialize Active Ingredients from OCR extracted ingredients
    bmrState.activeIngredients = [];
    if (appState.ingredients && appState.ingredients.length > 0) {
        // Collect names for rate check
        const names = appState.ingredients.map(i => i.name);
        let rateMap = {};
        try {
            const res = await fetch("/api/batch-master/check-rates", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ingredients: names })
            });
            const data = await res.json();
            if (data.success && data.results) {
                rateMap = data.results;
            }
        } catch (e) {
            console.warn("Batch check rates notice:", e);
        }

        for (const item of appState.ingredients) {
            let rawDose = parseFloat(item.dosage) || 50;
            const u = (item.unit || "mg").toLowerCase();
            const nameLower = (item.name || "").toLowerCase();
            let doseMg = rawDose;

            if (u === "g") {
                doseMg = rawDose * 1000;
            } else if (u === "mcg") {
                doseMg = rawDose / 1000;
            } else if (u === "iu") {
                doseMg = rawDose * getIuToMgFactor(item.name);
            }

            const rInfo = rateMap[item.name] || {
                available: item.is_rate_available || false,
                rate: item.rate || 0,
                matched_name: item.rate_matched_name || ""
            };

            let itemRate = rInfo.rate || 0;
            let isUserEstimated = Boolean(item.is_user_estimated);
            let userEstimatedRate = item.user_estimated_rate || 0;
            if (userEstimatedRate > 0) {
                itemRate = userEstimatedRate;
                isUserEstimated = true;
            } else if (item.rate && isUserEstimated) {
                itemRate = item.rate;
            }

            bmrState.activeIngredients.push({
                name: item.name,
                dosage: rawDose,
                unit: item.unit || "mg",
                per_unit_mg: doseMg,
                rate: itemRate,
                is_rate_available: (rInfo.available && Number(rInfo.rate) > 0) || isUserEstimated,
                rate_matched_name: rInfo.matched_name || "",
                is_user_estimated: isUserEstimated,
                user_estimated_rate: userEstimatedRate,
                type: "Extract"
            });
        }
    } else {
        // Fallback default sample if user opened without OCR
        bmrState.activeIngredients.push({
            name: "L-Glutathione",
            per_unit_mg: 500,
            rate: 7246.91,
            is_rate_available: true,
            rate_matched_name: "l-glutathion reduced",
            type: "Extract"
        });
    }

    onBmrProductTypeChange();
    renderBmrActiveIngredients();
    autoCalculateTabletMgAndSize();
    autoCalculateCapsuleMgAndSize();
    goToBmrStep(1);
    lucide.createIcons();
}

function closeBatchMasterWizard() {
    const modal = document.getElementById("batch-master-modal");
    if (modal) modal.classList.add("hidden");
}

// Tablet Active Mg Auto-Calculation & Auto-Sizing Engine
function autoCalculateTabletMgAndSize() {
    if (bmrState.productType !== "Tablet") return;

    let totalActiveMg = 0;
    (bmrState.activeIngredients || []).forEach(it => {
        let mg = parseFloat(it.per_unit_mg) || 0;
        totalActiveMg += mg;
    });

    const sizeSelect = document.getElementById("bmr-tablet-size");
    const badge = document.getElementById("tablet-auto-calc-badge");
    const badgeText = document.getElementById("tablet-auto-calc-text");
    const warnBox = document.getElementById("tablet-limit-warning");
    const warnTitle = document.getElementById("tablet-limit-warning-title");

    if (totalActiveMg > 1800) {
        bmrState.tabletLimitExceeded = true;
        if (warnBox) warnBox.classList.remove("hidden");
        if (warnTitle) warnTitle.innerText = `Active weight (${totalActiveMg.toFixed(1)} mg) exceeds 1800 mg limit for a single tablet`;
        if (badge) badge.classList.add("hidden");
    } else {
        bmrState.tabletLimitExceeded = false;
        if (warnBox) warnBox.classList.add("hidden");
        if (badge) badge.classList.remove("hidden");

        let targetSize = 400;
        if (totalActiveMg < 50) {
            targetSize = 100;
        } else if (totalActiveMg >= 50 && totalActiveMg <= 300) {
            targetSize = 400;
        } else if (totalActiveMg > 300 && totalActiveMg <= 600) {
            targetSize = 900;
        } else if (totalActiveMg > 600 && totalActiveMg <= 800) {
            targetSize = 1000;
        } else if (totalActiveMg > 800 && totalActiveMg <= 1800) {
            targetSize = 1800;
        }

        if (sizeSelect) {
            const prevVal = sizeSelect.value;
            sizeSelect.value = String(targetSize);
            if (prevVal !== String(targetSize)) {
                loadBmrExcipients();
            }
        }

        if (badgeText) {
            badgeText.innerText = `Total Active: ${totalActiveMg.toFixed(1)} mg ➔ Auto-selected ${targetSize} mg Tablet`;
        }
    }
}

// Capsule Active Mg Auto-Calculation & Auto-Sizing Engine
function autoCalculateCapsuleMgAndSize() {
    if (bmrState.productType !== "Capsule") return;

    let totalActiveMg = 0;
    (bmrState.activeIngredients || []).forEach(it => {
        let mg = parseFloat(it.per_unit_mg) || 0;
        totalActiveMg += mg;
    });

    const sizeSelect = document.getElementById("bmr-capsule-size");
    const badge = document.getElementById("capsule-auto-calc-badge");
    const badgeText = document.getElementById("capsule-auto-calc-text");
    const warnBox = document.getElementById("capsule-limit-warning");
    const warnTitle = document.getElementById("capsule-limit-warning-title");

    if (totalActiveMg > 1000) {
        bmrState.capsuleLimitExceeded = true;
        if (warnBox) warnBox.classList.remove("hidden");
        if (warnTitle) warnTitle.innerText = `Active weight (${totalActiveMg.toFixed(1)} mg) exceeds 1000 mg maximum capsule limit (Size 000)`;
        if (badge) badge.classList.add("hidden");
    } else {
        bmrState.capsuleLimitExceeded = false;
        if (warnBox) warnBox.classList.add("hidden");
        if (badge) badge.classList.remove("hidden");

        let targetSize = "00";
        if (totalActiveMg <= 150.0) {
            targetSize = "2";
        } else if (totalActiveMg <= 250.0) {
            targetSize = "1";
        } else if (totalActiveMg <= 450.0) {
            targetSize = "0";
        } else if (totalActiveMg <= 650.0) {
            targetSize = "00";
        } else {
            targetSize = "000";
        }

        if (sizeSelect) {
            sizeSelect.value = targetSize;
        }

        if (badgeText) {
            if (targetSize === "000") {
                badgeText.innerText = `Total Active: ${totalActiveMg.toFixed(1)} mg ➔ Auto-selected Size "000" (Max 1000 mg) | Veg: ₹0.60 / Gelatin: ₹0.30`;
            } else {
                badgeText.innerText = `Total Active: ${totalActiveMg.toFixed(1)} mg ➔ Auto-selected Size "${targetSize}" | Veg: ₹0.48 / Gelatin: ₹0.18`;
            }
        }
    }
}

// Navigate through 4-step wizard
function goToBmrStep(step) {
    if (step < 1 || step > 4) return;

    // Validate Step 1 before proceeding
    if (bmrState.currentStep === 1 && step > 1) {
        if (bmrState.productType === "Tablet") {
            const el = document.getElementById("bmr-tablet-qty");
            const qty = parseInt(el?.value || 0);
            if (qty < 100000) {
                alert("Minimum batch size for Tablet is 1,00,000 tablets. You can enter higher quantities, but not lower than 1,00,000.");
                if (el) el.value = 100000;
                return;
            }
        } else if (bmrState.productType === "Capsule") {
            const el = document.getElementById("bmr-capsule-qty");
            const qty = parseInt(el?.value || 0);
            if (qty < 100000) {
                alert("Minimum batch size for Capsule is 1,00,000 capsules. You can enter higher quantities, but not lower than 1,00,000.");
                if (el) el.value = 100000;
                return;
            }
        } else {
            const qty = getBmrQuantity();
            if (qty <= 0) {
                alert("Please enter a valid batch quantity greater than 0.");
                return;
            }
        }
    }

    // Check tablet limit (>1800mg)
    if (bmrState.productType === "Tablet" && bmrState.tabletLimitExceeded && step === 4) {
        alert("Active ingredients total exceeds 1800 mg for a single tablet. Please contact with us. Batch calculation is disabled.");
        return;
    }

    // Check capsule limit (>1000mg)
    if (bmrState.productType === "Capsule" && bmrState.capsuleLimitExceeded && step === 4) {
        alert("Active ingredients total exceeds 1000 mg for a single capsule (Size 000). Please contact with us. Batch calculation is disabled.");
        return;
    }

    bmrState.currentStep = step;

    // Show/hide step panels (1 to 4)
    for (let i = 1; i <= 4; i++) {
        const panel = document.getElementById(`bmr-step-panel-${i}`);
        if (panel) panel.classList.toggle("hidden", i !== step);

        // Update nav pill
        const nav = document.getElementById(`step-nav-${i}`);
        if (nav) {
            const badge = nav.querySelector("span:first-child");
            if (i === step) {
                nav.className = "flex items-center space-x-2 text-teal-700 font-bold whitespace-nowrap cursor-pointer";
                if (badge) badge.className = "w-6 h-6 rounded-full bg-teal-600 text-white flex items-center justify-center text-[11px] shadow-sm";
            } else if (i < step) {
                nav.className = "flex items-center space-x-2 text-emerald-700 font-semibold whitespace-nowrap cursor-pointer";
                if (badge) badge.className = "w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center justify-center text-[11px]";
            } else {
                nav.className = "flex items-center space-x-2 text-slate-400 whitespace-nowrap cursor-pointer";
                if (badge) badge.className = "w-6 h-6 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-[11px]";
            }
        }
    }

    // Update bottom footer navigation
    const prevBtn = document.getElementById("bmr-prev-btn");
    const nextBtn = document.getElementById("bmr-next-btn");

    if (prevBtn) prevBtn.classList.toggle("hidden", step === 1);
    if (nextBtn) {
        if (step === 4) {
            nextBtn.classList.add("hidden");
        } else {
            nextBtn.classList.remove("hidden");
            const labels = ["Next: Active Ingredients", "Next: Packaging", "Calculate & View Product Rates"];
            nextBtn.innerHTML = `<span>${labels[step - 1]}</span> <i data-lucide="chevron-right" class="w-4 h-4"></i>`;
        }
    }

    // Step-specific activations
    if (step === 2) {
        renderBmrActiveIngredients();
    } else if (step === 4) {
        calculateAndShowBmr();
    }

    if (window.lucide) lucide.createIcons();
}

function nextBmrStep() {
    goToBmrStep(bmrState.currentStep + 1);
}

function prevBmrStep() {
    goToBmrStep(bmrState.currentStep - 1);
}

// Product Type Change: Tablet | Capsule | Liquid
function onBmrProductTypeChange() {
    const radios = document.getElementsByName("bmr_product_type");
    for (const r of radios) {
        if (r.checked) {
            bmrState.productType = r.value;
            break;
        }
    }

    // Highlight selected card
    ["tablet", "capsule", "liquid"].forEach(t => {
        const card = document.getElementById(`card-type-${t}`);
        const isSel = bmrState.productType.toLowerCase() === t;
        if (card) {
            card.classList.toggle("border-teal-500", isSel);
            card.classList.toggle("bg-teal-50/50", isSel);
            card.classList.toggle("border-slate-200", !isSel);
        }
    });

    // Auto-calculate size if tablet or capsule
    if (bmrState.productType === "Tablet") {
        autoCalculateTabletMgAndSize();
    } else if (bmrState.productType === "Capsule") {
        autoCalculateCapsuleMgAndSize();
    }

    // Toggle specific option fields in Step 1
    const tabF = document.getElementById("bmr-tablet-fields");
    const capF = document.getElementById("bmr-capsule-fields");
    const liqF = document.getElementById("bmr-liquid-fields");
    if (tabF) tabF.classList.toggle("hidden", bmrState.productType !== "Tablet");
    if (capF) capF.classList.toggle("hidden", bmrState.productType !== "Capsule");
    if (liqF) liqF.classList.toggle("hidden", bmrState.productType !== "Liquid");

    // Toggle Step 4 packaging box
    const tabPkg = document.getElementById("bmr-pkg-tablet-box");
    const liqPkg = document.getElementById("bmr-pkg-liquid-box");
    if (tabPkg) tabPkg.classList.toggle("hidden", bmrState.productType === "Liquid");
    if (liqPkg) liqPkg.classList.toggle("hidden", bmrState.productType !== "Liquid");

    loadBmrExcipients();
}

function getBmrQuantity() {
    if (bmrState.productType === "Tablet") {
        const val = parseInt(document.getElementById("bmr-tablet-qty")?.value);
        return (!val || val < 100000) ? 100000 : val;
    } else if (bmrState.productType === "Capsule") {
        const val = parseInt(document.getElementById("bmr-capsule-qty")?.value);
        return (!val || val < 100000) ? 100000 : val;
    } else {
        return parseInt(document.getElementById("bmr-liquid-qty")?.value) || 5000;
    }
}

function getBmrSize() {
    if (bmrState.productType === "Tablet") {
        return parseInt(document.getElementById("bmr-tablet-size").value) || 400;
    } else if (bmrState.productType === "Capsule") {
        return document.getElementById("bmr-capsule-size").value || "00";
    } else {
        const sel = document.getElementById("bmr-bottle-size")?.value || "200 ml";
        if (sel === "custom") {
            const custVal = parseFloat(document.getElementById("bmr-custom-bottle-ml")?.value) || 200;
            return `${custVal} ml`;
        }
        return sel;
    }
}

function getBmrServingSize() {
    const sel = document.getElementById("bmr-serving-size")?.value || "10 ml";
    if (sel === "custom") {
        const custVal = parseFloat(document.getElementById("bmr-custom-serving-ml")?.value) || 10;
        return `${custVal} ml`;
    }
    return sel;
}

function onBottleSizeChange() {
    const sel = document.getElementById("bmr-bottle-size");
    const custInput = document.getElementById("bmr-custom-bottle-ml");
    if (!sel) return;
    const isCustom = sel.value === "custom";
    if (custInput) {
        custInput.classList.toggle("hidden", !isCustom);
        if (isCustom && !custInput.value) custInput.value = "200";
    }
    
    // Check if bottle size is < 60 mL to flag dropper recommendation
    const volStr = getBmrSize();
    const volNum = parseFloat(volStr) || 200;
    const dropperBox = document.getElementById("bmr-dropper-box");
    const dropperSel = document.getElementById("bmr-liq-dropper");
    if (dropperBox && dropperSel) {
        if (volNum < 60) {
            dropperBox.classList.add("ring-2", "ring-teal-400", "rounded-lg", "p-1");
            dropperSel.value = "yes";
        } else {
            dropperBox.classList.remove("ring-2", "ring-teal-400", "rounded-lg", "p-1");
        }
    }

    if (bmrState.currentStep === 2) {
        renderBmrActiveIngredients();
    }
}

function onServingSizeChange() {
    const sel = document.getElementById("bmr-serving-size");
    const custInput = document.getElementById("bmr-custom-serving-ml");
    if (!sel) return;
    const isCustom = sel.value === "custom";
    if (custInput) {
        custInput.classList.toggle("hidden", !isCustom);
        if (isCustom && !custInput.value) custInput.value = "10";
    }
    if (bmrState.currentStep === 2) {
        renderBmrActiveIngredients();
    }
}

function onSugarBaseChange() {
    const type = document.getElementById("bmr-sugar-type")?.value || "Sugar";
    const concBox = document.getElementById("bmr-sugar-conc-box");
    if (concBox) {
        concBox.classList.toggle("hidden", type !== "Sugar");
    }
}

function onLiqPkgModeChange() {
    const radios = document.getElementsByName("bmr_liq_pkg_mode");
    let mode = "MODE_A";
    for (const r of radios) {
        if (r.checked) { mode = r.value; break; }
    }
    const notice = document.getElementById("bmr-mode-a-notice");
    if (notice) {
        notice.classList.toggle("hidden", mode !== "MODE_A");
    }
}

// Load default excipients from backend API
async function loadBmrExcipients() {
    const listEl = document.getElementById("bmr-excipients-list");
    if (!listEl) return;
    listEl.innerHTML = `<div class="p-4 text-center text-xs text-slate-500">Loading standard excipients...</div>`;

    try {
        const size = getBmrSize();
        const res = await fetch(`/api/batch-master/excipients?product_type=${bmrState.productType}&tablet_size=${size}`);
        const data = await res.json();
        bmrState.excipients = data.excipients || [];
        renderBmrExcipients();
    } catch (e) {
        listEl.innerHTML = `<div class="p-4 text-rose-600 text-xs">Failed to load excipients: ${e.message}</div>`;
    }
}

function renderBmrExcipients() {
    const listEl = document.getElementById("bmr-excipients-list");
    if (!listEl) return;

    // Group excipients
    const groups = {};
    bmrState.excipients.forEach((item, idx) => {
        const g = item.group || "Excipients";
        if (!groups[g]) groups[g] = [];
        groups[g].push({ ...item, origIdx: idx });
    });

    let html = "";
    for (const [groupName, items] of Object.entries(groups)) {
        html += `
            <div class="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm space-y-2">
                <div class="flex items-center justify-between pb-2 border-b border-slate-100">
                    <span class="text-xs font-extrabold text-slate-800 uppercase tracking-wide flex items-center space-x-1.5">
                        <i data-lucide="check-square" class="w-3.5 h-3.5 text-teal-600"></i>
                        <span>${escapeHtml(groupName)}</span>
                    </span>
                    <button type="button" onclick="toggleGroupExcipients('${escapeHtml(groupName)}', true)" class="text-[10px] text-teal-700 hover:underline font-semibold">Select All</button>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 pt-1">
                    ${items.map(it => `
                        <label class="flex items-center space-x-2 text-xs text-slate-700 cursor-pointer p-1.5 rounded hover:bg-slate-50">
                            <input type="checkbox" id="exc-chk-${it.origIdx}" ${it.selected ? 'checked' : ''} onchange="bmrState.excipients[${it.origIdx}].selected = this.checked" class="rounded text-teal-600 focus:ring-teal-500">
                            <span class="truncate" title="${escapeHtml(it.name)}">${escapeHtml(it.name)}</span>
                        </label>
                    `).join("")}
                </div>
            </div>
        `;
    }
    listEl.innerHTML = html;
    lucide.createIcons();
}

function toggleAllExcipients(selected) {
    bmrState.excipients.forEach((it, idx) => {
        it.selected = selected;
        const chk = document.getElementById(`exc-chk-${idx}`);
        if (chk) chk.checked = selected;
    });
}

function toggleGroupExcipients(groupName, selected) {
    bmrState.excipients.forEach((it, idx) => {
        if ((it.group || "Excipients") === groupName) {
            it.selected = selected;
            const chk = document.getElementById(`exc-chk-${idx}`);
            if (chk) chk.checked = selected;
        }
    });
}

// Render Step 3 Active Ingredients Table
function renderBmrActiveIngredients() {
    const tbody = document.getElementById("bmr-active-table-body");
    if (!tbody) return;

    const qty = getBmrQuantity();
    const isLiquid = bmrState.productType === "Liquid";
    let bottleMl = 200;
    let srvMl = 10;
    if (isLiquid) {
        try {
            bottleMl = parseFloat(getBmrSize()) || 200;
            srvMl = parseFloat(getBmrServingSize()) || 10;
        } catch (e) {}
    }
    const servingsPerBottle = srvMl > 0 ? (bottleMl / srvMl) : 1;
    const totalServings = qty * servingsPerBottle;

    // Hide rate warning banner if present
    const warnBanner = document.getElementById("bmr-rate-warning-banner");
    if (warnBanner) {
        warnBanner.classList.add("hidden");
        warnBanner.innerHTML = "";
    }

    tbody.innerHTML = bmrState.activeIngredients.map((item, idx) => {
        let totalBatchKg = 0;
        if (isLiquid) {
            totalBatchKg = (item.per_unit_mg * totalServings) / 1000000;
        } else {
            totalBatchKg = (item.per_unit_mg * qty) / 1000000;
        }

        const isDbRate = item.is_rate_available && !item.is_user_estimated && Number(item.rate) > 0;
        const currentRateVal = item.user_estimated_rate || item.rate || "";

        return `
            <tr class="hover:bg-slate-50 transition text-xs">
                <td class="py-2.5 px-3">
                    <input type="text" value="${escapeHtml(item.name)}" oninput="updateActiveIngr(${idx}, 'name', this.value)" class="w-full text-xs p-1.5 border border-slate-200 rounded font-sans font-medium focus:ring-teal-500">
                </td>
                <td class="py-2.5 px-3">
                    ${item.unit && item.unit.toUpperCase() === 'IU' ? `
                        <div class="flex items-center space-x-1.5">
                            <span class="text-xs font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200 font-mono">${item.dosage || Math.round(item.per_unit_mg * getMgToIuFactor(item.name))} IU</span>
                            <span class="text-[10px] text-slate-500 font-mono">(${item.per_unit_mg < 0.001 ? item.per_unit_mg.toFixed(6) : (item.per_unit_mg < 0.1 ? item.per_unit_mg.toFixed(4) : item.per_unit_mg.toFixed(2))} mg)</span>
                        </div>
                    ` : `
                        <div class="flex items-center space-x-1">
                            <input type="number" value="${item.per_unit_mg}" step="0.1" min="0.0001" oninput="updateActiveIngr(${idx}, 'per_unit_mg', parseFloat(this.value)||0)" class="w-24 text-xs p-1.5 border border-slate-200 rounded font-mono font-bold focus:ring-teal-500">
                            <span class="text-[11px] text-slate-500 font-sans">mg</span>
                        </div>
                    `}
                </td>
                <td class="py-2.5 px-3 text-right">
                    <span class="font-bold text-slate-800 font-mono">${totalBatchKg.toFixed(4)} Kg</span>
                </td>
                <td class="py-2.5 px-3 text-right">
                    ${isDbRate ? `
                        <div class="flex flex-col items-end justify-center py-0.5">
                            <span class="inline-flex items-center text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-300 px-2.5 py-1 rounded-md shadow-2xs">
                                <i data-lucide="check-circle-2" class="w-3.5 h-3.5 mr-1 text-emerald-600"></i> Official DB
                            </span>
                            <span class="text-[9px] text-slate-400 font-sans mt-0.5 font-medium">Rate secured in database</span>
                        </div>
                    ` : `
                        <div class="flex flex-col items-end space-y-1">
                            <div class="flex items-center space-x-1 justify-end">
                                <span class="text-xs font-bold ${item.rate > 0 ? 'text-amber-700' : 'text-rose-500'}">₹</span>
                                <input type="number" step="0.01" min="0" 
                                       value="${currentRateVal}" 
                                       placeholder="Est. Rate/Kg"
                                       onchange="updateActiveIngr(${idx}, 'rate', parseFloat(this.value)||0)" 
                                       class="w-28 text-xs p-1 text-right border-2 ${item.rate > 0 ? 'border-amber-400 bg-amber-50 text-slate-900' : 'border-rose-300 bg-rose-50/80 text-slate-900'} rounded-md font-mono font-bold focus:bg-white focus:border-amber-500 focus:ring-1 focus:ring-amber-500 shadow-2xs">
                                <span class="text-[10px] text-slate-400 font-medium font-mono">/ kg</span>
                            </div>
                            <span class="text-[9px] ${item.rate > 0 ? 'text-amber-800 bg-amber-100 border border-amber-300' : 'text-rose-700 bg-rose-50 border border-rose-200'} font-bold px-1.5 py-0.5 rounded shadow-2xs flex items-center">
                                ${item.rate > 0 ? '<i data-lucide="edit-3" class="w-3 h-3 mr-1 text-amber-600"></i> User Estimated (Audited)' : '<i data-lucide="alert-circle" class="w-3 h-3 mr-1 text-rose-500"></i> Fill Estimated Rate'}
                            </span>
                        </div>
                    `}
                </td>
                <td class="py-2.5 px-3 text-center">
                    <button type="button" onclick="removeActiveRow(${idx})" class="text-rose-500 hover:text-rose-700 p-1" title="Remove ingredient">
                        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join("");

    lucide.createIcons();
}

function updateActiveIngr(idx, field, val) {
    if (bmrState.activeIngredients[idx]) {
        bmrState.activeIngredients[idx][field] = val;
        if (field === 'rate') {
            const numRate = parseFloat(val) || 0;
            bmrState.activeIngredients[idx].rate = numRate;
            bmrState.activeIngredients[idx].user_estimated_rate = numRate;
            bmrState.activeIngredients[idx].is_user_estimated = true;
            bmrState.activeIngredients[idx].is_rate_available = numRate > 0;

            const ingName = bmrState.activeIngredients[idx].name;
            const matchInAppState = appState.ingredients.find(i => i.name.toLowerCase() === ingName.toLowerCase());
            if (matchInAppState) {
                matchInAppState.rate = numRate;
                matchInAppState.user_estimated_rate = numRate;
                matchInAppState.is_user_estimated = true;
                matchInAppState.is_rate_available = numRate > 0;
                renderIngredientsTable();
            }

            if (numRate > 0) {
                fetch("/api/batch-master/log-estimated-rate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        ingredient_name: ingName,
                        estimated_rate: numRate,
                        product_type: bmrState.productType || "Tablet"
                    })
                }).catch(e => console.warn("Failed to log estimated rate:", e));
            }

            renderBmrActiveIngredients();
        } else if (field === 'per_unit_mg') {
            renderBmrActiveIngredients();
            autoCalculateTabletMgAndSize();
            autoCalculateCapsuleMgAndSize();
        }
    }
}

function addCustomActiveRow(name = "Active Extract", mg = 50, rate = 0) {
    bmrState.activeIngredients.push({
        name: name,
        per_unit_mg: mg,
        rate: rate,
        is_rate_available: rate > 0,
        type: "Extract"
    });
    renderBmrActiveIngredients();
    autoCalculateTabletMgAndSize();
    autoCalculateCapsuleMgAndSize();
}

function removeActiveRow(idx) {
    bmrState.activeIngredients.splice(idx, 1);
    renderBmrActiveIngredients();
    autoCalculateTabletMgAndSize();
    autoCalculateCapsuleMgAndSize();
}

// Step 3 Primary Packaging Radio Switch
function onBmrPrimaryChange() {
    const radios = document.getElementsByName("bmr_primary_type");
    let val = "STRIP";
    for (const r of radios) {
        if (r.checked) { val = r.value; break; }
    }
    const stripOpts = document.getElementById("bmr-strip-opts");
    const jarOpts = document.getElementById("bmr-jar-opts");
    const looseOpts = document.getElementById("bmr-loose-opts");
    if (stripOpts) stripOpts.classList.toggle("hidden", val !== "STRIP");
    if (jarOpts) jarOpts.classList.toggle("hidden", val !== "JAR");
    if (looseOpts) looseOpts.classList.toggle("hidden", val !== "LOOSE");
}

// Master BMR Lock & Password State (Walpar@123)
let bmrUnlocked = false;
let bmrMasterPassword = "";

function promptUnlockBmrModal() {
    const modal = document.getElementById("bmr-password-modal");
    if (modal) modal.classList.remove("hidden");
    const input = document.getElementById("bmr-master-pass-input");
    if (input) {
        input.value = "";
        input.focus();
    }
    const err = document.getElementById("bmr-pass-error");
    if (err) err.classList.add("hidden");
    if (window.lucide) lucide.createIcons();
}

function closeBmrPasswordModal() {
    const modal = document.getElementById("bmr-password-modal");
    if (modal) modal.classList.add("hidden");
}

async function submitBmrMasterPassword() {
    const input = document.getElementById("bmr-master-pass-input");
    const err = document.getElementById("bmr-pass-error");
    const pwd = input ? input.value.trim() : "";

    if (!pwd) {
        if (err) {
            err.innerText = "Please enter Master Password";
            err.classList.remove("hidden");
        }
        return;
    }

    try {
        const res = await fetch("/api/batch-master/verify-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: pwd, action: "unlock_and_download" })
        });
        const data = await res.json();
        if (!data.success) {
            if (err) {
                err.innerText = data.error || "Incorrect Master Password. Access Denied.";
                err.classList.remove("hidden");
            }
            return;
        }

        bmrUnlocked = true;
        bmrMasterPassword = pwd;
        closeBmrPasswordModal();

        // Unlock BMR Card View
        const lockedContainer = document.getElementById("bmr-locked-container");
        const unlockedContainer = document.getElementById("bmr-unlocked-container");
        if (lockedContainer) lockedContainer.classList.add("hidden");
        if (unlockedContainer) unlockedContainer.classList.remove("hidden");
        if (window.lucide) lucide.createIcons();

        // Download Excel directly
        exportBmrExcel();
    } catch (e) {
        if (err) {
            err.innerText = "Verification failed: " + e.message;
            err.classList.remove("hidden");
        }
    }
}

// Step 5: Execute Calculation Engine & Render Master Card
async function calculateAndShowBmr() {
    const tbody = document.getElementById("bmr-output-table-body");
    if (!tbody) return;

    const productType = bmrState.productType;

    // Strict Check: Tablet Active > 1800mg limit
    if (productType === "Tablet" && bmrState.tabletLimitExceeded) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-rose-600 font-bold text-sm">Please contact with us — Total active ingredients exceed 1800 mg for a single tablet. Calculation disabled.</td></tr>`;
        const lockedContainer = document.getElementById("bmr-locked-container");
        const unlockedContainer = document.getElementById("bmr-unlocked-container");
        if (unlockedContainer) unlockedContainer.classList.add("hidden");
        if (lockedContainer) {
            lockedContainer.classList.remove("hidden");
            lockedContainer.innerHTML = `
                <div class="w-16 h-16 rounded-full bg-rose-50 border border-rose-200 text-rose-700 flex items-center justify-center mx-auto shadow-inner">
                    <i data-lucide="alert-octagon" class="w-8 h-8 text-rose-600"></i>
                </div>
                <div class="max-w-md mx-auto">
                    <h4 class="text-base font-extrabold text-rose-800">Please Contact With Us</h4>
                    <p class="text-xs text-rose-600 mt-1">Total active ingredients exceed 1800 mg. Single tablet compression is not feasible. Calculation and batch card are not displayed. Please contact Walpar technical formulation support.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
        }
        return;
    }

    // Strict Check: Capsule Active > 1000mg limit
    if (productType === "Capsule" && bmrState.capsuleLimitExceeded) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-rose-600 font-bold text-sm">Please contact with us — Total active ingredients exceed 1000 mg for a single capsule (Size 000). Calculation disabled.</td></tr>`;
        const lockedContainer = document.getElementById("bmr-locked-container");
        const unlockedContainer = document.getElementById("bmr-unlocked-container");
        if (unlockedContainer) unlockedContainer.classList.add("hidden");
        if (lockedContainer) {
            lockedContainer.classList.remove("hidden");
            lockedContainer.innerHTML = `
                <div class="w-16 h-16 rounded-full bg-rose-50 border border-rose-200 text-rose-700 flex items-center justify-center mx-auto shadow-inner">
                    <i data-lucide="alert-octagon" class="w-8 h-8 text-rose-600"></i>
                </div>
                <div class="max-w-md mx-auto">
                    <h4 class="text-base font-extrabold text-rose-800">Please Contact With Us</h4>
                    <p class="text-xs text-rose-600 mt-1">Total active ingredients exceed 1000 mg. Single capsule encapsulation is not feasible even in Size "000". Calculation and batch card are not displayed. Please contact Walpar technical formulation support.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
        }
        return;
    }

    // Toggle locked / unlocked container based on bmrUnlocked state
    const lockedContainer = document.getElementById("bmr-locked-container");
    const unlockedContainer = document.getElementById("bmr-unlocked-container");
    if (bmrUnlocked) {
        if (lockedContainer) lockedContainer.classList.add("hidden");
        if (unlockedContainer) unlockedContainer.classList.remove("hidden");
    } else {
        if (lockedContainer) lockedContainer.classList.remove("hidden");
        if (unlockedContainer) unlockedContainer.classList.add("hidden");
    }

    tbody.innerHTML = `<tr><td colspan="7" class="p-8 text-center text-xs text-slate-500"><div class="inline-block animate-spin rounded-full h-6 w-6 border-2 border-teal-600 border-t-transparent mb-2"></div><p>Calculating Theoretical Formulations &amp; Material Quantities...</p></td></tr>`;

    const quantity = getBmrQuantity();
    const sizeOrCapsule = getBmrSize();

    // Packaging details
    let packagingPayload = {};
    if (productType === "Liquid") {
        const bottleSizeStr = String(sizeOrCapsule);
        const shipperParts = (document.getElementById("bmr-liq-shipper")?.value || "60 nos|5ply").split("|");
        const liqPkgModeRadios = document.getElementsByName("bmr_liq_pkg_mode");
        let liqPkgMode = "MODE_A";
        for (const r of liqPkgModeRadios) {
            if (r.checked) { liqPkgMode = r.value; break; }
        }

        packagingPayload = {
            pkg_mode: liqPkgMode,
            bottle_type: document.getElementById("bmr-liq-bottle-type")?.value || "round brute",
            ropp_type: document.getElementById("bmr-liq-ropp-type")?.value || "quality",
            include_dropper: document.getElementById("bmr-liq-dropper")?.value === "yes",
            include_measuring_cup: document.getElementById("bmr-liq-cup")?.value === "yes",
            carton_type: document.getElementById("bmr-liq-carton")?.value || "uv dripp off",
            label_type: document.getElementById("bmr-liq-label")?.value || "chromo",
            include_insert: document.getElementById("bmr-liq-insert")?.value === "yes",
            shipper_capacity: shipperParts[0] || "60 nos",
            shipper_ply: shipperParts[1] || "5ply",
            include_accessories: true
        };
    } else {
        const primaryRadio = Array.from(document.getElementsByName("bmr_primary_type")).find(r => r.checked);
        packagingPayload = {
            include_primary: document.getElementById("bmr-inc-primary")?.checked ?? true,
            primary_type: primaryRadio ? primaryRadio.value : "STRIP",
            strip_type: document.getElementById("bmr-strip-type")?.value || "Alu Alu",
            strip_size: document.getElementById("bmr-strip-size")?.value || "1*10",
            jar_type: document.getElementById("bmr-jar-type")?.value || "PET",
            cap_type: document.getElementById("bmr-cap-type")?.value || "CRC",
            tablets_per_jar: parseInt(document.getElementById("bmr-tablets-per-jar")?.value) || 60,
            loose_type: document.getElementById("bmr-loose-type")?.value || "aluminum pouch",
            tablets_per_loose: parseInt(document.getElementById("bmr-tablets-per-loose")?.value) || 1000,
            include_secondary: document.getElementById("bmr-inc-secondary")?.checked ?? true,
            secondary_method: document.getElementById("bmr-sec-method")?.value || "Individual Carton",
            material_type: document.getElementById("bmr-mat-type")?.value || "350 GSM",
            secondary_size: document.getElementById("bmr-sec-size")?.value || "1*10",
            include_tertiary: document.getElementById("bmr-inc-tertiary")?.checked ?? true,
            tertiary_type: document.getElementById("bmr-tert-type")?.value || "5 PLY",
            include_cellotape: document.getElementById("bmr-inc-cellotape")?.checked ?? true
        };
    }

    const payload = {
        product_type: productType,
        product_name: productType === "Liquid" ? (document.getElementById("bmr-liquid-product-name")?.value || "OSSOFY P suspension 200 ml") : null,
        party_name: productType === "Liquid" ? (document.getElementById("bmr-liq-party")?.value || "Walpar Standard Quotation") : null,
        quantity: quantity,
        size_or_capsule: sizeOrCapsule,
        capsule_type: productType === "Capsule" ? document.getElementById("bmr-capsule-type").value : null,
        serving_size: productType === "Liquid" ? getBmrServingSize() : null,
        sugar_type: productType === "Liquid" ? document.getElementById("bmr-sugar-type")?.value : null,
        sugar_percent: productType === "Liquid" ? document.getElementById("bmr-sugar-percent")?.value : null,
        xanthan_gum_qty: productType === "Liquid" ? (parseFloat(document.getElementById("bmr-xanthan-gum-qty")?.value) || 0.62) : null,
        include_preservatives: productType === "Liquid" ? (document.getElementById("bmr-preservatives-req")?.value === "yes") : true,
        yield_percent: productType === "Liquid" ? (parseFloat(document.getElementById("bmr-yield-percent")?.value) || 100.0) : 100.0,
        active_ingredients: bmrState.activeIngredients,
        selected_excipients: bmrState.excipients,
        packaging: packagingPayload
    };

    bmrState.lastPayload = payload;

    try {
        const res = await fetch("/api/batch-master/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!result.success) throw new Error(result.error || "Calculation failed");
        bmrState.lastResult = result;

        // Subtitle
        const sub = document.getElementById("bmr-output-subtitle");
        if (sub) {
            sub.innerText = `Product: ${result.product_type} | Batch Size: ${result.quantity.toLocaleString()} units | Total Formula Mass: ${result.total_batch_kg} Kg`;
        }

        // Render table rows (7 Columns: Sr, Stage/Group, Ingredient Name, Type, Qty Kg, Qty g, Qty per Unit)
        let rowsHtml = "";
        let currentGroup = null;
        (result.items || []).forEach(it => {
            if (it.group !== currentGroup) {
                currentGroup = it.group;
                rowsHtml += `
                    <tr class="bg-teal-50/80 font-sans font-bold border-y border-teal-200">
                        <td colspan="7" class="py-1.5 px-3 text-teal-900 tracking-wider text-[11px] uppercase">${escapeHtml(currentGroup)}</td>
                    </tr>
                `;
            }

            const isUnpriced = it.is_rate_available === false || it.rate === 0;
            const unpricedBadge = (isUnpriced && (it.group || '').includes("Active")) 
                ? ` <span class="ml-1.5 px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-[9px] font-bold border border-amber-300">⚠️ Rate Pending Admin Entry</span>` 
                : '';

            rowsHtml += `
                <tr class="hover:bg-slate-50 text-[11px] ${isUnpriced && (it.group || '').includes('Active') ? 'bg-amber-50/40' : ''}">
                    <td class="py-2 px-3 text-center text-slate-400 font-sans">${it.sr_no}</td>
                    <td class="py-2 px-3 text-slate-500 font-sans">${escapeHtml(it.group)}</td>
                    <td class="py-2 px-3 font-semibold text-slate-800 font-sans flex items-center flex-wrap">
                        <span>${escapeHtml(it.name)}</span>
                        ${unpricedBadge}
                    </td>
                    <td class="py-2 px-3 text-slate-500 font-sans">${escapeHtml(it.type)}</td>
                    <td class="py-2 px-3 text-right font-bold text-slate-900">${it.qty_kg.toFixed(4)}</td>
                    <td class="py-2 px-3 text-right text-slate-600">${it.qty_g.toFixed(1)}</td>
                    <td class="py-2 px-3 text-right font-sans text-slate-600">${escapeHtml(it.qty_per_unit || "")}</td>
                </tr>
            `;
        });

        // Totals Row (Strictly Batch Mass & Quantities)
        rowsHtml += `
            <tr class="bg-teal-900 text-white font-bold font-mono">
                <td colspan="4" class="py-2.5 px-3 text-right font-sans uppercase">TOTAL FORMULATION BATCH WEIGHT:</td>
                <td class="py-2.5 px-3 text-right font-black text-emerald-300">${result.total_batch_kg.toFixed(4)} Kg</td>
                <td class="py-2.5 px-3 text-right font-black text-emerald-300">${(result.total_batch_kg * 1000).toFixed(1)} g</td>
                <td></td>
            </tr>
        `;
        // Toggle table containers
        const tabletTableContainer = document.getElementById("bmr-tablet-table-container");
        const liquidMasterContainer = document.getElementById("bmr-liquid-master-card-container");
        if (productType === "Liquid" && result.liquid_master_card) {
            if (tabletTableContainer) tabletTableContainer.classList.add("hidden");
            if (liquidMasterContainer) {
                liquidMasterContainer.classList.remove("hidden");
                renderLiquidMasterBatchCard(result.liquid_master_card);
            }
        } else {
            if (tabletTableContainer) tabletTableContainer.classList.remove("hidden");
            if (liquidMasterContainer) liquidMasterContainer.classList.add("hidden");
        }

        // ═══════════════════════════════════════════════════════
        // Commercial Product Rates Quotation (Rate per Jar / Strip / Loose)
        // ═══════════════════════════════════════════════════════
        const fin = result.financials || {};
        const safeSet = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.innerText = val;
        };

        safeSet("rate-batch-qty", `${result.quantity.toLocaleString()} Units`);
        safeSet("rate-total-weight-sub", `Net Weight: ${result.total_batch_kg.toFixed(3)} Kg`);
        safeSet("rate-total-batch-val", (fin.total_batch_cost_with_profit || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));

        const unitName = productType === "Capsule" ? "Capsule" : (productType === "Liquid" ? "Serving" : "Tablet");
        safeSet("rate-unit-label", `Rate Per ${unitName}`);
        safeSet("rate-per-unit-val", (fin.rate_per_unit || 0).toFixed(2));
        safeSet("rate-per-unit-sub", `Single ${unitName.toLowerCase()} conversion & raw formulation`);

        if (productType === "Liquid") {
            safeSet("rate-primary-label", "Rate Per Bottle");
            safeSet("rate-primary-val", (fin.profit_per_bottle || 0).toFixed(2));
            safeSet("rate-primary-sub", `Per ${sizeOrCapsule} bottle (incl. ROPP, carton & shipper)`);
            safeSet("rate-product-desc", `Liquid syrup quotation for ${result.quantity.toLocaleString()} bottles of ${sizeOrCapsule}.`);
        } else {
            const primType = packagingPayload.primary_type || "STRIP";
            if (primType === "JAR") {
                const tabsPerJar = packagingPayload.tablets_per_jar || 60;
                safeSet("rate-primary-label", "Rate Per Jar");
                safeSet("rate-primary-val", (fin.profit_per_jar || 0).toFixed(2));
                safeSet("rate-primary-sub", `Per jar of ${tabsPerJar} ${unitName.toLowerCase()}s (PET/HDPE + cap)`);
                safeSet("rate-product-desc", `Jar pack quotation for ${tabsPerJar} ${unitName.toLowerCase()}s per jar, batch of ${result.quantity.toLocaleString()} units.`);
            } else if (primType === "LOOSE") {
                const tabsPerLoose = packagingPayload.tablets_per_loose || 1000;
                const looseVal = fin.profit_per_loose || ((fin.rate_per_unit || 0) * tabsPerLoose);
                safeSet("rate-primary-label", "Rate Per Loose Pack");
                safeSet("rate-primary-val", Number(looseVal).toFixed(2));
                safeSet("rate-primary-sub", `Per pack of ${tabsPerLoose} ${unitName.toLowerCase()}s (${packagingPayload.loose_type})`);
                safeSet("rate-product-desc", `Loose bulk quotation for ${tabsPerLoose} ${unitName.toLowerCase()}s per pack, batch of ${result.quantity.toLocaleString()} units.`);
            } else {
                // Default STRIP
                const stripSize = packagingPayload.strip_size || "1*10";
                safeSet("rate-primary-label", "Rate Per Strip");
                safeSet("rate-primary-val", (fin.profit_per_strip || 0).toFixed(2));
                safeSet("rate-primary-sub", `Per strip (${stripSize}) with outer carton & shipper`);
                safeSet("rate-product-desc", `Blister/Alu-Alu strip quotation for ${stripSize} pack, batch of ${result.quantity.toLocaleString()} units.`);
            }
        }

        // ═══════════════════════════════════════════════════════
        // Missing Ingredient Rates Notice Banner
        // ═══════════════════════════════════════════════════════
        const missingBox = document.getElementById("bmr-missing-rate-alert");
        const missingList = document.getElementById("bmr-missing-items-list");
        const missingMsg = document.getElementById("bmr-missing-rate-msg");
        const missingItems = result.missing_rate_items || fin.missing_rate_items || [];

        if (missingBox) {
            if (missingItems && missingItems.length > 0) {
                missingBox.classList.remove("hidden");
                if (missingList) missingList.innerText = missingItems.join(", ");
                if (missingMsg && result.missing_rate_notice) {
                    missingMsg.innerHTML = `Rate for <strong class="text-white underline underline-offset-2">${escapeHtml(missingItems.join(', '))}</strong> is currently pending review by Admin. <span class="font-bold text-amber-300">This ingredient rate will be added to this final cost once verified by Admin.</span>`;
                }
            } else {
                missingBox.classList.add("hidden");
            }
        }

        // ═══════════════════════════════════════════════════════
        // Costing & Commercial Rate Derivation Section (Unlocked)
        // ═══════════════════════════════════════════════════════
        const rd = result.rate_derivation || fin.rate_derivation || {};
        const capPerStrip = rd.capsules_or_tablets_per_strip || 10;
        const totalMfgCost = rd.net_manufacturing_cost || fin.total_cost_with_conversion || 0;
        const totalBatchVal = rd.total_batch_commercial_val || fin.total_batch_cost_with_profit || 0;
        const ratePerUnit = rd.final_rate_per_unit || fin.rate_per_unit || 0;
        const ratePerStrip = rd.final_rate_per_strip || fin.profit_per_strip || (ratePerUnit * capPerStrip);

        // Populate Formulas
        safeSet("deriv-unit-title", `Formula: Rate Per ${unitName}`);
        safeSet("deriv-strip-title", `Formula: Rate Per Strip (${rd.strip_size || '1*10'})`);
        safeSet("deriv-formula-unit", rd.formula_unit || `Rate Per ${unitName} = Total Commercial Value (₹${totalBatchVal.toLocaleString('en-IN', {minimumFractionDigits: 2})}) ÷ Batch Quantity (${result.quantity.toLocaleString()}) = ₹${ratePerUnit.toFixed(4)}`);
        safeSet("deriv-formula-strip", rd.formula_strip || `Rate Per Strip = Rate Per ${unitName} (₹${ratePerUnit.toFixed(4)}) × ${capPerStrip} Units/Strip = ₹${ratePerStrip.toFixed(2)}`);

        // Populate Derivation Table
        const derivTbody = document.getElementById("deriv-cost-table-body");
        if (derivTbody) {
            const dRows = [
                {
                    name: "A. Active Raw Materials Cost",
                    basis: "Sum of all active formulation ingredients",
                    total: fin.active_ingredients_cost || rd.active_ingredients_total || 0,
                    perUnit: rd.active_cost_per_unit || 0,
                    perStrip: rd.active_cost_per_strip || ((rd.active_cost_per_unit || 0) * capPerStrip),
                    highlight: false
                },
                {
                    name: "B. Inactive Excipients & Binders",
                    basis: "Granulation, disintegrants, lubricants & shell",
                    total: fin.other_ingredients_cost || rd.excipients_total || 0,
                    perUnit: rd.excipient_cost_per_unit || 0,
                    perStrip: rd.excipient_cost_per_strip || ((rd.excipient_cost_per_unit || 0) * capPerStrip),
                    highlight: false
                },
                {
                    name: "C. Conversion / Manufacturing Charge",
                    basis: "₹0.25 per unit standard GMP manufacturing charge",
                    total: fin.conversion_cost || rd.conversion_charges_total || 0,
                    perUnit: rd.conversion_cost_per_unit || 0.25,
                    perStrip: rd.conversion_cost_per_strip || (0.25 * capPerStrip),
                    highlight: false
                },
                {
                    name: "D. Packaging Materials (Primary + Outer + Shipper)",
                    basis: `${packagingPayload.primary_type || 'STRIP'} pack + carton & 5-ply shipper`,
                    total: fin.total_packaging_cost || rd.packaging_material_total || 0,
                    perUnit: rd.packaging_cost_per_unit || 0,
                    perStrip: rd.packaging_cost_per_strip || 0,
                    highlight: false
                },
                {
                    name: "E. Net Manufacturing Cost (A + B + C + D)",
                    basis: "Prime manufacturing cost before operating margin",
                    total: totalMfgCost,
                    perUnit: rd.net_mfg_cost_per_unit || (totalMfgCost / result.quantity),
                    perStrip: rd.net_mfg_cost_per_strip || ((totalMfgCost / result.quantity) * capPerStrip),
                    highlight: "bg-slate-800/70 font-bold text-slate-100"
                },
                {
                    name: "F. Walpar Operating Margin (20%)",
                    basis: "20% margin on net manufacturing cost",
                    total: fin.profit_margin_20 || rd.profit_margin_20_total || 0,
                    perUnit: rd.margin_per_unit || 0,
                    perStrip: rd.margin_per_strip || ((rd.margin_per_unit || 0) * capPerStrip),
                    highlight: false
                },
                {
                    name: "G. TOTAL COMMERCIAL BATCH VALUE (E + F)",
                    basis: `Final commercial quotation for ${result.quantity.toLocaleString()} units`,
                    total: totalBatchVal,
                    perUnit: ratePerUnit,
                    perStrip: ratePerStrip,
                    highlight: "bg-emerald-950/80 font-black text-emerald-300 border-t-2 border-emerald-500"
                }
            ];

            derivTbody.innerHTML = dRows.map(r => `
                <tr class="${r.highlight || 'hover:bg-slate-900/50'} text-xs">
                    <td class="py-2 px-3 font-semibold ${r.highlight ? '' : 'text-slate-200'}">${escapeHtml(r.name)}</td>
                    <td class="py-2 px-3 text-[11px] text-slate-400 font-sans">${escapeHtml(r.basis)}</td>
                    <td class="py-2 px-3 text-right font-mono ${r.highlight ? '' : 'text-slate-200'}">₹${Number(r.total).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                    <td class="py-2 px-3 text-right font-mono ${r.highlight ? '' : 'text-slate-300'}">₹${Number(r.perUnit).toFixed(4)}</td>
                    <td class="py-2 px-3 text-right font-mono ${r.highlight ? '' : 'text-slate-300'}">₹${Number(r.perStrip).toFixed(2)}</td>
                </tr>
            `).join("");
        }

        // Populate Active Itemized Cost Table
        const activeTbody = document.getElementById("deriv-active-cost-body");
        if (activeTbody) {
            const activeItems = (result.items || []).filter(i => i.group === "A. Active Ingredients");
            let hasUserEst = false;
            activeTbody.innerHTML = activeItems.map(it => {
                const cUnit = result.quantity > 0 ? (it.cost / result.quantity) : 0;
                let srcBadge = "";
                if (it.is_user_estimated) {
                    hasUserEst = true;
                    srcBadge = `<span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-bold">User Estimated (Audited)</span>`;
                } else if (it.is_rate_available) {
                    srcBadge = `<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] font-semibold">Official DB</span>`;
                } else {
                    srcBadge = `<span class="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/40 text-[10px] font-semibold">Pending Admin</span>`;
                }

                return `
                    <tr class="hover:bg-slate-900/50 text-xs">
                        <td class="py-2 px-3 text-center text-slate-500 font-sans">${it.sr_no}</td>
                        <td class="py-2 px-3 font-semibold text-slate-200">${escapeHtml(it.name)}</td>
                        <td class="py-2 px-3 text-right text-slate-300 font-mono">${it.qty_kg.toFixed(4)}</td>
                        <td class="py-2 px-3 text-right font-mono text-slate-200">
                            ${it.is_user_estimated ? `<span class="text-amber-300 font-bold">₹${Number(it.rate).toFixed(2)}</span>` : `<span class="text-emerald-400 font-sans text-[11px] font-semibold">Official DB</span>`}
                        </td>
                        <td class="py-2 px-3 text-right font-bold font-mono text-amber-300">₹${Number(it.cost).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        <td class="py-2 px-3 text-right font-mono text-slate-300">₹${cUnit.toFixed(4)}</td>
                        <td class="py-2 px-3 text-center">${srcBadge}</td>
                    </tr>
                `;
            }).join("");

            const badge = document.getElementById("deriv-user-rate-count-badge");
            if (badge) {
                badge.classList.toggle("hidden", !hasUserEst);
            }
        }

        // Clear hidden financial elements to prevent errors
        const safeSetText = (id, txt) => {
            const el = document.getElementById(id);
            if (el) el.innerText = txt;
        };
        safeSetText("cost-active", "");
        safeSetText("cost-other", "");
        safeSetText("cost-pkg", "");
        safeSetText("cost-conv", "");
        safeSetText("cost-profit-margin", "");
        safeSetText("cost-total-batch", "");
        safeSetText("unit-cost-val", "");

        if (window.lucide) lucide.createIcons();

    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="p-6 text-center text-rose-600 text-xs">Error calculating formulation: ${escapeHtml(err.message)}</td></tr>`;
    }
}

// Render Master Batch Card for Liquid (Matching uploaded image layout)
function renderLiquidMasterBatchCard(card) {
    if (!card) return;
    const safeSet = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
    };

    const h = card.header || {};
    safeSet("liq-card-product-name", h.product_name || "OSSOFY P suspension 200 ml");
    safeSet("liq-card-batch-size", `${Number(h.batch_size_ltr || 1000).toFixed(2)} Ltr`);
    safeSet("liq-card-bottles", Number(h.batch_quantity_bottles || 5000).toLocaleString());
    safeSet("liq-card-pack-size", h.pack_size || "200 ml");
    safeSet("liq-card-dosage", h.dosage_basis || "Each 10 ml");
    const sugarDesc = h.sugar_base_desc || (h.sugar_type === "Sorbitol" ? `Sugar Free / Sorbitol (${h.sugar_percent || '30%'})` : `With Sugar (${h.sugar_percent || '60%'} w/v)`);
    safeSet("liq-card-sugar-base", sugarDesc);
    safeSet("liq-spec-sugar", sugarDesc);
    safeSet("liq-card-yield", `${h.yield_percent || 100}%`);
    safeSet("liq-card-party", h.party_name || "Walpar Standard Quotation");

    // Table A (Bulk)
    const tblA = card.table_a_bulk || {};
    const items = tblA.items || [];
    const tbodyA = document.getElementById("liq-table-a-body");
    if (tbodyA) {
        let rowsHtml = "";
        let currentGroup = null;
        items.forEach(it => {
            if (it.group !== currentGroup) {
                currentGroup = it.group;
                rowsHtml += `
                    <tr class="bg-teal-50/70 font-sans font-bold border-y border-teal-200">
                        <td colspan="7" class="py-1 px-2.5 text-teal-900 tracking-wider text-[10px] uppercase">${escapeHtml(currentGroup)}</td>
                    </tr>
                `;
            }
            rowsHtml += `
                <tr class="hover:bg-slate-50">
                    <td class="py-1.5 px-2.5 text-center text-slate-400 font-sans">${it.sr_no}</td>
                    <td class="py-1.5 px-2.5 font-semibold text-slate-800 font-sans">${escapeHtml(it.item_description)}</td>
                    <td class="py-1.5 px-2.5 text-right font-sans text-slate-600">${escapeHtml(it.claim || '-')}</td>
                    <td class="py-1.5 px-2.5 text-right font-bold text-slate-900">${Number(it.std_batch_qty).toFixed(4)}</td>
                    <td class="py-1.5 px-2 text-center text-slate-500 font-sans">${escapeHtml(it.unit || 'KG')}</td>
                    <td class="py-1.5 px-2.5 text-right text-slate-700">${Number(it.unit_rate).toFixed(2)}</td>
                    <td class="py-1.5 px-2.5 text-right font-bold text-slate-900">₹${Number(it.total_cost).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                </tr>
            `;
        });
        tbodyA.innerHTML = rowsHtml;
    }

    safeSet("liq-total-bulk-qty", Number(tblA.bulk_total_qty_ltr || 1000).toFixed(2));
    safeSet("liq-total-bulk-cost", `₹${Number(tblA.bulk_total_cost || 0).toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`);
    safeSet("liq-per-bottle-bulk-cost", `₹${Number(tblA.per_bottle_bulk_cost || 0).toFixed(2)}`);

    // Table B (Semi Finish)
    const tblB = card.table_b_semi_finish || {};
    const specs = tblB.specs || {};
    const costs = tblB.costs_per_bottle || {};

    safeSet("liq-cost-bulk", `₹${Number(costs.per_bottle_bulk || 0).toFixed(2)}`);
    safeSet("liq-spec-bottle", specs.bottle || "WHITE BRUTE");
    safeSet("liq-cost-bottle", `₹${Number(costs.bottle || 0).toFixed(2)}`);
    safeSet("liq-spec-label", specs.label || "uv varnish roll");
    safeSet("liq-cost-label", `₹${Number(costs.label || 0).toFixed(2)}`);
    safeSet("liq-spec-ropp", specs.ropp || "GOLDEN CAP");
    safeSet("liq-cost-ropp", `₹${Number(costs.ropp || 0).toFixed(2)}`);
    safeSet("liq-spec-carton", specs.carton || "uv drip off");
    safeSet("liq-cost-carton", `₹${Number(costs.carton || 0).toFixed(2)}`);
    safeSet("liq-spec-cup", specs.measuring_cup || "10 ML CUP");
    safeSet("liq-cost-cup", `₹${Number(costs.measuring_cup || 0).toFixed(2)}`);
    safeSet("liq-spec-box", specs.box || "60 BOTT");
    safeSet("liq-cost-box", `₹${Number(costs.box || 0).toFixed(2)}`);

    const dropperRow = document.getElementById("liq-row-dropper");
    if (dropperRow) {
        const hasDropper = specs.dropper && specs.dropper !== "N/A";
        dropperRow.classList.toggle("hidden", !hasDropper);
        if (hasDropper) {
            safeSet("liq-spec-dropper", specs.dropper);
            safeSet("liq-cost-dropper", `₹${Number(costs.dropper || 0).toFixed(2)}`);
        }
    }

    const insertRow = document.getElementById("liq-row-insert");
    if (insertRow) {
        const hasInsert = specs.insert && specs.insert !== "N/A";
        insertRow.classList.toggle("hidden", !hasInsert);
        if (hasInsert) {
            safeSet("liq-spec-insert", specs.insert);
            safeSet("liq-cost-insert", `₹${Number(costs.insert || 0).toFixed(2)}`);
        }
    }

    safeSet("liq-cost-conv", `₹${Number(costs.conversion || 0).toFixed(2)}`);
    safeSet("liq-cost-stereo", `₹${Number(costs.stereo || 0).toFixed(2)}`);
    safeSet("liq-cost-margin", `₹${Number(costs.margin || 0).toFixed(2)}`);
    safeSet("liq-cost-testing", `₹${Number(costs.testing_charge || 0).toFixed(2)}`);
    safeSet("liq-total-mfg-cost", `₹${Number(costs.total_mfg_cost || 0).toFixed(2)}`);
    safeSet("liq-final-rate", `₹${Number(costs.final_rate || 0).toFixed(2)}`);
}

// Download Excel File directly (Protected by Master Password: Walpar@123)
async function exportBmrExcel() {
    if (!bmrState.lastPayload) {
        alert("Please calculate the Batch Master Card first.");
        return;
    }

    if (!bmrUnlocked || !bmrMasterPassword) {
        promptUnlockBmrModal();
        return;
    }

    try {
        const payloadWithPass = {
            ...bmrState.lastPayload,
            master_password: bmrMasterPassword
        };
        const res = await fetch("/api/batch-master/export-excel", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payloadWithPass)
        });
        if (!res.ok) {
            const errData = await res.json().catch(() => null);
            throw new Error((errData && errData.detail) || "Excel export failed");
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        const prod = (bmrState.lastPayload.product_type || "Product").toLowerCase();
        a.download = `Walpar_BMR_${prod}_${bmrState.lastPayload.quantity}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        alert("Failed to export Excel file: " + e.message);
    }
}

// ══════════════════════════════════════════════════════════════════
// LAPTOP & WEBCAM LIVE CAMERA CAPTURE (HTML5 getUserMedia API)
// ══════════════════════════════════════════════════════════════════
let cameraStream = null;
let currentFacingMode = "environment";
let availableVideoDevices = [];
let currentDeviceId = null;
let isCameraMirrored = false; // Default un-mirrored so labels & formulation text are correctly readable

async function startCameraCapture() {
    console.log("[Camera] startCameraCapture initiated");

    const modal = document.getElementById("camera-modal");
    if (modal) {
        modal.classList.remove("hidden");
    }

    const errorBanner = document.getElementById("camera-error-banner");
    if (errorBanner) errorBanner.classList.add("hidden");
    const badge = document.getElementById("camera-resolution-badge");
    if (badge) badge.innerText = "Connecting camera...";
    
    if (window.lucide) lucide.createIcons();

    // Check secure context (localhost, 127.0.0.1, or HTTPS)
    const isSecure = window.isSecureContext || location.hostname === "localhost" || location.hostname === "127.0.0.1";
    if (!isSecure && location.protocol !== "https:") {
        if (errorBanner) {
            errorBanner.classList.remove("hidden");
            const errorMsg = document.getElementById("camera-error-msg");
            if (errorMsg) {
                errorMsg.innerHTML = `
                    <strong>Insecure Connection (HTTP IP)</strong><br>
                    Browsers block webcam access on unencrypted IP addresses.<br><br>
                    <a href="http://localhost:8000" class="inline-block px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded text-xs font-bold mr-2 mb-2">Open http://localhost:8000</a>
                    <a href="https://rat-bone-pas-which.trycloudflare.com" class="inline-block px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-bold mb-2">Open HTTPS Cloudflare Link</a>
                `;
            }
        }
        return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (errorBanner) {
            errorBanner.classList.remove("hidden");
            const errorMsg = document.getElementById("camera-error-msg");
            if (errorMsg) {
                errorMsg.innerHTML = "Camera API (getUserMedia) is not supported or blocked in this browser.<br>Please open Chrome or Edge on <strong>http://localhost:8000</strong>.";
            }
        }
        return;
    }

    await enumerateCameras();
    await initCameraStream();
}

async function enumerateCameras() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
        const devices = await navigator.mediaDevices.enumerateDevices();
        availableVideoDevices = devices.filter(d => d.kind === "videoinput");
        
        const select = document.getElementById("camera-device-select");
        if (select) {
            select.innerHTML = "";
            if (availableVideoDevices.length === 0) {
                select.innerHTML = '<option value="">Default Laptop Camera</option>';
            } else {
                availableVideoDevices.forEach((dev, idx) => {
                    const opt = document.createElement("option");
                    opt.value = dev.deviceId;
                    opt.text = dev.label || `Camera ${idx + 1}`;
                    if (currentDeviceId && dev.deviceId === currentDeviceId) {
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
            }
        }
    } catch (e) {
        console.warn("Could not enumerate video devices:", e);
    }
}

async function initCameraStream(deviceId = null) {
    stopCameraStream();

    const videoEl = document.getElementById("camera-video");
    const errorBanner = document.getElementById("camera-error-banner");
    const errorMsg = document.getElementById("camera-error-msg");
    const badge = document.getElementById("camera-resolution-badge");
    if (badge) badge.innerText = "Connecting camera...";
    if (errorBanner) errorBanner.classList.add("hidden");

    // Tier 1: Ideal 1080p (NO strict min values to prevent OverconstrainedError)
    const tier1 = {
        video: deviceId 
            ? { deviceId: { exact: deviceId }, width: { ideal: 1920 }, height: { ideal: 1080 } }
            : { width: { ideal: 1920 }, height: { ideal: 1080 }, facingMode: { ideal: currentFacingMode } },
        audio: false
    };

    // Tier 2: Flexible resolution with device preference
    const tier2 = {
        video: deviceId 
            ? { deviceId: { exact: deviceId } }
            : { facingMode: { ideal: currentFacingMode } },
        audio: false
    };

    // Tier 3: Universal simple fallback (guaranteed to work on all webcams)
    const tier3 = { video: true, audio: false };

    let stream = null;
    let lastError = null;

    for (const c of [tier1, tier2, tier3]) {
        try {
            stream = await navigator.mediaDevices.getUserMedia(c);
            if (stream) {
                console.log("[Camera] Connected with constraint tier:", c);
                break;
            }
        } catch (e) {
            console.warn("[Camera] Constraint tier failed:", c, e);
            lastError = e;
        }
    }

    if (!stream) {
        console.error("[Camera] All camera getUserMedia attempts failed:", lastError);
        if (errorBanner) {
            errorBanner.classList.remove("hidden");
            if (lastError && (lastError.name === "NotAllowedError" || lastError.name === "PermissionDeniedError")) {
                errorMsg.innerHTML = "Camera permission was denied.<br>Please click the <strong>camera / lock icon</strong> in your browser address bar and select <strong>Allow</strong>, then click Try Again.";
            } else if (lastError && (lastError.name === "NotFoundError" || lastError.name === "DevicesNotFoundError")) {
                errorMsg.innerHTML = "No camera hardware detected on your laptop.<br>Please ensure your laptop webcam or USB camera is connected.";
            } else if (lastError && (lastError.name === "NotReadableError" || lastError.name === "TrackStartError")) {
                errorMsg.innerHTML = "Your webcam is currently locked by another application (Zoom, Teams, Skype, or Windows Camera).<br>Please close those apps and click Try Again.";
            } else {
                errorMsg.innerText = `Could not access camera: ${lastError ? lastError.message || lastError.name : 'Unknown error'}`;
            }
        }
        if (window.lucide) lucide.createIcons();
        return;
    }

    cameraStream = stream;
    if (videoEl) {
        videoEl.srcObject = cameraStream;
        videoEl.muted = true;

        try {
            await videoEl.play();
        } catch (playErr) {
            console.warn("[Camera] Autoplay play() rejected, waiting for metadata:", playErr);
        }

        videoEl.onloadedmetadata = () => {
            videoEl.play().catch(e => console.warn(e));
            const w = videoEl.videoWidth || 1280;
            const h = videoEl.videoHeight || 720;
            const label = w >= 1920 ? "Full HD (1080p)" : (w >= 1280 ? "HD (720p)" : `${w}x${h}`);
            if (badge) badge.innerText = `● ${label} Ready`;
        };
    }
    applyCameraMirror();
    await enumerateCameras();
}

function stopCameraStream() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => {
            try { track.stop(); } catch (e) {}
        });
        cameraStream = null;
    }
    const videoEl = document.getElementById("camera-video");
    if (videoEl) {
        videoEl.srcObject = null;
    }
}

function closeCameraModal() {
    stopCameraStream();
    const modal = document.getElementById("camera-modal");
    if (modal) modal.classList.add("hidden");
}

function toggleCameraMirror() {
    isCameraMirrored = !isCameraMirrored;
    applyCameraMirror();
}

function applyCameraMirror() {
    const videoEl = document.getElementById("camera-video");
    const mirrorBtnText = document.getElementById("camera-mirror-text");
    if (!videoEl) return;

    if (isCameraMirrored) {
        videoEl.style.transform = "scaleX(-1)"; // Mirrored (selfie style)
        if (mirrorBtnText) mirrorBtnText.innerText = "Mirrored View";
    } else {
        videoEl.style.transform = "scaleX(1)"; // Un-mirrored (normal document reading)
        if (mirrorBtnText) mirrorBtnText.innerText = "Normal View";
    }
}

async function switchCameraDevice(deviceId) {
    if (!deviceId) return;
    currentDeviceId = deviceId;
    await initCameraStream(deviceId);
}

async function cycleCamera() {
    if (availableVideoDevices.length > 1) {
        const curIdx = availableVideoDevices.findIndex(d => d.deviceId === currentDeviceId);
        const nextIdx = (curIdx + 1) % availableVideoDevices.length;
        currentDeviceId = availableVideoDevices[nextIdx].deviceId;
        const select = document.getElementById("camera-device-select");
        if (select) select.value = currentDeviceId;
        await initCameraStream(currentDeviceId);
    } else {
        currentFacingMode = (currentFacingMode === "user") ? "environment" : "user";
        currentDeviceId = null;
        await initCameraStream();
    }
}

function captureCameraFrame() {
    const videoEl = document.getElementById("camera-video");
    if (!videoEl || !cameraStream) {
        alert("Camera stream is not active. Please wait or reload.");
        return;
    }

    const vw = videoEl.videoWidth;
    const vh = videoEl.videoHeight;
    if (!vw || !vh) {
        alert("Camera is warming up, please try in a moment.");
        return;
    }

    // Visual Flash Animation
    const flashEl = document.getElementById("camera-flash");
    if (flashEl) {
        flashEl.classList.remove("hidden");
        flashEl.style.opacity = "0.9";
        setTimeout(() => {
            flashEl.style.opacity = "0";
            setTimeout(() => flashEl.classList.add("hidden"), 150);
        }, 80);
    }

    // Draw high-resolution frame onto canvas
    const canvas = document.createElement("canvas");
    canvas.width = vw;
    canvas.height = vh;
    const ctx = canvas.getContext("2d");

    // If mirrored in preview, mirror the capture too; otherwise keep normal orientation
    if (isCameraMirrored) {
        ctx.translate(vw, 0);
        ctx.scale(-1, 1);
    }
    ctx.drawImage(videoEl, 0, 0, vw, vh);

    canvas.toBlob((blob) => {
        if (!blob) {
            alert("Could not capture frame. Please try again.");
            return;
        }

        // Close camera modal
        closeCameraModal();

        // Convert blob to File object
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const capturedFile = new File([blob], `walpar_camera_${timestamp}.jpg`, { type: "image/jpeg" });

        // Pass directly to the Document Scanner / Crop Modal
        if (typeof openCropModal === "function") {
            openCropModal(capturedFile);
        } else {
            handleFileSelect(capturedFile);
        }
    }, "image/jpeg", 0.95);
}

// ══════════════════════════════════════════════════════════════════
// ELEMENTAL SALT & RDA CALCULATOR CONTROLLER
// ══════════════════════════════════════════════════════════════════
let saltRdaCatalog = null;

async function loadSaltRdaCatalog() {
    if (saltRdaCatalog) return saltRdaCatalog;
    try {
        const res = await fetch("/api/salt-rda/catalog");
        const data = await res.json();
        if (data.success) {
            saltRdaCatalog = data;
            populateSaltRdaDropdowns();
        }
    } catch (e) {
        console.error("Failed to load Salt & RDA catalog:", e);
    }
    return saltRdaCatalog;
}

function populateSaltRdaDropdowns() {
    if (!saltRdaCatalog) return;
    const minSel = document.getElementById("rda-mineral-select");
    if (minSel && minSel.options.length <= 1) {
        (saltRdaCatalog.minerals || []).forEach(m => {
            const opt = document.createElement("option");
            opt.value = m;
            opt.textContent = m;
            minSel.appendChild(opt);
        });
    }

    const vitSel = document.getElementById("rda-vitamin-select");
    if (vitSel && vitSel.options.length <= 1) {
        (saltRdaCatalog.vitamins || []).forEach(v => {
            const opt = document.createElement("option");
            opt.value = v;
            opt.textContent = v;
            vitSel.appendChild(opt);
        });
    }
}

function getActiveFormulaIngredientsList() {
    if (appState && Array.isArray(appState.ingredients) && appState.ingredients.length > 0) {
        return appState.ingredients;
    }
    const rows = document.querySelectorAll("#ingredients-table-body tr");
    const list = [];
    rows.forEach(r => {
        const nameEl = r.querySelector(".ing-name-input") || r.querySelector("input[name='name']");
        const doseEl = r.querySelector(".ing-amount-input") || r.querySelector("input[name='amount']");
        const unitEl = r.querySelector(".ing-unit-select") || r.querySelector("select[name='unit']");
        if (nameEl && nameEl.value && nameEl.value.trim()) {
            list.push({
                name: nameEl.value.trim(),
                amount: parseFloat(doseEl ? doseEl.value : 0) || 0,
                unit: (unitEl ? unitEl.value : 'mg') || 'mg'
            });
        }
    });
    return list;
}

function populateActiveIngredientsDropdown() {
    const sel = document.getElementById("rda-active-ingredients-select");
    if (!sel) return;
    const ingList = getActiveFormulaIngredientsList();
    
    sel.innerHTML = `<option value="">-- Auto-Fetch from Active Ingredients (${ingList.length}) --</option>`;
    if (ingList.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.disabled = true;
        opt.textContent = "No formulation loaded yet - OCR or enter ingredients";
        sel.appendChild(opt);
        return;
    }

    ingList.forEach((ing, idx) => {
        const opt = document.createElement("option");
        opt.value = idx;
        const isElem = ing.is_elemental_specification ? " [Elemental Spec]" : (ing.salt_rda_data ? " [Salt Form]" : "");
        opt.textContent = `${ing.name || 'Unnamed'} - ${ing.amount || 0} ${ing.unit || 'mg'}${isElem}`;
        sel.appendChild(opt);
    });
}

async function onSelectActiveFormulaIngredient(idxVal) {
    if (idxVal === "" || idxVal === undefined || idxVal === null) return;
    const ingList = getActiveFormulaIngredientsList();
    const idx = parseInt(idxVal);
    if (isNaN(idx) || !ingList[idx]) return;

    const ing = ingList[idx];
    const ingName = ing.name || "";
    let dose = parseFloat(ing.amount) || 0;
    const unit = (ing.unit || "mg").toLowerCase();
    
    let doseMg = dose;
    if (unit === 'g') doseMg = dose * 1000;
    else if (unit === 'mcg' || unit === 'ug') doseMg = dose / 1000;

    await openSaltRdaForIngredient(ingName, doseMg, "mg", !!ing.is_elemental_specification);
}

function onRdaCalcModeChange() {
    const isTargetElem = document.getElementById("rda-mode-elemental-target")?.checked;
    const doseLabel = document.getElementById("rda-dose-label");
    const hint = document.getElementById("rda-calc-mode-hint");
    if (doseLabel) {
        doseLabel.innerText = isTargetElem ? "Target Elemental Dose (mg):" : "Salt Supplement Dose (mg):";
    }
    if (hint) {
        hint.innerText = isTargetElem 
            ? "Calculates required mg of each salt form to supply this target elemental dose" 
            : "Entering salt dose yields elemental mineral content";
    }
    const minSel = document.getElementById("rda-mineral-select");
    if (minSel && minSel.value) {
        onRdaMineralChange();
    }
}

async function onRdaMineralChange() {
    const minSel = document.getElementById("rda-mineral-select");
    const saltSel = document.getElementById("rda-salt-form-select");
    const doseInp = document.getElementById("rda-mineral-dose");
    if (!minSel || !saltSel || !saltRdaCatalog) return;

    const mineral = minSel.value;
    saltSel.innerHTML = `<option value="">-- Select Salt Form --</option>`;
    if (!mineral) {
        const optBox = document.getElementById("rda-salt-options-box");
        if (optBox) optBox.classList.add("hidden");
        return;
    }

    const salts = (saltRdaCatalog.salts || []).filter(s => s.element.toLowerCase() === mineral.toLowerCase());
    salts.forEach(s => {
        const opt = document.createElement("option");
        opt.value = s.salt_name;
        opt.textContent = `${s.salt_name} (${s.elemental_percent}% ${s.element})`;
        saltSel.appendChild(opt);
    });

    if (salts.length > 0) {
        saltSel.selectedIndex = 1;
    }

    const dose = parseFloat(doseInp?.value) || 10;
    const isTargetElem = document.getElementById("rda-mode-elemental-target")?.checked || false;
    await fetchAndRenderElementOptions(mineral, dose, isTargetElem);
}

async function onRdaSaltFormChange() {
    calculateModalSaltRda();
}

async function fetchAndRenderElementOptions(elementName, dose, isTargetElemental) {
    const optBox = document.getElementById("rda-salt-options-box");
    const tbody = document.getElementById("rda-salt-options-tbody");
    const titleEl = document.getElementById("rda-options-element-title");
    const countBadge = document.getElementById("rda-options-count-badge");
    if (!optBox || !tbody) return;

    try {
        const res = await fetch("/api/salt-rda/element-options", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                element: elementName,
                dose: parseFloat(dose) || 10,
                is_target_elemental: !!isTargetElemental
            })
        });
        const data = await res.json();
        if (!data.success || !Array.isArray(data.options) || data.options.length === 0) {
            optBox.classList.add("hidden");
            return;
        }

        if (titleEl) titleEl.innerText = data.element || elementName;
        if (countBadge) countBadge.innerText = `${data.total_options} Salt Options Available`;

        const currentSalt = document.getElementById("rda-salt-form-select")?.value || "";

        tbody.innerHTML = data.options.map(opt => {
            const isSelected = (opt.salt_name.toLowerCase() === currentSalt.toLowerCase());
            const rowClass = isSelected ? "bg-teal-50/80 font-bold border-teal-200" : "hover:bg-slate-50";
            const secNutr = opt.secondary_element ? `${opt.secondary_element} (${opt.secondary_percent}%)` : '<span class="text-slate-400">-</span>';
            const adultRda = opt.adult_rda_pct > 0 ? `${opt.adult_rda_pct}%` : '<span class="text-slate-400">-</span>';
            
            return `
                <tr class="${rowClass} transition">
                    <td class="py-2.5 px-3">
                        <div class="font-bold text-slate-800">${escapeHtml(opt.salt_name)}</div>
                        <div class="text-[10px] text-slate-500 font-sans">${escapeHtml(opt.chemical_formula || '')}</div>
                    </td>
                    <td class="py-2.5 px-2 text-center font-bold text-teal-800">${opt.elemental_percent}%</td>
                    <td class="py-2.5 px-3 text-right font-black ${isTargetElemental ? 'text-amber-700 bg-amber-50/50' : 'text-slate-700'}">
                        ${opt.required_salt_mg} mg
                    </td>
                    <td class="py-2.5 px-3 text-right font-black ${!isTargetElemental ? 'text-teal-700 bg-teal-50/50' : 'text-slate-700'}">
                        ${opt.elemental_yield_mg} mg
                    </td>
                    <td class="py-2.5 px-2.5 text-slate-600 font-sans text-[10px]">${secNutr}</td>
                    <td class="py-2.5 px-2 text-right font-bold text-slate-700">${adultRda}</td>
                    <td class="py-2.5 px-2.5 text-center">
                        <button type="button" onclick="selectSaltOption('${escapeHtml(opt.salt_name)}', ${opt.required_salt_mg})" 
                                class="px-2.5 py-1 ${isSelected ? 'bg-teal-700 text-white' : 'bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-300'} rounded font-semibold text-[10px] shadow-2xs transition">
                            ${isSelected ? 'Selected' : 'Select'}
                        </button>
                    </td>
                </tr>
            `;
        }).join("");

        optBox.classList.remove("hidden");
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        console.error("Error fetching salt options:", e);
    }
}

function selectSaltOption(saltName, requiredSaltMg) {
    const saltSel = document.getElementById("rda-salt-form-select");
    if (saltSel) {
        saltSel.value = saltName;
    }
    calculateModalSaltRda();
}

async function calculateModalSaltRda() {
    const saltSel = document.getElementById("rda-salt-form-select");
    const doseInp = document.getElementById("rda-mineral-dose");
    const minSel = document.getElementById("rda-mineral-select");
    const isTargetElem = document.getElementById("rda-mode-elemental-target")?.checked || false;
    if (!saltSel || !doseInp) return;

    const saltName = saltSel.value;
    const doseMg = parseFloat(doseInp.value) || 10;
    if (!saltName) {
        alert("Please select a salt form.");
        return;
    }

    try {
        const res = await fetch("/api/salt-rda/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                salt_name: saltName, 
                dose_mg: doseMg,
                is_target_elemental: isTargetElem
            })
        });
        const data = await res.json();
        if (!data.success) {
            alert(data.error || "Calculation failed");
            return;
        }

        const box = document.getElementById("rda-mineral-results-box");
        if (box) box.classList.remove("hidden");

        const amtTitle = document.getElementById("rda-elemental-title");
        const amtEl = document.getElementById("rda-elemental-amount");
        if (amtTitle) {
            amtTitle.innerText = isTargetElem 
                ? `Required Salt Dose for ${data.element_name}:`
                : `Elemental ${data.element_name} Yield:`;
        }
        if (amtEl) {
            amtEl.innerText = isTargetElem
                ? `${data.dose_mg} mg ${data.salt_name} (${data.elemental_percent}% yield)`
                : `${data.elemental_mg} mg ${data.element_name} (${data.elemental_percent}%)`;
        }

        const secBox = document.getElementById("rda-secondary-amount-box");
        const secAmt = document.getElementById("rda-secondary-amount");
        const secTitle = document.getElementById("rda-secondary-title");
        if (data.secondary_element && data.secondary_mg > 0) {
            if (secBox) secBox.classList.remove("hidden");
            if (secTitle) secTitle.innerText = `${data.secondary_element} Yield:`;
            if (secAmt) secAmt.innerText = `${data.secondary_mg} mg (${data.secondary_percent}%)`;
        } else if (secBox) {
            secBox.classList.add("hidden");
        }

        const tbody = document.getElementById("rda-demographic-tbody");
        if (tbody) {
            tbody.innerHTML = (data.demographic_rda || []).map(d => `
                <tr class="hover:bg-slate-50 text-xs">
                    <td class="py-2 px-3 font-semibold text-slate-800">${escapeHtml(d.group)}</td>
                    <td class="py-2 px-3 text-slate-600">${d.rda_mg} ${d.unit || 'mg'}</td>
                    <td class="py-2 px-3 text-right font-black ${d.pct >= 100 ? 'text-emerald-700' : 'text-teal-700'}">${d.pct}%</td>
                </tr>
            `).join("");
        }

        if (minSel && minSel.value) {
            fetchAndRenderElementOptions(minSel.value, doseMg, isTargetElem);
        }

        if (window.lucide) lucide.createIcons();
    } catch (e) {
        alert("Error calculating elemental yield: " + e.message);
    }
}

function onRdaVitaminChange() {
    const vitSel = document.getElementById("rda-vitamin-select");
    const formSel = document.getElementById("rda-vitamin-form-select");
    if (!vitSel || !formSel || !saltRdaCatalog) return;

    const vit = vitSel.value;
    formSel.innerHTML = `<option value="">-- Select Chemical Form --</option>`;
    if (!vit) return;

    const forms = (saltRdaCatalog.vitamins_detail || {})[vit] || [vit];
    forms.forEach(f => {
        const formName = typeof f === 'object' ? f.name : f;
        const opt = document.createElement("option");
        opt.value = formName;
        opt.textContent = formName;
        formSel.appendChild(opt);
    });

    if (formSel.options.length > 1) {
        formSel.selectedIndex = 1;
    }
}

async function calculateModalVitaminRda() {
    const formSel = document.getElementById("rda-vitamin-form-select");
    const doseInp = document.getElementById("rda-vitamin-dose");
    const unitSel = document.getElementById("rda-vitamin-unit");
    if (!formSel || !doseInp) return;

    const formName = formSel.value;
    const dose = parseFloat(doseInp.value) || 10;
    const unit = unitSel ? unitSel.value : "mg";
    if (!formName) {
        alert("Please select a vitamin chemical form.");
        return;
    }

    try {
        const res = await fetch("/api/salt-rda/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ salt_name: formName, dose_mg: dose, unit: unit })
        });
        const data = await res.json();
        if (!data.success) {
            alert(data.error || "Calculation failed");
            return;
        }

        const box = document.getElementById("rda-vitamin-results-box");
        if (box) box.classList.remove("hidden");

        const amtEl = document.getElementById("rda-vitamin-elemental-amount");
        if (amtEl) amtEl.innerText = `${data.elemental_mg} ${data.unit || 'mg'} Active ${data.element_name} (${data.elemental_percent}%)`;

        const tbody = document.getElementById("rda-vitamin-demographic-tbody");
        if (tbody) {
            tbody.innerHTML = (data.demographic_rda || []).map(d => `
                <tr class="hover:bg-slate-50 text-xs">
                    <td class="py-2 px-3 font-semibold text-slate-800">${escapeHtml(d.group)}</td>
                    <td class="py-2 px-3 text-slate-600">${d.rda_mg} ${d.unit || 'mg'}</td>
                    <td class="py-2 px-3 text-right font-black ${d.pct >= 100 ? 'text-emerald-700' : 'text-teal-700'}">${d.pct}%</td>
                </tr>
            `).join("");
        }
        if (window.lucide) lucide.createIcons();
    } catch (e) {
        alert("Error calculating vitamin RDA: " + e.message);
    }
}

function openSaltRdaModal(prefillSaltName, doseMg) {
    const modal = document.getElementById("salt-rda-modal");
    if (modal) modal.classList.remove("hidden");
    loadSaltRdaCatalog().then(() => {
        populateActiveIngredientsDropdown();
        if (prefillSaltName) {
            openSaltRdaForIngredient(prefillSaltName, doseMg);
        }
    });
    if (window.lucide) lucide.createIcons();
}

function closeSaltRdaModal() {
    const modal = document.getElementById("salt-rda-modal");
    if (modal) modal.classList.add("hidden");
}

function switchSaltRdaTab(tab) {
    const minTab = document.getElementById("rda-tab-minerals");
    const vitTab = document.getElementById("rda-tab-vitamins");
    const minPan = document.getElementById("rda-panel-minerals");
    const vitPan = document.getElementById("rda-panel-vitamins");

    if (tab === "minerals") {
        if (minTab) { minTab.className = "px-4 py-2 rounded-lg bg-teal-600 text-white shadow-sm transition flex items-center space-x-1.5"; }
        if (vitTab) { vitTab.className = "px-4 py-2 rounded-lg bg-white text-slate-600 hover:text-slate-900 border border-slate-200 transition flex items-center space-x-1.5"; }
        if (minPan) minPan.classList.remove("hidden");
        if (vitPan) vitPan.classList.add("hidden");
    } else {
        if (vitTab) { vitTab.className = "px-4 py-2 rounded-lg bg-teal-600 text-white shadow-sm transition flex items-center space-x-1.5"; }
        if (minTab) { minTab.className = "px-4 py-2 rounded-lg bg-white text-slate-600 hover:text-slate-900 border border-slate-200 transition flex items-center space-x-1.5"; }
        if (vitPan) vitPan.classList.remove("hidden");
        if (minPan) minPan.classList.add("hidden");
    }
    if (window.lucide) lucide.createIcons();
}

async function openSaltRdaForIngredient(saltName, dose, unit, isElementalTarget) {
    const modal = document.getElementById("salt-rda-modal");
    if (modal) modal.classList.remove("hidden");
    await loadSaltRdaCatalog();
    populateActiveIngredientsDropdown();

    let doseMg = parseFloat(dose) || 100;
    if (unit && unit.toLowerCase() === 'g') doseMg *= 1000;
    else if (unit && (unit.toLowerCase() === 'mcg' || unit.toLowerCase() === 'ug')) doseMg /= 1000;

    // Check if saltName is or contains a vitamin
    const vits = saltRdaCatalog?.vitamins || [];
    const matchedVit = vits.find(v => (saltName || "").toLowerCase().includes(v.toLowerCase()));
    
    if (matchedVit) {
        switchSaltRdaTab("vitamins");
        const vitSel = document.getElementById("rda-vitamin-select");
        if (vitSel) {
            vitSel.value = matchedVit;
            onRdaVitaminChange();
            const formSel = document.getElementById("rda-vitamin-form-select");
            if (formSel) {
                for (let i = 0; i < formSel.options.length; i++) {
                    if (formSel.options[i].value.toLowerCase().includes((saltName || "").toLowerCase()) ||
                        (saltName || "").toLowerCase().includes(formSel.options[i].value.toLowerCase())) {
                        formSel.selectedIndex = i;
                        break;
                    }
                }
            }
            const vitDoseInp = document.getElementById("rda-vitamin-dose");
            if (vitDoseInp) vitDoseInp.value = doseMg;
            calculateModalVitaminRda();
        }
        if (window.lucide) lucide.createIcons();
        return;
    }

    // Mineral & Salt form handling
    switchSaltRdaTab("minerals");

    const modeRadioSalt = document.getElementById("rda-mode-salt-dose");
    const modeRadioElem = document.getElementById("rda-mode-elemental-target");
    if (isElementalTarget) {
        if (modeRadioElem) modeRadioElem.checked = true;
    } else {
        if (modeRadioSalt) modeRadioSalt.checked = true;
    }
    onRdaCalcModeChange();

    const minSel = document.getElementById("rda-mineral-select");
    const saltSel = document.getElementById("rda-salt-form-select");
    const doseInp = document.getElementById("rda-mineral-dose");
    if (doseInp) doseInp.value = doseMg;

    const matchedSalt = (saltRdaCatalog && saltRdaCatalog.salts)
        ? saltRdaCatalog.salts.find(s => s.salt_name.toLowerCase() === (saltName || "").toLowerCase() ||
                                         (saltName || "").toLowerCase().includes(s.salt_name.toLowerCase()))
        : null;

    if (matchedSalt) {
        if (minSel) {
            minSel.value = matchedSalt.element;
            await onRdaMineralChange();
            if (saltSel) saltSel.value = matchedSalt.salt_name;
            await calculateModalSaltRda();
        }
    } else {
        const minerals = saltRdaCatalog?.minerals || [];
        const matchedMin = minerals.find(m => (saltName || "").toLowerCase().includes(m.toLowerCase()));
        if (matchedMin && minSel) {
            minSel.value = matchedMin;
            await onRdaMineralChange();
            await calculateModalSaltRda();
        } else {
            await calculateModalSaltRda();
        }
    }
    if (window.lucide) lucide.createIcons();
}

// ══════════════════════════════════════════════════════════════════
// LIVE IST CLOCK (Indian Standard Time, UTC+5:30)
// ══════════════════════════════════════════════════════════════════
function initIstClock() {
    function updateClock() {
        const el = document.getElementById("header-ist-clock");
        if (!el) return;
        const now = new Date();
        const istStr = new Intl.DateTimeFormat("en-IN", {
            timeZone: "Asia/Kolkata",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false
        }).format(now);
        el.innerText = `${istStr} IST`;
    }
    setInterval(updateClock, 1000);
    updateClock();
}

// ══════════════════════════════════════════════════════════════════
// MY QUOTATIONS & ADMIN REVISED RATES MODAL
// ══════════════════════════════════════════════════════════════════
function openMyQuotationsModal() {
    const modal = document.getElementById("my-quotations-modal");
    if (modal) modal.classList.remove("hidden");
    loadMyQuotations();
    if (window.lucide) lucide.createIcons();
}

function closeMyQuotationsModal() {
    const modal = document.getElementById("my-quotations-modal");
    if (modal) modal.classList.add("hidden");
}

async function loadMyQuotations() {
    const listEl = document.getElementById("my-quotations-list");
    const countEl = document.getElementById("my-quotes-count");
    if (!listEl) return;

    listEl.innerHTML = `
        <div class="py-8 text-center text-slate-500 text-xs flex items-center justify-center space-x-2">
            <div class="w-4 h-4 border-2 border-teal-400 border-t-transparent rounded-full animate-spin"></div>
            <span>Fetching your quotation history...</span>
        </div>
    `;

    try {
        const res = await fetch("/api/user/quotations");
        const data = await res.json();
        if (!data.success) throw new Error(data.error || "Failed to load quotations");

        const quotes = data.quotations || [];
        if (countEl) countEl.innerText = `${quotes.length} Quotations Recorded`;

        if (quotes.length === 0) {
            listEl.innerHTML = `
                <div class="py-12 text-center text-slate-400 text-xs">
                    <p class="font-bold text-slate-300">No quotations calculated yet</p>
                    <p class="text-[11px] text-slate-500 mt-1">Open the Batch Master Wizard to calculate commercial rates for tablets, capsules, or liquids.</p>
                </div>
            `;
            return;
        }

        let html = "";
        quotes.forEach(q => {
            const isRevised = q.status === "RATE_UPDATED_BY_ADMIN" || q.rate_status === "RESOLVED_BY_ADMIN";
            const isPending = q.status === "PENDING_ADMIN_RATE" || q.rate_status === "PENDING_ADMIN_RATE";

            let borderClass = "border-slate-800 bg-slate-950/70";
            let statusBadge = `<span class="px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30 text-[10px] font-bold">Quotation Ready</span>`;

            if (isRevised) {
                borderClass = "border-emerald-500/60 bg-emerald-950/20 shadow-md shadow-emerald-950/30";
                statusBadge = `<span class="px-2 py-0.5 rounded bg-emerald-500 text-slate-950 font-black text-[10px] animate-pulse">REVISED BY ADMIN</span>`;
            } else if (isPending) {
                borderClass = "border-amber-500/60 bg-amber-950/20 shadow-md shadow-amber-950/30";
                statusBadge = `<span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-bold">Rate Pending Admin Verification</span>`;
            }

            html += `
                <div class="p-4 rounded-xl border ${borderClass} space-y-3 transition">
                    <div class="flex items-start justify-between gap-2 border-b border-slate-800 pb-2.5">
                        <div>
                            <div class="flex items-center space-x-2">
                                <span class="text-xs font-bold text-white">${escapeHtml(q.product_type)}</span>
                                <span class="text-[11px] font-mono text-teal-300">${(q.batch_qty || 100000).toLocaleString()} units</span>
                                <span class="text-[11px] text-slate-400">(${escapeHtml(q.pack_type || 'Standard')})</span>
                            </div>
                            <div class="text-[10px] text-slate-400 font-mono mt-0.5">${escapeHtml(q.timestamp_ist)}</div>
                        </div>
                        <div>${statusBadge}</div>
                    </div>

                    <!-- Commercial Rates -->
                    <div class="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs font-mono">
                        <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                            <span class="text-[10px] text-slate-400 block font-sans">Rate Given / Pack</span>
                            ${isRevised && q.updated_rate_per_pack ? `
                                <div class="text-emerald-400 font-black text-sm">₹${q.updated_rate_per_pack.toFixed(2)}</div>
                                <div class="text-[9px] text-slate-500 line-through">₹${(q.rate_per_pack || 0).toFixed(2)}</div>
                            ` : `
                                <div class="text-emerald-300 font-bold text-sm">₹${(q.rate_per_pack || 0).toFixed(2)}</div>
                            `}
                        </div>
                        <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                            <span class="text-[10px] text-slate-400 block font-sans">Rate / Unit</span>
                            ${isRevised && q.updated_rate_per_unit ? `
                                <div class="text-teal-300 font-bold text-sm">₹${q.updated_rate_per_unit.toFixed(2)}</div>
                                <div class="text-[9px] text-slate-500 line-through">₹${(q.rate_per_unit || 0).toFixed(2)}</div>
                            ` : `
                                <div class="text-teal-300 font-bold text-sm">₹${(q.rate_per_unit || 0).toFixed(2)}</div>
                            `}
                        </div>
                        <div class="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 col-span-2 sm:col-span-1">
                            <span class="text-[10px] text-slate-400 block font-sans">Total Batch Commercial Value</span>
                            ${isRevised && q.updated_total_val ? `
                                <div class="text-amber-300 font-black text-sm">₹${q.updated_total_val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                                <div class="text-[9px] text-slate-500 line-through">₹${(q.total_batch_val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                            ` : `
                                <div class="text-amber-300 font-bold text-sm">₹${(q.total_batch_val || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                            `}
                        </div>
                    </div>

                    ${isRevised && q.admin_notes ? `
                        <div class="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px] font-sans flex items-start space-x-2">
                            <i data-lucide="check-circle" class="w-4 h-4 flex-shrink-0 text-emerald-400 mt-0.5"></i>
                            <div>
                                <span class="font-bold block">Rate Update from Admin:</span>
                                <span>${escapeHtml(q.admin_notes)}</span>
                            </div>
                        </div>
                    ` : ''}

                    ${isPending && q.missing_items && q.missing_items.length > 0 ? `
                        <div class="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200 text-[11px] font-sans flex items-start space-x-2">
                            <i data-lucide="alert-triangle" class="w-4 h-4 flex-shrink-0 text-amber-400 mt-0.5"></i>
                            <div>
                                <span class="font-bold block">Rate Pending Verification by Admin:</span>
                                <span>Rate for <strong>${escapeHtml(q.missing_items.join(', '))}</strong> is currently under review. This ingredient rate will be added to this final cost once verified by Admin.</span>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        });

        listEl.innerHTML = html;
        if (window.lucide) lucide.createIcons();

    } catch (err) {
        listEl.innerHTML = `<div class="p-4 text-center text-rose-400 text-xs">Error loading quotations: ${escapeHtml(err.message)}</div>`;
    }
}

// Check for admin revisions on page load
async function checkUserRevisedQuotations() {
    try {
        const res = await fetch("/api/user/quotations");
        const data = await res.json();
        if (data.success && data.has_updated_quotes) {
            const dot = document.getElementById("user-revised-dot");
            if (dot) dot.classList.remove("hidden");
        }
    } catch (e) {}
}

// Auto-initialize IST clock and check revised quotes
document.addEventListener("DOMContentLoaded", () => {
    initIstClock();
    loadSaltRdaCatalog();
    checkUserRevisedQuotations();
});
initIstClock();
