# Semáforo — Arduino UNO + Python + Web

Fiel al Figma `semaforo`: carcasa `#B7B7B7`, rojo `#FF0000` arriba,
amarillo `#F4FF2D` medio, verde `#15F14C` abajo, poste `#BFBFBF`, título `STATUS` Inter 36px.

## 1. Arduino
1. Abre `semaforo.ino` en Arduino IDE.
2. Conecta: Rojo→pin 2, Amarillo→pin 3, Verde→pin 4 (+ resistencias 220Ω a GND).
3. Herramientas → Placa: Arduino UNO, Puerto: COM9. Sube el sketch.
4. Abre el Monitor Serial a 9600: debes ver `{"state":"GREEN",...}` cada segundo.

## 2. Servidor (Python)
```
pip install -r requirements.txt
python server.py --port COM9 --baud 9600
```
Web en http://localhost:5000

Sin Arduino a la mano para probar la web:
```
python server.py --simulate
```

## Variante ESP32
Ver `semaforo_esp32.ino` (WiFi + POST a `/api/state`) y correr:
```
python server.py --no-serial
```
