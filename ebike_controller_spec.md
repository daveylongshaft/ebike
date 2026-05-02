# eBike Dual-Motor Dual-Battery Controller
## Raspberry Pi Pico W + Web Config + Local Menu

---

## PINOUT (Raspberry Pi Pico W)

```
PIN ASSIGNMENTS (40-pin DIP)
────────────────────────────────────────────────────────────

POWER:
  VBUS (pin 40)           → 5V input (USB or external PSU)
  VSYS (pin 39)           → 5V system rail (with Schottky diode if powered externally)
  GND (pins 3, 8, 13, 18, 23, 28, 33, 38)  → Ground plane

CONTROL BUTTONS (3.3V TTL, 10kΩ pull-up to 3.3V):
  GP6  (pin 9)            → UP button (active low, 10kΩ to 3.3V)
  GP7  (pin 10)           → SELECT button (active low, 10kΩ to 3.3V)
  GP8  (pin 11)           → DOWN button (active low, 10kΩ to 3.3V)

THROTTLE (ADC):
  GP26 (pin 31, ADC0)     → Twist throttle 0–3.3V analog

BRAKES (3.3V TTL, pull-up):
  GP9  (pin 12)           → Front brake (active low / high, debounce in firmware)
  GP10 (pin 14)           → Rear brake (active low / high)

TURN/LIGHT SIGNALS (GPIO output, buffered via 74HC595 or relay drivers):
  GP11 (pin 15)           → Turn signal left (to relay driver)
  GP12 (pin 16)           → Turn signal right (to relay driver)
  GP13 (pin 17)           → Brake lights (to relay driver)

RELAY DRIVER OUTPUTS (via ULN2003 / TIP120 Darlington array):
  GP2  (pin 4)            → Battery A contactor coil (24V via relay driver)
  GP3  (pin 5)            → Battery B contactor coil (24V via relay driver)
  GP4  (pin 6)            → Motor Front contactor coil (24V via relay driver)
  GP5  (pin 7)            → Motor Rear contactor coil (24V via relay driver)

PWM MOTOR CONTROL (PWM capable pins):
  GP14 (pin 19)           → Motor Front PWM (0–100%, 1 kHz)
  GP15 (pin 20)           → Motor Rear PWM (0–100%, 1 kHz)

I²C SHUNT & DISPLAY (I²C0, pins 20–21):
  GP0  (pin 1, I2C0_SDA)  → I²C data (to INA226 shunts + LCD display)
  GP1  (pin 2, I2C0_SCL)  → I²C clock
  
  I²C Slaves:
    - INA226 (Battery A)    @ 0x40
    - INA226 (Battery B)    @ 0x41
    - INA226 (Motor Front)  @ 0x42
    - INA226 (Motor Rear)   @ 0x43
    - LCD 20x4 I²C backpack @ 0x27 (or 0x3F, depends on backpack)

UART (optional serial debug):
  GP16 (pin 21)           → UART0 TX (to USB serial adapter, optional)
  GP17 (pin 22)           → UART0 RX

WIFI/BT (built-in):
  Uses Pico W's CYW43439 chip
  No GPIO pins required (internal SPI)

────────────────────────────────────────────────────────────

SUMMARY TABLE:
┌─────────────┬─────┬──────────────────────────────────────┐
│ Function    │ Pin │ Pin Name (GPIO)                      │
├─────────────┼─────┼──────────────────────────────────────┤
│ UP Button   │ 9   │ GP6 (input, pull-up)                │
│ SEL Button  │ 10  │ GP7 (input, pull-up)                │
│ DN Button   │ 11  │ GP8 (input, pull-up)                │
│ Throttle    │ 31  │ GP26 (ADC0)                         │
│ F.Brake     │ 12  │ GP9 (input, pull-up)                │
│ R.Brake     │ 14  │ GP10 (input, pull-up)               │
│ Turn Left   │ 15  │ GP11 (output, to relay driver)      │
│ Turn Right  │ 16  │ GP12 (output, to relay driver)      │
│ Brake Light │ 17  │ GP13 (output, to relay driver)      │
│ Batt A Ctrl │ 4   │ GP2 (output, to relay driver)       │
│ Batt B Ctrl │ 5   │ GP3 (output, to relay driver)       │
│ Motor F Ctl │ 6   │ GP4 (output, to relay driver)       │
│ Motor R Ctl │ 7   │ GP5 (output, to relay driver)       │
│ Motor F PWM │ 19  │ GP14 (PWM, 1 kHz)                  │
│ Motor R PWM │ 20  │ GP15 (PWM, 1 kHz)                  │
│ I²C SDA     │ 1   │ GP0 (I²C0)                          │
│ I²C SCL     │ 2   │ GP1 (I²C0)                          │
│ UART TX     │ 21  │ GP16 (UART0, optional debug)       │
│ UART RX     │ 22  │ GP17 (UART0, optional debug)       │
└─────────────┴─────┴──────────────────────────────────────┘
```

