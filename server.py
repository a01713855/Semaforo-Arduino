"""
Servidor puente: Arduino UNO (Serial) o ESP32 (WiFi HTTP) -> Pagina web.
- Arduino UNO: lineas JSON por COM9 @ 9600:
  {"state":"RED","time_left":19,"duration":20}
- ESP32: POST http://<PC-IP>:5000/api/state con el mismo JSON (ver semaforo_esp32.ino)
Expone:
  GET /            -> pagina
  GET /api/status  -> {"state","time_left","duration","connected","last_seen","simulated"}
  POST /api/state  <- ESP32 WiFi
Uso:
  pip install -r requirements.txt
  python server.py [--port COM9] [--baud 9600] [--simulate] [--no-serial] [--web-port 5000]
  ESP32 (sin Serial): python server.py --no-serial
"""
import argparse
import json
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

try:
    import serial  # pyserial
except ImportError:
    serial = None

BASE_DIR = Path(__file__).parent
PUBLIC_DIR = BASE_DIR / "public"

# Estado compartido
state = {
    "state": "RED",
    "time_left": 20,
    "duration": 20,
    "last_seen": 0.0,   # epoch
    "connected": False,
    "simulated": False,
}

VALID = {"RED": 20, "YELLOW": 5, "GREEN": 15}

app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(str(PUBLIC_DIR), "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    p = PUBLIC_DIR / filename
    if p.is_file():
        return send_from_directory(str(PUBLIC_DIR), filename)
    return send_from_directory(str(PUBLIC_DIR), "index.html")


@app.route("/api/state", methods=["POST"])
def api_state():
    """Recibe el push del ESP32 por WiFi (mismo JSON que el Serial)."""
    msg = request.get_json(silent=True) or {}
    s = str(msg.get("state", "")).upper()
    if s not in VALID:
        return jsonify({"ok": False, "error": "state debe ser RED/YELLOW/GREEN"}), 400
    apply_message(msg)
    return jsonify({"ok": True, "state": state["state"]})


@app.route("/api/status")
def api_status():
    now = time.time()
    # Si el dato tiene mas de 3.5 s sin actualizarse, marcamos desconectado
    # (en modo Arduino real el Arduino envia cada 1 s).
    age = now - state["last_seen"] if state["last_seen"] else 9999
    # Compensa la cuenta regresiva del lado servidor
    remaining = state["time_left"]
    if state["last_seen"]:
        elapsed = int(now - state["last_seen"])
        remaining = max(0, state["time_left"] - elapsed)
    connected = state["connected"] and age < 3.5
    return jsonify({
        "state": state["state"],
        "time_left": remaining,
        "duration": state["duration"],
        "connected": connected,
        "simulated": state["simulated"],
        "age": round(age, 1),
    })


def apply_message(msg: dict):
    s = str(msg.get("state", "")).upper()
    if s not in VALID:
        return
    try:
        tl = int(msg.get("time_left", VALID[s]))
    except (TypeError, ValueError):
        tl = VALID[s]
    try:
        dur = int(msg.get("duration", VALID[s]))
    except (TypeError, ValueError):
        dur = VALID[s]
    state["state"] = s
    state["time_left"] = max(0, min(tl, dur))
    state["duration"] = dur
    state["last_seen"] = time.time()
    state["connected"] = True


def serial_loop(port: str, baud: int):
    if serial is None:
        print("[WARN] pyserial no instalado. Usa --simulate o instala requirements.")
        return
    while True:
        try:
            ser = serial.Serial(port, baud, timeout=1)
            print(f"[OK] Leyendo {port} @ {baud}")
        except Exception as e:
            print(f"[ERROR] No se pudo abrir {port}: {e}")
            print("        Ejecuta con --simulate para probar la web sin Arduino.")
            time.sleep(5)
            continue
        failures = 0
        try:
            while True:
                try:
                    chunk = ser.readline()
                    if not chunk:
                        continue
                    line = chunk.decode("utf-8", errors="ignore").strip()
                    if not line.startswith("{"):
                        continue
                    try:
                        msg = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    apply_message(msg)
                    failures = 0
                except Exception as e:
                    failures += 1
                    # Evita spam: avisa cada 10 fallos y reabre el puerto
                    if failures % 10 == 1:
                        print(f"[WARN] serial ({failures}): {e}")
                    try:
                        ser.close()
                    except Exception:
                        pass
                    time.sleep(5)
                    break  # salir al while externo para reabrir
        except Exception as e:
            print(f"[WARN] serial: {e}")
            time.sleep(5)


def simulate_loop():
    """Genera el mismo ciclo del .ino cuando no hay Arduino conectado."""
    print("[SIM] Modo simulado: VERDE 15s -> AMARILLO 5s -> ROJO 20s")
    state["simulated"] = True
    seq = [("GREEN", 15), ("YELLOW", 5), ("RED", 20)]
    while True:
        for name, dur in seq:
            for t in range(dur, 0, -1):
                apply_message({"state": name, "time_left": t, "duration": dur})
                time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM9")
    ap.add_argument("--baud", type=int, default=9600)
    ap.add_argument("--web-port", type=int, default=5000)
    ap.add_argument("--simulate", action="store_true",
                    help="No usa Serial, genera ciclo en el servidor")
    ap.add_argument("--no-serial", action="store_true",
                    help="No abre Serial (usar con ESP32 por WiFi)")
    args = ap.parse_args()

    if args.simulate:
        threading.Thread(target=simulate_loop, daemon=True).start()
    elif not args.no_serial:
        threading.Thread(target=serial_loop, args=(args.port, args.baud), daemon=True).start()
    else:
        print("[OK] Modo WiFi: esperando POST del ESP32 en /api/state")

    print(f"Web en http://localhost:{args.web_port}")
    app.run(host="0.0.0.0", port=args.web_port, debug=False)


if __name__ == "__main__":
    main()
