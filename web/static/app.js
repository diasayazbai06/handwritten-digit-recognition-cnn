// DigitNet — клиенттік логика: салу тақтасы, жүктеу, MNIST мысалдары, нәтижені көрсету
const $ = (s) => document.querySelector(s);

/* ---------- Нәтижені көрсету ---------- */
const barsEl = $("#bars");
for (let d = 0; d < 10; d++) {
  barsEl.insertAdjacentHTML("beforeend",
    `<div class="bar" id="bar${d}"><span>${d}</span><div class="bar-track"><div class="bar-fill"></div></div><span class="bar-v">0.0%</span></div>`);
}

function showResult(r) {
  const digitEl = $("#digit");
  digitEl.textContent = r.digit;
  digitEl.classList.remove("pop"); void digitEl.offsetWidth; digitEl.classList.add("pop");
  const pct = r.confidence * 100;
  $("#conf").textContent = pct.toFixed(1) + "%";
  $("#ring").style.setProperty("--p", pct.toFixed(1));
  $("#status").textContent = pct > 90 ? "Модель нәтижеге сенімді" : pct > 60 ? "Модель біршама сенімді" : "Цифр анық емес — қайта салып көріңіз";
  $("#preview").src = r.preview;
  r.probs.forEach((p, d) => {
    const row = $("#bar" + d);
    row.classList.toggle("top", d === r.digit);
    row.querySelector(".bar-fill").style.width = (p * 100).toFixed(1) + "%";
    row.querySelector(".bar-v").textContent = (p * 100).toFixed(1) + "%";
  });
}

function resetResult(msg = "Цифр салынғанын күтуде…") {
  $("#digit").textContent = "?";
  $("#conf").textContent = "—";
  $("#ring").style.setProperty("--p", 0);
  $("#status").textContent = msg;
  $("#preview").removeAttribute("src");
  document.querySelectorAll(".bar").forEach((b) => {
    b.classList.remove("top");
    b.querySelector(".bar-fill").style.width = "0";
    b.querySelector(".bar-v").textContent = "0.0%";
  });
}

async function predictDataUrl(dataUrl) {
  const res = await fetch("/api/predict", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: dataUrl }),
  });
  const r = await res.json();
  if (!res.ok) { resetResult(r.error || "Қате"); return null; }
  showResult(r);
  return r;
}

/* ---------- Салу тақтасы ---------- */
const pad = $("#pad");
const ctx = pad.getContext("2d");
let drawing = false, last = null, dirty = false, timer = null;

function clearPad() {
  ctx.fillStyle = "#0b0d1d";
  ctx.fillRect(0, 0, pad.width, pad.height);
  dirty = false;
  $("#hint").classList.remove("hide");
  resetResult();
}
clearPad();

function pos(e) {
  const r = pad.getBoundingClientRect();
  return { x: (e.clientX - r.left) * (pad.width / r.width), y: (e.clientY - r.top) * (pad.height / r.height) };
}
function schedulePredict(delay) {
  clearTimeout(timer);
  timer = setTimeout(() => dirty && predictDataUrl(pad.toDataURL("image/png")), delay);
}
pad.addEventListener("pointerdown", (e) => {
  drawing = true; last = pos(e); pad.setPointerCapture(e.pointerId);
  $("#hint").classList.add("hide");
  ctx.beginPath(); ctx.arc(last.x, last.y, $("#brush").value / 2, 0, Math.PI * 2);
  ctx.fillStyle = "#fff"; ctx.fill(); dirty = true;
});
pad.addEventListener("pointermove", (e) => {
  if (!drawing) return;
  const p = pos(e);
  ctx.strokeStyle = "#fff"; ctx.lineWidth = $("#brush").value; ctx.lineCap = "round"; ctx.lineJoin = "round";
  ctx.beginPath(); ctx.moveTo(last.x, last.y); ctx.lineTo(p.x, p.y); ctx.stroke();
  last = p; dirty = true;
  schedulePredict(180); // салу барысында нәтижені жаңарту
});
["pointerup", "pointercancel", "pointerleave"].forEach((ev) =>
  pad.addEventListener(ev, () => { if (drawing) { drawing = false; schedulePredict(40); } }));
$("#clearBtn").addEventListener("click", clearPad);

/* ---------- Қойындылар ---------- */
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
  document.querySelectorAll(".tab-pane").forEach((p) => p.classList.toggle("active", p.id === "pane-" + t.dataset.tab));
  resetResult(t.dataset.tab === "upload" ? "Суретті жүктеңіз" : "Цифр салынғанын күтуде…");
  if (t.dataset.tab === "sample") loadSample();
  if (t.dataset.tab === "draw" && dirty) predictDataUrl(pad.toDataURL("image/png"));
}));

/* ---------- Сурет жүктеу ---------- */
const drop = $("#drop"), fileInput = $("#fileInput");
function handleFile(file) {
  if (!file || !file.type.startsWith("image/")) return;
  const reader = new FileReader();
  reader.onload = () => {
    const img = $("#uploadPreview");
    img.src = reader.result; img.hidden = false;
    predictDataUrl(reader.result);
  };
  reader.readAsDataURL(file);
}
fileInput.addEventListener("change", () => handleFile(fileInput.files[0]));
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => handleFile(e.dataTransfer.files[0]));

/* ---------- MNIST мысалдары ---------- */
async function loadSample() {
  const r = await (await fetch("/api/sample")).json();
  $("#sampleImg").src = r.original;
  $("#sampleIdx").textContent = "№" + r.index;
  $("#sampleTrue").textContent = r.label;
  const v = $("#sampleVerdict");
  v.textContent = r.digit === r.label ? "✓ Дұрыс танылды" : `✗ Қате: модель ${r.digit} деп болжады`;
  v.className = "verdict " + (r.digit === r.label ? "ok" : "no");
  showResult(r);
}
$("#sampleBtn").addEventListener("click", loadSample);

/* ---------- Hero: тірі мысал ---------- */
const heroBars = $("#heroBars");
for (let d = 0; d < 10; d++) heroBars.insertAdjacentHTML("beforeend", `<div data-d="${d}"></div>`);
async function heroTick() {
  try {
    const r = await (await fetch("/api/sample")).json();
    $("#heroImg").src = r.original;
    $("#heroDigit").textContent = r.digit;
    $("#heroConf").textContent = (r.confidence * 100).toFixed(1) + "%";
    $("#heroTrue").textContent = r.label;
    [...heroBars.children].forEach((b, d) => {
      b.style.height = Math.max(3, r.probs[d] * 100) + "%";
      b.classList.toggle("top", d === r.digit);
    });
  } catch (e) { /* сервер қолжетімсіз */ }
}
heroTick();
setInterval(heroTick, 3500);

/* ---------- URL арқылы қойындыны ашу: #draw, #upload, #sample ---------- */
(() => {
  const tab = location.hash.slice(1);
  const btn = document.querySelector(`.tab[data-tab="${tab}"]`);
  if (btn) { btn.click(); document.getElementById("demo").scrollIntoView(); }
})();