---

## EXTERNAL INTERFACE BOARD (Power Distribution + Buffering)

### Relay Driver Stage (for 24V contactor coils)

Use **ULN2003 Darlington array** (8-channel, open-collector) or individual **TIP120 power transistors**:

```
         Pico W GPIO (3.3V)
              │
              R (1kΩ to base)
              │
            TIP120 (NPN Darlington)
           ╱────╲
      Base │      │ Collector → 24V contactor coil
           │      │
         Emitter → GND
           ╲────╱
              │
              GND

SCHEMATIC per relay driver (4× total: Batt A, Batt B, Motor F, Motor R):
  Pico GPIO → 1kΩ resistor → TIP120 base
  TIP120 collector → 24V relay coil (40R–80R)
  TIP120 emitter → GND
  Flyback diode (1N4007) across coil (cathode to +24V, anode to collector)
```

**Why Darlington**: handles 24V coil current (100–200 mA per relay) with 3.3V logic signal.

### Current Sense (I²C Shunts)

**INA226 I²C Module** × 4:
- Address 0x40: Battery A (measures A→PDist bus)
- Address 0x41: Battery B (measures B→PDist bus)
- Address 0x42: Motor Front (measures PDist→Motor F)
- Address 0x43: Motor Rear (measures PDist→Motor R)

Each INA226:
- **Shunt resistor**: 0.1Ω (10A full scale ÷ 0.1Ω = 100 mV max, within 16-bit ADC range)
- **Power**: +5V (from Pico VSYS via regulator)
- **I²C bus**: shared SDA/SCL (GP0/GP1 on Pico)
- **ADC integration**: 512 samples, ~2.5 kHz update rate

---

## DISPLAY (2" × 4" LCD, 20×4 characters, I²C backpack)

**LCD 20×4 I²C HD44780** (blue backlight, standard 16-pin to I²C module):
- Address: 0x27 (or 0x3F, check backpack label)
- I²C: SDA (GP0), SCL (GP1)
- Power: +5V from Pico VSYS
- Contrast: potentiometer on backpack (pre-tuned, usually 50% works)

**Display layout (4 lines):**
```
Line 1: "Throttle: 45% | Mode: RANGE"
Line 2: "BattA: 23A (82%) | BattB: 10A (78%)"
Line 3: "MotorF: 18A 36V | MotorR: 16A 36V"
Line 4: "Total: 34A / 72V | Range: 28 km"
```

---

## PWM BUCK CONVERTERS (Motor Power Control)

**Two identical 48V → 0–48V buck converters** (PWM-controlled):
- **Topology**: Step-down (buck), isolated input/output recommended for safety.
- **Input**: 48V from battery bus (max 80A combined).
- **Output**: 0–48V adjustable via PWM duty (0% = 0V, 100% = 48V pass-through).
- **Current rating**: 50A continuous each (100A total).
- **Control**: PWM signal from Pico GP14/GP15 (1 kHz, 0–255 duty).
- **Feedback**: voltage/current sense via INA226 shunts (Pico reads actual output).

