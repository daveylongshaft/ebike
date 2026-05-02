# eBike Dual-Motor Dual-Battery Controller

A complete power distribution and motor control system for dual-hub-motor ebikes, built on Raspberry Pi Pico W with web-based remote configuration and local 3-button menu interface.

## Features

- **Dual Hub Motors**: Independent front/rear PWM control with current limiting
- **Dual Batteries**: 2× 48V 20Ah packs with automatic SoC-balanced switching (parallel when balanced)
- **Remote Configuration**: WiFi-enabled web UI (headless compatible)
- **Local Menu**: 3-button interface (UP/SEL/DN) + 2"×4" LCD display for field operation
- **Real-time Monitoring**: 4× INA226 current shunts (battery A/B, motor F/R) with voltage/current/range tracking
- **Three Power Modes**:
  - **Range Mode** (0–33% throttle): 12–24V, 10–20A per motor
  - **Mixed Mode** (33–66%): 24–36V, 20–35A per motor
  - **Performance Mode** (66–100%): 36–48V, 35–50A per motor
- **Security**: Hidden WiFi SSID, WPA2 password, HTTP Basic Auth on web UI, configurable 4-digit PIN for bike operation
- **Brake Priority**: PWM immediately kills when brakes engaged; brake lights controlled via relay

## Hardware

### Microcontroller
- **Raspberry Pi Pico W** (€6.50) — MCU + integrated WiFi/BT

### Power Distribution
- 2× 48V 20Ah battery packs (user-supplied)
- 2× 80A inline fuses + holders
- 2× XT90-S antispark connectors
- 4× 24V 40A contactor relays (battery A/B, motor F/R selection)
- Heavy copper busbars / 4 AWG wiring
- Flyback diodes for relay coil protection

### Motor Control
- 2× 48V 30A PWM buck converters (adjustable 0–48V via Pico PWM)
- 2× 50A hub motors (user-supplied)

### Sensing
- 4× INA226 I²C current sense modules (0.1Ω shunt, 80A range)
  - 0x40: Battery A
  - 0x41: Battery B
  - 0x42: Motor Front
  - 0x43: Motor Rear

### User Interface
- 3× push buttons (UP/SEL/DN) for menu navigation
- 1× LCD 20×4 I²C HD44780 module
- 1× twist throttle (0–3.3V analog)
- 2× brake levers (2-wire switch, active high/low configurable)
- Turn signal & brake light outputs

### Total BOM Cost
**€297** (excluding batteries, motors, harnesses)

**→ See [Full Hardware Spec](ebike_controller_spec.md) for complete pinout, sourced components with verified links, and assembly instructions**

## Directory Structure

```
ebike/
├── README.md                          # This file
├── ebike_controller_spec.md           # Full pinout, BOM, build plan
├── main.py                            # MicroPython firmware (Pico W)
├── config.json                        # Runtime config (generated on first boot)
├── firmware/
│   ├── sensors.py                     # INA226 I²C reading
│   ├── motor_controller.py            # PWM + current feedback loop
│   ├── battery_manager.py             # SoC-based battery switching
│   ├── display.py                     # LCD 20×4 menu & status
│   ├── buttons.py                     # Debounce + menu navigation
│   ├── security.py                    # 4-digit PIN entry
│   ├── wifi_server.py                 # Microdot web server (HTTP API)
│   └── utils.py                       # Helpers (unit conversions, averaging, etc.)
├── web_ui/
│   └── index.html                     # Served by Pico W (embedded in main.py for now)
└── docs/
    ├── WIRING.md                      # Detailed wiring guide (power distribution board)
    ├── TUNING.md                      # PWM curve calibration, current limit tweaking
    ├── TROUBLESHOOTING.md             # Common issues + fixes
    └── SAFETY.md                      # Electrical safety warnings
```

## Documentation Map

