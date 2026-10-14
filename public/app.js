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
    const d = await r.json();
    last = d;
    lastFetch = Date.now();
    elConn.textContent = d.connected ? "● Conectado" : "● Desconectado";
    elConn.className = "conn " + (d.connected ? "connected" : "disconnected");
    elMode.textContent = d.simulated ? "Simulado (sin Arduino)" : "Serial COM9";
    paint(d.state);
  } catch (e) {
    elConn.textContent = "● Servidor no accesible";
    elConn.className = "conn disconnected";
  }
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