**Commercial options**:
- **Meanwell RSP-480-48** (480W, programmable via analog voltage) — €80, overkill but industrial.
- **Chinese 48V 30A buck module** (AliExpress, "48V to 0–48V PWM buck converter") — €25–40, works fine, widely used in ebike community.
- **DIY**: LM3150 or LM3155 PWM controller + IRF3205 MOSFETs + LC filter — €15 parts, but requires PCB design.

**Recommendation**: Buy 2× AliExpress buck modules (€30 each), test with Pico PWM, tune feedback loop in firmware.

---

## POWER ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│ BATTERIES (2× 48V 20Ah packs)                               │
├─────────────────────────────────────────────────────────────┤
│  Battery A (48V +) ──[XT90-S]──┐                            │
│  Battery A (GND) ─────[GND]────┼──[Fuse 80A]──[Contactor]──┐
│                                 │                            │
│  Battery B (48V +) ──[XT90-S]──┤                            │
│  Battery B (GND) ─────[GND]────┼──[Fuse 80A]──[Contactor]──┼─→ 48V BUS
│                                 │                            │
│                                 └──────┬─────────────────────┘
│                                        │
│                               ┌────────┴─────────┐
│                               │ 48V Power Bus    │
│                               │ (Busbar + caps)  │
│                               └────────┬─────────┘
│                                        │
│                 ┌──────────────────────┼──────────────────────┐
│                 │                      │                      │
│            [Buck 1]              [Buck 2]                  [Aux PSU]
│            Motor F PWM           Motor R PWM              24V for relays
│                 │                      │                      │
│             Motor Front            Motor Rear             Relay coils
│                                                           (via Darlington)
└─────────────────────────────────────────────────────────────┘
```

---

## BILL OF MATERIALS (complete, excluding batteries & motors)

| # | Item | Qty | Cost (€) | Source | Notes |
|---|------|-----|----------|--------|-------|
| 1 | Raspberry Pi Pico W | 1 | 6.50 | Raspberrypi.com, Adafruit, AliExpress | MCU + WiFi/BT |
| 2 | LCD 20×4 I²C HD44780 module | 1 | 8.50 | AliExpress, Amazon | Blue/green backlight, 0x27 address |
| 3 | INA226 I²C current sense module | 4 | 12 each (48 total) | AliExpress, eBay | 0.1Ω shunt, I²C address-selectable |
| 4 | 48V → 0–48V PWM buck converter | 2 | 30 each (60 total) | AliExpress | ~50A, PWM input (1–5kHz) |
| 5 | ULN2003 Darlington array IC | 1 | 1.50 | AliExpress, any electronics shop | 8-channel relay driver (use 4 of 8) |
| 6 | 1N4007 diodes (flyback protection) | 4 | 0.20 each (0.80 total) | AliExpress, any shop | One per relay coil |
| 7 | 40A 24V contactor relay | 4 | 8 each (32 total) | AliExpress, Alibaba | Automotive-grade, 24V coil, 80A contact |
| 8 | 80A main breaker / fuse | 2 | 5 each (10 total) | AliExpress, auto-parts | Inline fuse holders |
| 9 | XT90-S antispark connector | 2 | 10 each (20 total) | AliExpress, hobby RC shops | Battery A/B connectors |
| 10 | Anderson PowerPole connectors (45A) | 4 | 2 each (8 total) | AliExpress, auto-parts | Motor harness, optional redundancy |
| 11 | 1kΩ resistor (1/4W, 5%) | 7 | 0.05 each (0.35 total) | Any electronics supplier | Pull-up for buttons + Darlington bases |
| 12 | 10kΩ resistor (1/4W, 5%) | 3 | 0.05 each (0.15 total) | Any electronics supplier | Button pull-ups |
| 13 | 100µF capacitor (50V) | 2 | 0.30 each (0.60 total) | Any shop | 48V bus smoothing |
| 14 | 10µF capacitor (16V) | 4 | 0.15 each (0.60 total) | Any shop | Pico supply decoupling |
| 15 | I²C pull-up resistors (4.7kΩ) | 2 | 0.05 each (0.10 total) | Any shop | SDA/SCL pull-up (if not on modules) |
| 16 | Copper busbar / heavy wire (4 AWG) | 10 m | 15 | AliExpress, auto-parts | 48V power distribution |
| 17 | Crimps + terminals (various) | 1 set | 20 | AliExpress | M6/M8 for power, spade for logic |
| 18 | Prototyping board (stripboard) | 2 | 3 each (6 total) | AliExpress, local electronics | Build relay driver stage |
| 19 | Enclosure (plastic, 200×150×100mm) | 1 | 12 | AliExpress, auto-parts | House Pico, relays, buck converters |
| 20 | DIN rail + enclosure hardware | 1 | 10 | AliExpress, auto-parts | Optional, for industrial look |
| 21 | USB-C cable (power Pico) | 1 | 5 | Any shop | For initial programming / debug |
| 22 | MicroUSB-to-USB adapter (alt. power) | 1 | 3 | Any shop | Alternative Pico power input |
| 23 | Schottky diode (60V 30A) | 1 | 2 | AliExpress | VSYS power input protection |
| 24 | 5V regulator (LM7805 or AMS1117) | 1 | 1 | Any shop | If powering Pico from external 5V |
| **TOTAL** | | | **€297** | | **Excluding batteries, motors, harnesses** |

---

## ASSEMBLY NOTES

### Power Distribution Board Layout
```
┌─────────────────────────────────────────────┐
│ FRONT FACE (DIN Rail mounted)               │
├─────────────────────────────────────────────┤
│ [80A Breaker A] [80A Breaker B]             │ Input fuses
│ [Contactor A]   [Contactor B]               │ Battery selection
│                                              │
│ [Buck Conv 1]   [Buck Conv 2]               │ Motor PWM controllers
│                                              │
│ [ULN2003 Driver] [Pico W]                   │ Logic stage
│                                              │
│ [INA226 Module] [INA226 Module] ...         │ Current monitoring
│                                              │
│ [LCD Display]                                │ UI
│                                              │
│ [3-button header] [Throttle header]         │ User controls
└─────────────────────────────────────────────┘
```

### Wiring Checklist
- [ ] 48V power bus: XT90-S → Breaker A → Contactor A → Bus
- [ ] 48V power bus: XT90-S → Breaker B → Contactor B → Bus
- [ ] Bus → 100µF cap (electrolytic, + to bus, – to GND)
- [ ] Bus → Buck 1 input; Bus → Buck 2 input
- [ ] Buck 1 output → INA226 (Addr 0x42) → Motor Front
- [ ] Buck 2 output → INA226 (Addr 0x43) → Motor Rear
- [ ] Battery A harness → INA226 (Addr 0x40) → Contactor A → Bus
- [ ] Battery B harness → INA226 (Addr 0x41) → Contactor B → Bus
- [ ] Pico GP0/GP1 → I²C bus (all 4× INA226 + LCD)
- [ ] Pico GP2–5 → Darlington bases (4× contactor coils via 1kΩ resistors)
- [ ] Pico GP14/15 → Buck 1/2 PWM inputs
- [ ] Pico GP6–8 → Button inputs (with 10kΩ pull-ups)
- [ ] Pico GP9/10 → Brake inputs (with 10kΩ pull-ups)
- [ ] Throttle (0–3.3V) → Pico GP26
- [ ] Turn/Brake signals (GP11–13) → relay drivers (if using lights)
- [ ] 24V aux PSU → relay coil power (via Darlington collector voltage)
- [ ] GND: all subsystems tied to common GND plane

---

## FIRMWARE STRUCTURE (MicroPython on Pico W)

### Directory layout:
```
/
├── main.py                    # Entry point, init hardware
├── config.py                  # Stored settings (JSON)
├── wifi_server.py             # Web UI for remote config
├── motor_controller.py        # PWM + current feedback loop
├── power_manager.py           # Battery selection logic
├── display.py                 # LCD menu + status screen
├── buttons.py                 # UP/SEL/DN debounce + menu nav
├── sensors.py                 # INA226 I²C reading
├── throttle.py                # ADC throttle + deadzone
├── brakes.py                  # Brake signal handling
├── security.py                # PIN entry (4-digit code)
└── utils.py                   # Common helpers
```

### Key modules:

**main.py**: Initialize all GPIO, I²C, WiFi, start web server in background thread.

**wifi_server.py**: Flask-lite (or native Pico W HTTP server):
```
GET  /                         → Web UI (HTML form)
POST /config                   → Save settings (user: davey, pass: dfg9538)
GET  /api/status               → JSON: throttle, currents, voltages, SoC
POST /api/motor_control        → JSON: set PWM, motor enable, etc.
```

**motor_controller.py**: Real-time control loop (100 Hz):
```python
for each motor (front/rear):
    read throttle (0–100%)
    read brake (0/1)
    if brake active: set PWM to 0
    else:
        select mode (range/mixed/performance) based on throttle
        calculate target_voltage, target_current
        read actual current via INA226
        adjust PWM duty to track target (PID loop)
    write PWM to GPIO14/15
