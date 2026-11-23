const el = (id) => document.getElementById(id);

let latestState = null;
let dragging = { speaker1: false, speaker2: false, pan: false, tilt: false };
let lastLogSignature = "";
let lastSttSignature = "";

// --- Build 4x4 Mic Grid & 16 VU Bars once ---
function initAudioWidgets() {
  const grid = el("mic-grid");
  const vu = el("vu-bars");
  for (let i = 0; i < 16; i++) {
    const ch = i + 1;
    const cell = document.createElement("div");
    cell.className = "mic-cell";
    cell.id = `mic-cell-${i}`;
    cell.innerHTML = `<div class="ch-num">CH ${String(ch).padStart(2, "0")}</div><div class="ch-val" id="mic-val-${i}">--</div>`;
    grid.appendChild(cell);

    const col = document.createElement("div");
    col.className = "vu-col";
    col.innerHTML = `<div class="vu-fill" id="vu-fill-${i}" style="height: 8%;"></div>`;
    vu.appendChild(col);
  }
}

// --- API helper ---
async function postJSON(url, body = {}) {
  try {
    await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (err) {
    console.error("API error:", err);
  }
}

// --- Bind UI controls ---
function bindControls() {
  const sliderMap = [
    ["slider-s1", "speaker1"],
    ["slider-s2", "speaker2"],
    ["slider-pan", "pan"],
    ["slider-tilt", "tilt"],
  ];

  sliderMap.forEach(([id, axis]) => {
    const input = el(id);
    input.addEventListener("pointerdown", () => (dragging[axis] = true));
    input.addEventListener("pointerup", () => (dragging[axis] = false));
    input.addEventListener("change", () => {
      dragging[axis] = false;
      postJSON("/api/target", { axis, angle: parseFloat(input.value) });
    });
    input.addEventListener("input", () => {
      postJSON("/api/target", { axis, angle: parseFloat(input.value) });
    });
  });

  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const axis = btn.dataset.axis;
      const angle = parseFloat(btn.dataset.angle);
      postJSON("/api/target", { axis, angle });
    });
  });

  el("btn-estop").addEventListener("click", () => {
    const next = !(latestState && latestState.estop);
    postJSON("/api/estop", { enabled: next });
  });

  el("btn-home").addEventListener("click", () => postJSON("/api/home"));
  el("btn-park").addEventListener("click", () => postJSON("/api/park"));

  el("btn-motor-power").addEventListener("click", () => {
    const next = !(latestState && latestState.motor_power);
    postJSON("/api/motor-power", { enabled: next });
  });

  el("btn-ch10").addEventListener("click", () => {
    const next = !(latestState && latestState.ch10_muted);
    postJSON("/api/ch10-mute", { enabled: next });
  });

  el("btn-transcribe").addEventListener("click", () => postJSON("/api/transcribe"));
}

