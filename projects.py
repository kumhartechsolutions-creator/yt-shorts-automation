"""Project catalog and state tracking for daily Arduino/ESP32 YouTube Shorts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

STATE_FILE = Path(__file__).parent / "state.json"

# Already published on Zahid Bashir Young Innovator before this automation
INITIAL_COMPLETED_IDS = [
    "esp32-weather-station",
    "arduino-rfid-door-lock",
    "arduino-smart-dustbin",
]


@dataclass(frozen=True)
class ShortProject:
    id: str
    title: str
    hook_badge: str
    hook_headline: str
    cost_label: str
    sim_mode: str  # "radar", "waveform", "matrix", "laser"
    voiceover: str
    code_filename: str
    code_snippet: str
    full_code: str
    wiring_md: str
    description: str
    tags: List[str]
    pinned_comment: str
    gist_url: Optional[str] = None
    captions: List[str] = field(default_factory=list)
    image_prompt: str = ""


PROJECTS: List[ShortProject] = [
    ShortProject(
        id="esp32-mini-radar",
        title="ESP32 Mini Radar Scanner for $6! 📡 #shorts",
        hook_badge="ESP32 + OLED",
        hook_headline="DIY $6 MINI RADAR",
        cost_label="$6 BUILD",
        sim_mode="radar",
        voiceover=(
            "Build a six-dollar ESP32 Mini Radar! "
            "Ultrasonic eyes sweep 180 degrees on a micro servo, "
            "the OLED plots targets live in centimeters, "
            "and the buzzer triggers the instant anything gets too close! "
            "Full code and wiring are in the pinned comment. Subscribe for daily builds!"
        ),
        code_filename="esp32_mini_radar.ino",
        code_snippet=(
            "int dist = readDistanceCm();\n"
            "drawRadarFrame(angle, dist);\n"
            "if (dist > 0 && dist <= 25) {\n"
            "  digitalWrite(BUZZER_PIN, HIGH);\n"
            "}"
        ),
        full_code=(
            "// ESP32 Mini Radar Scanner | Zahid Bashir Young Innovator\n"
            "#include <Wire.h>\n#include <Adafruit_GFX.h>\n#include <Adafruit_SSD1306.h>\n"
            "#include <ESP32Servo.h>\n#include <math.h>\n\n"
            "#define TRIG_PIN 25\n#define ECHO_PIN 26\n#define SERVO_PIN 13\n"
            "#define BUZZER_PIN 27\n#define LED_PIN 14\n\n"
            "Adafruit_SSD1306 display(128, 64, &Wire, -1);\nServo radarServo;\n\n"
            "int readDistanceCm() {\n"
            "  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);\n"
            "  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);\n"
            "  digitalWrite(TRIG_PIN, LOW);\n"
            "  long d = pulseIn(ECHO_PIN, HIGH, 20000);\n"
            "  return d == 0 ? -1 : (int)(d * 0.0343 / 2.0);\n"
            "}\n\n"
            "void setup() {\n"
            "  pinMode(TRIG_PIN, OUTPUT); pinMode(ECHO_PIN, INPUT);\n"
            "  pinMode(BUZZER_PIN, OUTPUT); pinMode(LED_PIN, OUTPUT);\n"
            "  Wire.begin(21, 22);\n"
            "  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);\n"
            "  radarServo.attach(SERVO_PIN, 500, 2400);\n"
            "}\n\n"
            "void loop() {\n"
            "  for (int a = 15; a <= 165; a += 3) {\n"
            "    radarServo.write(a); delay(35);\n"
            "    int cm = readDistanceCm();\n"
            "    digitalWrite(LED_PIN, (cm > 0 && cm <= 25));\n"
            "    digitalWrite(BUZZER_PIN, (cm > 0 && cm <= 25));\n"
            "  }\n"
            "}\n"
        ),
        wiring_md=(
            "# ESP32 Mini Radar Wiring\n"
            "- OLED SDA -> GPIO 21 | SCL -> GPIO 22 | VCC -> 3.3V\n"
            "- HC-SR04 TRIG -> GPIO 25 | ECHO -> GPIO 26 (via 1k/2k divider)\n"
            "- SG90 Servo -> GPIO 13 | LED -> GPIO 14 | Buzzer -> GPIO 27\n"
        ),
        description=(
            "Build your own ESP32 Mini Radar Scanner with a live 0.96\" OLED display and target alert!\n\n"
            "Components (~$6): ESP32 DevKit V1, HC-SR04 Ultrasonic Sensor, SG90 Micro Servo, "
            "0.96\" I2C OLED (SSD1306), Active Buzzer, Red LED.\n\n"
            "Full Code & Wiring: {gist_url}\n\n"
            "Subscribe to Zahid Bashir Young Innovator for daily ESP32 & Arduino projects!\n"
            "#shorts #esp32 #arduino #radar #iot #electronics #diy #embedded #maker"
        ),
        tags=[
            "esp32", "arduino", "radar", "ultrasonic sensor", "oled", "iot",
            "electronics", "diy", "embedded systems", "shorts", "maker",
        ],
        pinned_comment=(
            "Full ESP32 code & pin-by-pin wiring guide: {gist_url}\n"
            "Comment 'RADAR' if you want Part 2 with Wi-Fi phone alerts!"
        ),
        gist_url="https://gist.github.com/kumhartechsolutions-creator/77eca353b3012fc99246cca62a6c0eb2",
        captions=[
            "Build a $6 ESP32 Mini Radar!",
            "Servo sweeps 180° nonstop",
            "OLED plots live target distance",
            "Buzzer fires under 25 cm!",
            "Code in pinned comment 👇",
        ],
        image_prompt=(
            "macro studio photography of an ESP32 DevKit on a breadboard wired with colorful jumper wires "
            "to an HC-SR04 ultrasonic sensor mounted on a blue SG90 micro servo, a glowing 0.96 inch OLED display, "
            "and a red LED on a dark electronics workbench, dramatic cyan rim light, photorealistic, 8k"
        ),
    ),
    ShortProject(
        id="arduino-ultrasonic-piano",
        title="Touchless Arduino Air Piano! 🎹 #shorts",
        hook_badge="ARDUINO + HC-SR04",
        hook_headline="TOUCHLESS AIR PIANO",
        cost_label="$4 BUILD",
        sim_mode="waveform",
        voiceover=(
            "Play music in mid-air with a four-dollar Arduino Air Piano! "
            "An ultrasonic sensor measures your hand height in real time "
            "and maps every zone to a clean musical note on a piezo speaker. "
            "Zero buttons, pure physics! Full code is in the pinned comment. Subscribe!"
        ),
        code_filename="arduino_air_piano.ino",
        code_snippet=(
            "int notes[] = {262, 294, 330, 349, 392, 440, 494, 523};\n"
            "int idx = constrain(map(dist, 5, 40, 0, 7), 0, 7);\n"
            "if (dist <= 40) tone(BUZZER_PIN, notes[idx]);\n"
            "else noTone(BUZZER_PIN);"
        ),
        full_code=(
            "// Touchless Arduino Air Piano | Zahid Bashir Young Innovator\n"
            "#define TRIG_PIN 9\n#define ECHO_PIN 10\n#define BUZZER_PIN 6\n\n"
            "const int NOTES[] = {262, 294, 330, 349, 392, 440, 494, 523};\n\n"
            "void setup() {\n"
            "  pinMode(TRIG_PIN, OUTPUT); pinMode(ECHO_PIN, INPUT); pinMode(BUZZER_PIN, OUTPUT);\n"
            "}\n\n"
            "void loop() {\n"
            "  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);\n"
            "  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);\n"
            "  digitalWrite(TRIG_PIN, LOW);\n"
            "  long dur = pulseIn(ECHO_PIN, HIGH, 20000);\n"
            "  int cm = dur ? (int)(dur * 0.0343 / 2.0) : 999;\n"
            "  if (cm >= 4 && cm <= 40) {\n"
            "    int i = constrain(map(cm, 4, 40, 0, 7), 0, 7);\n"
            "    tone(BUZZER_PIN, NOTES[i]);\n"
            "  } else {\n"
            "    noTone(BUZZER_PIN);\n"
            "  }\n"
            "  delay(40);\n"
            "}\n"
        ),
        wiring_md=(
            "# Arduino Air Piano Wiring\n"
            "- HC-SR04 VCC -> 5V | GND -> GND | TRIG -> D9 | ECHO -> D10\n"
            "- Passive Piezo Buzzer (+) -> D6 | (-) -> GND\n"
        ),
        description=(
            "Play musical notes in mid-air with an Arduino Uno and HC-SR04 ultrasonic sensor!\n\n"
            "Components (~$4): Arduino Uno, HC-SR04 Ultrasonic Sensor, Passive Buzzer, Jumper Wires.\n\n"
            "Full Code & Wiring: {gist_url}\n\n"
            "Subscribe to Zahid Bashir Young Innovator for daily Arduino & ESP32 builds!\n"
            "#shorts #arduino #arduinoproject #electronics #diy #music #iot #maker"
        ),
        tags=[
            "arduino", "air piano", "ultrasonic", "hc-sr04", "buzzer",
            "arduino project", "diy electronics", "shorts", "maker",
        ],
        pinned_comment=(
            "Full Arduino Air Piano code & wiring: {gist_url}\n"
            "Which song should I play on this next? Comment below!"
        ),
        captions=[
            "Play music in MID-AIR!",
            "Hand height picks the note",
            "Zero buttons, just ultrasonic",
            "8-note C-major scale live!",
            "Code in pinned comment 👇",
        ],
        image_prompt=(
            "macro studio photography of an Arduino Uno R3 on a dark electronics workbench wired to an HC-SR04 "
            "ultrasonic sensor and a black piezo buzzer on a breadboard with colorful jumper wires, "
            "dramatic neon blue and emerald lighting, photorealistic, 8k"
        ),
    ),
    ShortProject(
        id="arduino-laser-tripwire",
        title="DIY Arduino Laser Tripwire Alarm! 🔴 #shorts",
        hook_badge="ARDUINO SECURITY",
        hook_headline="LASER TRIPWIRE ALARM",
        cost_label="$3 BUILD",
        sim_mode="laser",
        voiceover=(
            "Make a spy-style Arduino Laser Tripwire for three dollars! "
            "A five-milliwatt laser aims straight at a photoresistor. "
            "The moment someone crosses the beam, the voltage drops and the alarm blasts! "
            "Full code and circuit are in the pinned comment. Subscribe!"
        ),
        code_filename="arduino_laser_tripwire.ino",
        code_snippet=(
            "int light = analogRead(LDR_PIN);\n"
            "if (light < THRESHOLD) {\n"
            "  tone(BUZZER_PIN, 2200);\n"
            "  digitalWrite(LED_PIN, HIGH);\n"
            "}"
        ),
        full_code=(
            "// Arduino Laser Tripwire Alarm | Zahid Bashir Young Innovator\n"
            "#define LDR_PIN A0\n#define BUZZER_PIN 8\n#define LED_PIN 7\n#define THRESHOLD 500\n\n"
            "void setup() {\n"
            "  pinMode(BUZZER_PIN, OUTPUT); pinMode(LED_PIN, OUTPUT);\n"
            "}\n\n"
            "void loop() {\n"
            "  int val = analogRead(LDR_PIN);\n"
            "  if (val < THRESHOLD) {\n"
            "    digitalWrite(LED_PIN, HIGH);\n"
            "    tone(BUZZER_PIN, 2200, 150);\n"
            "    delay(200);\n"
            "  } else {\n"
            "    digitalWrite(LED_PIN, LOW);\n"
            "    noTone(BUZZER_PIN);\n"
            "  }\n"
            "}\n"
        ),
        wiring_md=(
            "# Arduino Laser Tripwire Wiring\n"
            "- KY-008 Laser -> 5V & GND\n"
            "- LDR + 10k resistor divider -> A0\n"
            "- Buzzer -> D8 | Alert LED -> D7\n"
        ),
        description=(
            "Build a $3 spy-style Laser Tripwire Alarm using Arduino Uno and an LDR sensor!\n\n"
            "Full Code & Wiring: {gist_url}\n\n"
            "Subscribe to Zahid Bashir Young Innovator for daily Arduino & ESP32 builds!\n"
            "#shorts #arduino #laser #security #diy #electronics #arduinoproject"
        ),
        tags=[
            "arduino", "laser tripwire", "security system", "ldr",
            "diy electronics", "shorts", "maker", "innovation",
        ],
        pinned_comment=(
            "Full Laser Tripwire code & wiring: {gist_url}\n"
            "Comment 'SPY' if you want a version with ESP32 Telegram alerts!"
        ),
        captions=[
            "$3 Spy Laser Tripwire!",
            "Laser locks onto LDR sensor",
            "Cross the beam = instant alarm",
            "20 lines of Arduino code!",
            "Code in pinned comment 👇",
        ],
        image_prompt=(
            "macro studio photography of an Arduino Uno wired on a breadboard with a glowing red KY-008 laser module "
            "shining a bright red beam onto an LDR photoresistor and piezo buzzer on a dark electronics workbench, "
            "dramatic moody lighting, photorealistic, 8k"
        ),
    ),
]


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"uploaded": list(INITIAL_COMPLETED_IDS), "history": []}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def get_next_project() -> ShortProject:
    state = load_state()
    done = set(state.get("uploaded", []))
    for proj in PROJECTS:
        if proj.id not in done:
            return proj
    raise RuntimeError("All queued projects have been uploaded! Add more entries to PROJECTS in projects.py.")


def mark_project_uploaded(project_id: str, video_id: str, gist_url: str) -> None:
    state = load_state()
    uploaded = state.setdefault("uploaded", [])
    if project_id not in uploaded:
        uploaded.append(project_id)
    state.setdefault("history", []).append(
        {"project_id": project_id, "video_id": video_id, "gist_url": gist_url}
    )
    save_state(state)