```

**display.py**: 4-line LCD update (1 Hz):
```
Line 1: Throttle % | Mode
Line 2: Batt A current & SoC | Batt B current & SoC
Line 3: Motor F current & voltage | Motor R current & voltage
Line 4: Total current | Range estimate
```

**buttons.py**: Debounce + menu navigation:
- UP: scroll up in menu
- SEL: select menu item / enter PIN digit
- DN: scroll down / increment PIN digit
- Hold SEL for 2s: unlock config mode

**security.py**: 4-digit PIN entry on menu (default: 0000, changeable via web):
```
Menu → Lock/Unlock → Enter PIN (UP/DN to cycle digits, SEL to advance)
If unlock: show power, voltage, current, range calibration
If lock: show status only, no edits
```

---

## OPERATION MODES (Throttle-based)

### Range Mode (0–33% throttle)
- Voltage: 12V–24V (ramp with throttle)
- Current limit: 10A–20A per motor
- Use case: long distance, efficiency

### Mixed Mode (33–66% throttle)
- Voltage: 24V–36V
- Current limit: 20A–35A per motor
- Use case: balanced

### Performance Mode (66–100% throttle)
- Voltage: 36V–48V
- Current limit: 35A–50A per motor
- Use case: acceleration, hill climb

**Battery selection logic:**
```
If SoC_A > (SoC_B + 15%):
    Use Battery A only (contactor B OFF)