// --- Draw high-DPI 2D Polar Rig Canvas ---
function drawRig(state) {
  const canvas = el("rig-canvas");
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  if (canvas.width !== Math.round(rect.width * dpr) || canvas.height !== Math.round(rect.height * dpr)) {
    canvas.width = Math.round(rect.width * dpr);
    canvas.height = Math.round(rect.height * dpr);
  }

  const ctx = canvas.getContext("2d");
  ctx.save();
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;
  const cx = w / 2;
  const cy = h / 2 + 6;
  const R = Math.min(w, h) * 0.39;

  ctx.clearRect(0, 0, w, h);

  // Rear cable exclusion zone (bottom 120 deg sector)
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, R, Math.PI * 0.17, Math.PI * 0.83);
  ctx.closePath();
  ctx.fillStyle = "rgba(239, 68, 68, 0.08)";
  ctx.fill();

  // Concentric range rings (0.5m, 1.0m, 1.5m)
  [0.33, 0.66, 1.0].forEach((scale, idx) => {
    ctx.beginPath();
    ctx.arc(cx, cy, R * scale, 0, Math.PI * 2);
    ctx.strokeStyle = idx === 2 ? "rgba(148, 163, 184, 0.28)" : "rgba(148, 163, 184, 0.12)";
    ctx.lineWidth = idx === 2 ? 1.5 : 1;
    ctx.setLineDash(idx === 2 ? [] : [4, 4]);
    ctx.stroke();
  });
  ctx.setLineDash([]);

  // Safe 120 deg operating arcs for S1 (left) and S2 (right)
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.arc(cx, cy, R + 6, -Math.PI * 0.5 - (120 * Math.PI) / 180, -Math.PI * 0.5);
  ctx.strokeStyle = "rgba(34, 211, 238, 0.35)";
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(cx, cy, R + 6, -Math.PI * 0.5, -Math.PI * 0.5 + (120 * Math.PI) / 180);
  ctx.strokeStyle = "rgba(245, 158, 11, 0.35)";
  ctx.stroke();

  // Helper to convert speaker angle (0..120) to canvas radians
  // 0 deg = straight ahead (top), 90 deg = side broadside, 120 deg = outer safe stop
  const s1Rad = -Math.PI / 2 - (state.angles.speaker1 * Math.PI) / 180;
  const s2Rad = -Math.PI / 2 + (state.angles.speaker2 * Math.PI) / 180;
  const panRad = -Math.PI / 2 + (state.angles.pan * Math.PI) / 180;

  // Draw Mic Array acoustic beam cone
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, R * 0.85, panRad - 0.24, panRad + 0.24);
  ctx.closePath();
  const grad = ctx.createRadialGradient(cx, cy, 8, cx, cy, R * 0.85);
  grad.addColorStop(0, "rgba(16, 185, 129, 0.32)");
  grad.addColorStop(1, "rgba(16, 185, 129, 0.0)");
  ctx.fillStyle = grad;
  ctx.fill();

  // Draw Speaker Arms & Carts
  const drawSpeaker = (rad, color, label, deg) => {
    const x = cx + Math.cos(rad) * R;
    const y = cy + Math.sin(rad) * R;

    // 1.5m rod
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(x, y);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Cart glow + node
    ctx.beginPath();
    ctx.arc(x, y, 12, 0, Math.PI * 2);
    ctx.fillStyle = "#0f1624";
    ctx.fill();
    ctx.lineWidth = 3;
    ctx.strokeStyle = color;
    ctx.stroke();

    // Label
    ctx.font = "700 11px ui-monospace, monospace";
    ctx.fillStyle = color;
    ctx.textAlign = "center";
    ctx.fillText(`${label} ${deg.toFixed(0)}°`, x, y - 18);
  };

  drawSpeaker(s1Rad, "#22d3ee", "S1", state.angles.speaker1);
  drawSpeaker(s2Rad, "#f59e0b", "S2", state.angles.speaker2);

  // Center baseplate & rotating UMA-16 array icon
  ctx.save();
  ctx.translate(cx, cy);
  ctx.fillStyle = "#1e293b";
  ctx.strokeStyle = "rgba(148, 163, 184, 0.45)";
  ctx.lineWidth = 1.5;
  ctx.fillRect(-18, -18, 36, 36);
  ctx.strokeRect(-18, -18, 36, 36);

  ctx.rotate((state.angles.pan * Math.PI) / 180);
  ctx.fillStyle = "#10b981";
  ctx.fillRect(-10, -10, 20, 20);
  // Forward arrow on array
  ctx.beginPath();
  ctx.moveTo(0, -19);
  ctx.lineTo(-5, -11);
  ctx.lineTo(5, -11);
  ctx.closePath();
  ctx.fill();
  ctx.restore();

  // Labels
  ctx.font = "600 10px ui-monospace, monospace";
  ctx.fillStyle = "rgba(239, 68, 68, 0.75)";
  ctx.textAlign = "center";
  ctx.fillText("CABLE ZONE (KEEP CLEAR)", cx, cy + R * 0.72);

  ctx.restore();
}