**Getting Started**
- [**Full Hardware Spec & BOM**](ebike_controller_spec.md) — Complete pinout (GPIO pin assignments), verified component sources with pricing (€297 total), assembly instructions, testing checklist
- [**Quick Start Guide**](#quick-start) — 8-step setup from ordering to field tuning

**Building & Integration**
- [`docs/WIRING.md`](docs/WIRING.md) — Power distribution board layout, relay driver stage, busbar routing, crimp connections
- [`docs/SAFETY.md`](docs/SAFETY.md) — High-voltage warnings, fuse ratings, flyback diode placement, electrical safety checklist

**Operation & Tuning**
- [`docs/TUNING.md`](docs/TUNING.md) — PWM curve calibration, current feedback loop tuning, range estimation refinement
- [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md) — Common issues: I²C bus errors, relay chatter, range discrepancies, WiFi connection problems

**Firmware & Configuration**
- [`main.py`](main.py) — MicroPython entry point (GPIO init, WiFi, control loop, web API)
- [**Configuration**](#configuration) — JSON schema, editing via web UI or serial REPL
- [**API Endpoints**](#api-endpoints) — HTTP/JSON endpoints for remote control and status

## Quick Start

### 1. Order Components
See BOM in `ebike_controller_spec.md`. Lead times: 2–4 weeks from AliExpress.

### 2. Flash Pico W
- Download latest MicroPython UF2 for Pico W from [raspberrypi.com](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html)
- Hold BOOTSEL button, plug in USB, drag UF2 to RPI-RP2 drive
- Copy `main.py` to Pico W (via USB or Thonny IDE)

### 3. Assemble Power Distribution Board
- Wire batteries → XT90-S → fuses → contactors → power bus
- Wire power bus → buck converters → INA226 shunts → motor hubs
- Connect all GND to common ground plane
- Double-check polarity and current ratings before power-on

### 4. Wire Pico W (GPIO)
- Relay drivers (GP2–5) → contactor coil bases (via 1kΩ resistors + Darlington)
- PWM outputs (GP14–15) → buck converter PWM inputs
- Buttons (GP6–8) → 10kΩ pull-ups to 3.3V
- Throttle (GP26) → analog input (0–3.3V)
- I²C bus (GP0/GP1) → all INA226 modules + LCD
- See `ebike_controller_spec.md` full pinout for details

### 5. Power On & Test
- Start with external 48V supply on power bus (no batteries yet)
- Check I²C bus: all 4 INA226 modules + LCD respond
- Test GPIO outputs: relays click when Pico drives pins
- Check PWM: measure voltage on scope (should be 0V at 0% duty, 48V at 100%)

### 6. Configure WiFi & Web
- Pico W starts in STA mode, connects to network named "fahu"
- Once connected, visit `http://<pico-ip>/` in browser
- Log in with user: `davey`, password: `dfg9538` (HTTP Basic Auth)
- Configure PIN code, power curves, current limits via web form

### 7. Calibrate on Test Stand
- Mount motors on stand (no load), enable motors via web UI
- Sweep throttle 0–100%, observe current draw at each PWM setting
- Tune `voltage_range` and `current_limit` tables in config.json
- Test brake priority: brakes should immediately kill PWM

### 8. Mount on Frame
- Secure Pico W + relay board in weatherproof enclosure
- Route wires to hub motors, batteries, brake levers, throttle
- Test full throttle response end-to-end
- Log range data over multiple rides to refine range estimation

## Configuration

Config is stored as JSON on Pico W flash (`config.json`). Edit via:
1. **Web UI** (easiest): http://<pico-ip>/ → fill form → save
2. **Serial REPL**: Connect USB, edit config.json directly, reboot
3. **Local menu**: 3-button interface (PIN required)

**Default config:**
```json
{
    "wifi_ssid": "fahu",
    "wifi_password": "your_wifi_password",
    "web_user": "your_username",
    "web_pass": "your_password",
    "pin_code": "your_4_digit_pin",
    "mode": "range",
    "voltage_range": {
        "range": [12, 24],
        "mixed": [24, 36],
        "performance": [36, 48]
    },
    "current_limit": {
        "range": [10, 20],
        "mixed": [20, 35],
        "performance": [35, 50]
    },
    "throttle_deadzone": 0.05,
    "battery_balance_threshold": 15
}
```

## API Endpoints

All endpoints require HTTP Basic Auth.

- **GET** `/` — Web UI (HTML)
- **GET** `/api/status` — JSON status (throttle, currents, voltages, SoC, range)
- **POST** `/api/motor_control` — Enable/disable motors
  ```json
  {"motor": "f", "enable": true}
  ```
- **POST** `/api/battery_control` — Enable/disable batteries
  ```json
  {"battery": "a", "enable": true}
  ```
- **POST** `/config` — Save config (web form)

## Safety & Legal

⚠️ **High voltage / high current**: 48V DC at up to 100A. Follow standard electrical safety practices.

- Always use fuses rated for your motor current (80A recommended)
- Double-check wire gauges and crimp connections
- Use flyback diodes on all relay coils
- Test in controlled environment before field use
- Wear safety equipment (helmet, gloves) when testing
- Consult local ebike regulations (motor wattage, speed limits, licensing)

**→ See [Safety Checklist](docs/SAFETY.md) for detailed electrical safety guidelines**

## Support & Contributing

**→ See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for common issues and solutions**

For questions, open an issue or contact the author.

## Quick Navigation

| Need Help With | Go To |
|---|---|
| Hardware assembly & wiring | [Hardware Spec](ebike_controller_spec.md) → [Wiring Guide](docs/WIRING.md) |
| PWM tuning & calibration | [Tuning Guide](docs/TUNING.md) |
| WiFi config or API | [Configuration](#configuration) → [API Endpoints](#api-endpoints) |
| Debugging I²C/relay/range issues | [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Electrical safety | [Safety Checklist](docs/SAFETY.md) |
| Firmware source | [main.py](main.py) |

## License

MIT License — see LICENSE file.

---

**Built with Raspberry Pi Pico W, MicroPython, and a lot of debugging.**