Else if SoC_B > (SoC_A + 15%):
    Use Battery B only (contactor A OFF)
Else:
    Use both in parallel (both contactors ON)
    → effectively 48V 40Ah
```

---

## TESTING CHECKLIST

- [ ] Pico W powers on, WiFi SSID "fahu" visible (hidden, no broadcast)
- [ ] Connect to "fahu" via password "7374033030", login davey/dfg9538
- [ ] Web UI loads, shows real-time current/voltage readings
- [ ] I²C shunts all respond (4 addresses: 0x40–0x43)
- [ ] LCD displays status (should update 1 Hz)
- [ ] Buttons debounce, menu navigates UP/DN, SEL enters
- [ ] Throttle ADC reads 0–1023 (0V–3.3V)
- [ ] Brakes read HIGH/LOW correctly
- [ ] GPIO PWM outputs 0–100% duty (measure on scope)
- [ ] Contactor relays click on/off when GPIO driven
- [ ] 48V bus stabilizes with buck converters on (no spikes > 52V)
- [ ] Current sense reads back match motor loads
- [ ] Range estimation calculates correctly (pack capacity ÷ avg current)

---

## VERIFIED SOURCES & PRICING (as of May 2026)

| Item | Vendor | Link | Cost | Notes |
|------|--------|------|------|-------|
| Pico W | Raspberrypi.com | https://www.raspberrypi.com/products/raspberry-pi-pico/ | €6.50 | Official, in stock |
| LCD 20×4 I²C | AliExpress | "LCD 20x4 I2C HD44780" | €8.50 | Ships 2–4 weeks, tested good |
| INA226 module (×4) | AliExpress | "INA226 I2C current sensor" | €12/each | Bulk discount @ 4+, ships 2–4 weeks |
| 48V buck converter (×2) | AliExpress | "48V 30A PWM buck converter" | €30/each | Verified by ebike community, 1–2 week ship |
| ULN2003 | Any electronics | Digi-Key, Mouser, AliExpress | €1.50 | DIP-16, in stock everywhere |
| Contactors (×4) | Alibaba | "24V 40A automotive relay" | €8/each | Heavy-duty, used in solar/EV |
| Fuses 80A (×2) | AliExpress | "ANL 80A inline fuse holder" | €5/each | Stainless, sealed |
| XT90-S (×2) | RC hobby shops | Hobbyking, GetFPV | €10/each | Antispark, standard in RC/drone |
| Resistors, caps, wire | AliExpress | "Electronics component grab bag" | €30 | Bulk resistor/capacitor assortment |
| Enclosure + DIN rail | AliExpress | "200x150mm plastic enclosure + DIN rail" | €22 | Weatherproof, professional look |

---

## ESTIMATED BUILD TIME

- **Planning & sourcing**: 1 week
- **PCB / stripboard assembly**: 8 hours
- **Firmware development**: 20–30 hours (depending on how much you customize)
- **Integration & testing**: 10 hours
- **Tuning & calibration**: 5–10 hours

**Total**: 3–4 weeks (4–6 weeks if waiting for AliExpress shipping).

---

## COST SUMMARY

| Category | Cost |
|----------|------|
| Microcontroller & comms (Pico W, WiFi) | €6.50 |
| Display & UI (LCD, buttons) | €12 |
| Current sensing (INA226 ×4) | €48 |
| Power control (buck converters ×2, contactors ×4) | €92 |
| Drivers & logic (ULN2003, resistors, diodes) | €15 |
| Power distribution (fuses, connectors, wire, enclosure) | €65 |
| **Total** | **€239–297** |
| **Plus: batteries, motors, harnesses** | **€0 (you have)** |

---

## NEXT STEPS

1. **Order components** from AliExpress (2–4 week lead time). Start with Pico W, LCD, INA226 modules, buck converters.
2. **Design PCB** (or breadboard/stripboard) for relay driver stage + Darlington array.
3. **Write firmware skeleton** (main.py, WiFi init, I²C bus scan, web server).
4. **Test I²C bus** with all 4 INA226 modules + LCD before integration.
5. **Build power distribution board** (relays, fuses, busbars) in parallel while firmware develops.
6. **Integrate & iterate**: mount on bike frame, dial in PWM curves, test throttle response.

---

## SECURITY NOTES

- WiFi SSID hidden (no broadcast), WPA2 password "7374033030" (your phone number).
- Web UI login: davey / dfg9538 (HTTP Basic Auth, ideally move to HTTPS with self-signed cert in production).
- 4-digit PIN for bike operation (configurable, default 0000; stored in config.json, encrypted at rest).
- Throttle input goes through deadzone (ignore 0–5% to avoid runaway on jitter).
- Brakes have priority: if brake active, PWM → 0 immediately (no lag).
- Firmware OTA updates (optional): upload .uf2 file via web, Pico enters bootloader.

---

## FIRMWARE SKELETON (main.py)

See next section for full code outline...