// --- Render telemetry frame ---
function render(state) {
  latestState = state;

  // Top bar pills
  const modePill = el("pill-mode");
  modePill.textContent = state.mode === "simulation" ? "SIMULATION MODE" : "LIVE PI HARDWARE";
  el("pill-temp").textContent = `CPU ${state.health.cpu_temp.toFixed(1)}°C | ${state.health.disk_free_gb} GB`;
  el("pi-ip-label").textContent = `HOST: ${state.pi_host}`;

  const estopBtn = el("btn-estop");
  estopBtn.classList.toggle("active", state.estop);
  estopBtn.textContent = state.estop ? "RESET E-STOP" : "E-STOP";

  const motionBadge = el("motion-badge");
  motionBadge.textContent = state.estop ? "HALTED" : state.moving ? "MOVING" : "IDLE";
  motionBadge.className = `badge ${state.moving ? "badge-moving" : "badge-idle"}`;

  // Motor power button
  const mpBtn = el("btn-motor-power");
  mpBtn.classList.toggle("active", state.motor_power);
  mpBtn.textContent = state.motor_power ? "ON" : "SILENT (OFF)";

  // Ch10 button
  const ch10Btn = el("btn-ch10");
  ch10Btn.classList.toggle("active", state.ch10_muted);
  ch10Btn.textContent = state.ch10_muted ? "CH10 MUTED" : "CH10 LIVE";

  // Angle readouts & sliders
  el("val-s1").textContent = `${state.angles.speaker1.toFixed(1)}°`;
  el("val-s2").textContent = `${state.angles.speaker2.toFixed(1)}°`;
  el("val-pan").textContent = `${state.angles.pan.toFixed(1)}°`;
  el("val-tilt").textContent = `${state.angles.tilt.toFixed(1)}°`;

  if (!dragging.speaker1) el("slider-s1").value = state.angles.target_speaker1;
  if (!dragging.speaker2) el("slider-s2").value = state.angles.target_speaker2;
  if (!dragging.pan) el("slider-pan").value = state.angles.target_pan;
  if (!dragging.tilt) el("slider-tilt").value = state.angles.target_tilt;

  // 16-Channel audio meters
  el("rms-badge").textContent = `RMS: ${state.audio.mean_rms.toFixed(1)} dBFS`;
  state.audio.channels_db.forEach((db, i) => {
    const valEl = el(`mic-val-${i}`);
    const cellEl = el(`mic-cell-${i}`);
    const fillEl = el(`vu-fill-${i}`);

    const isCh10 = i === 9;
    cellEl.classList.toggle("ch10-muted", isCh10 && state.ch10_muted);
    cellEl.classList.toggle("ch10-fault", isCh10 && !state.ch10_muted);

    valEl.textContent = isCh10 && state.ch10_muted ? "MUTE" : `${db.toFixed(0)} dB`;

    // Map -85..-5 dBFS to 4..100% height
    const pct = Math.max(4, Math.min(100, ((db + 85) / 80) * 100));
    fillEl.style.height = `${isCh10 && state.ch10_muted ? 4 : pct}%`;
    fillEl.className = `vu-fill ${isCh10 && state.ch10_muted ? "muted" : isCh10 ? "fault" : ""}`;
  });

  // Transcribe button state
  const sttBtn = el("btn-transcribe");
  sttBtn.disabled = state.transcribing;
  sttBtn.textContent = state.transcribing ? "Recording & Transcribing..." : "● Record & Transcribe";

  // Transcriptions feed (update only when changed)
  const sttSig = JSON.stringify(state.transcriptions);
  if (sttSig !== lastSttSignature) {
    lastSttSignature = sttSig;
    el("stt-feed").innerHTML = state.transcriptions
      .map(
        (item) => `
        <div class="stt-item">
          <div class="stt-text">"${item.text}"</div>
          <div class="stt-meta">
            <span>${item.time} &nbsp;•&nbsp; ${item.angles}</span>
            <span>CONF ${item.confidence}%</span>
          </div>
        </div>`
      )
      .join("");
  }

  // Event log (update only when changed)
  const logSig = JSON.stringify(state.logs);
  if (logSig !== lastLogSignature) {
    lastLogSignature = logSig;
    el("log-feed").innerHTML = state.logs
      .map(
        (l) => `
        <div class="log-row">
          <span class="log-time">${l.time}</span>
          <span class="log-lvl lvl-${l.level}">[${l.level}]</span>
          <span>${l.msg}</span>
        </div>`
      )
      .join("");
  }

  drawRig(state);
}

// --- WebSocket connection with auto-reconnect ---
function connectWS() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  const pill = el("pill-conn");

  ws.onopen = () => {
    pill.textContent = "WS CONNECTED";
    pill.className = "pill pill-ok";
  };
  ws.onmessage = (evt) => render(JSON.parse(evt.data));
  ws.onclose = () => {
    pill.textContent = "RECONNECTING...";
    pill.className = "pill pill-red";
    setTimeout(connectWS, 1500);
  };
}

initAudioWidgets();
bindControls();
connectWS();
