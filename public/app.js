// Polling cada 1 s a /api/status + countdown local suave
const elRed = document.getElementById("light-red");
const elYellow = document.getElementById("light-yellow");
const elGreen = document.getElementById("light-green");
const elState = document.getElementById("state-name");
const elCount = document.getElementById("count");
const elBar = document.getElementById("bar-fill");
const elConn = document.getElementById("conn");
const elMode = document.getElementById("mode");

let last = { state: null, time_left: 0, duration: 1 };
let lastFetch = 0;
let demo = false;          // modo prueba: sin servidor, simula el ciclo local
const DEMO_SEQ = [["GREEN", 15], ["YELLOW", 5], ["RED", 20]];

const NAMES = { RED: "ROJO", YELLOW: "AMARILLO", GREEN: "VERDE" };

function paint(state) {
  elRed.classList.toggle("on", state === "RED");
  elYellow.classList.toggle("on", state === "YELLOW");
  elGreen.classList.toggle("on", state === "GREEN");
  elState.textContent = NAMES[state] || state || "—";
}

async function poll() {
  try {
    const r = await fetch("/api/status", { cache: "no-store" });
    if (!r.ok) throw new Error("sin servidor");
    const d = await r.json();
    demo = false;
    last = d;
    lastFetch = Date.now();
    elConn.textContent = d.connected ? "● Conectado" : "● Desconectado";
    elConn.className = "conn " + (d.connected ? "connected" : "disconnected");
    elMode.textContent = d.simulated ? "Simulado (sin Arduino)" : "Serial COM9";
    paint(d.state);
  } catch (e) {
    // Sin servidor (ej. GitHub Pages): modo prueba con ciclo local
    if (!demo) {
      demo = true;
      elConn.textContent = "● Modo prueba (sin Arduino)";
      elConn.className = "conn connected";
      elMode.textContent = "Demo local";
      startDemo();
    }
  }
}

// Modo prueba: reproduce VERDE 15s -> AMARILLO 5s -> ROJO 20s en el navegador
let demoTimer = null;
function startDemo() {
  if (demoTimer) return;
  let idx = 0;
  const tick = () => {
    if (!demo) return;
    const name = DEMO_SEQ[idx][0];
    const dur = DEMO_SEQ[idx][1];
    last = { state: name, time_left: dur, duration: dur };
    lastFetch = Date.now();
    paint(name);
    let t = dur;
    demoTimer = setInterval(() => {
      if (!demo) { clearInterval(demoTimer); demoTimer = null; return; }
      t--;
      if (t <= 0) {
        clearInterval(demoTimer); demoTimer = null;
        idx = (idx + 1) % DEMO_SEQ.length;
        tick();
        return;
      }
      last = { state: name, time_left: t, duration: dur };
      lastFetch = Date.now();
    }, 1000);
  };
  tick();
}

// Countdown local: interpola entre polls para que no se vea a saltos
setInterval(() => {
  const elapsed = (Date.now() - lastFetch) / 1000;
  const remain = Math.max(0, Math.round((last.time_left || 0) - elapsed));
  elCount.textContent = lastFetch ? remain : "—";
  const dur = last.duration || 1;
  elBar.style.width = ((remain / dur) * 100) + "%";
}, 250);

poll();
setInterval(poll, 1000);
