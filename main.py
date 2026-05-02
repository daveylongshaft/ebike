# eBike Controller Firmware - Raspberry Pi Pico W
# MicroPython main.py skeleton

import machine
import time
import json
import uasyncio as asyncio
from machine import Pin, PWM, ADC, I2C, UART
import ubinascii
import network
from microdot import Microdot, Request, Response

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "wifi_ssid": "fahu",
    "wifi_password": "7374033030",
    "web_user": "davey",
    "web_pass": "dfg9538",
    "pin_code": "0000",
    "mode": "range",  # range, mixed, performance
    "voltage_range": {"range": [12, 24], "mixed": [24, 36], "performance": [36, 48]},
    "current_limit": {"range": [10, 20], "mixed": [20, 35], "performance": [35, 50]},
    "throttle_deadzone": 0.05,
    "battery_balance_threshold": 15,  # Switch single battery if SoC diff > 15%
}

# ═══════════════════════════════════════════════════════════════
# GPIO PINOUT
# ═══════════════════════════════════════════════════════════════

# Relay Control (GPIO output → Darlington driver)
PIN_BATT_A_CTRL = Pin(2, Pin.OUT)   # GP2 → Battery A contactor
PIN_BATT_B_CTRL = Pin(3, Pin.OUT)   # GP3 → Battery B contactor
PIN_MOTOR_F_CTRL = Pin(4, Pin.OUT)  # GP4 → Motor Front contactor
PIN_MOTOR_R_CTRL = Pin(5, Pin.OUT)  # GP5 → Motor Rear contactor

# PWM Motor Control (GPIO PWM, 1 kHz)
PIN_MOTOR_F_PWM = machine.PWM(Pin(14))  # GP14 → Motor Front PWM
PIN_MOTOR_R_PWM = machine.PWM(Pin(15))  # GP15 → Motor Rear PWM
PIN_MOTOR_F_PWM.freq(1000)
PIN_MOTOR_R_PWM.freq(1000)

# Button inputs (GPIO input, active low with pull-up)
PIN_BTN_UP = Pin(6, Pin.IN, Pin.PULL_UP)    # GP6
PIN_BTN_SEL = Pin(7, Pin.IN, Pin.PULL_UP)   # GP7
PIN_BTN_DN = Pin(8, Pin.IN, Pin.PULL_UP)    # GP8

# Brake inputs (GPIO input, pull-up)
PIN_BRAKE_F = Pin(9, Pin.IN, Pin.PULL_UP)   # GP9
PIN_BRAKE_R = Pin(10, Pin.IN, Pin.PULL_UP)  # GP10

# Signal outputs (to relay drivers)
PIN_TURN_L = Pin(11, Pin.OUT)       # GP11 → Left turn signal
PIN_TURN_R = Pin(12, Pin.OUT)       # GP12 → Right turn signal
PIN_BRAKE_LIGHT = Pin(13, Pin.OUT)  # GP13 → Brake lights

# Throttle input (ADC)
ADC_THROTTLE = ADC(Pin(26, mode=Pin.IN))  # GP26 (ADC0)

# I²C (SDA=GP0, SCL=GP1)
I2C_BUS = I2C(0, scl=Pin(1), sda=Pin(0), freq=400_000)

# UART (optional debug, GP16/GP17)
UART_DEBUG = UART(0, baudrate=115200)

# ═══════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════

class SystemState:
    def __init__(self):
        self.throttle = 0.0       # 0–1.0
        self.mode = "range"       # range, mixed, performance
        self.brake_f = False
        self.brake_r = False
        self.batt_a_current = 0.0
        self.batt_b_current = 0.0
        self.motor_f_current = 0.0
        self.motor_r_current = 0.0
        self.batt_a_voltage = 48.0
        self.batt_b_voltage = 48.0
        self.motor_f_voltage = 0.0
        self.motor_r_voltage = 0.0
        self.batt_a_soc = 100.0   # %
        self.batt_b_soc = 100.0   # %
        self.range_km = 0.0
        self.pwm_f = 0
        self.pwm_r = 0
        self.motor_f_enabled = False
        self.motor_r_enabled = False
        self.batt_a_enabled = False
        self.batt_b_enabled = False
        self.lock_code = "0000"
        self.unlocked = False

state = SystemState()
config = {}

# ═══════════════════════════════════════════════════════════════
# HARDWARE INIT
# ═══════════════════════════════════════════════════════════════

def init_hardware():
    """Initialize all GPIO, I²C, ADC, etc."""
    print("[INIT] Hardware initialization...")

    # Start I²C bus scan
    i2c_devices = I2C_BUS.scan()
    print(f"[I2C] Devices found: {[hex(d) for d in i2c_devices]}")

    # Initialize INA226 modules (addresses 0x40–0x43)
    # (Full init code in sensors.py)

    # Set relay outputs LOW (inactive)
    PIN_BATT_A_CTRL.off()
    PIN_BATT_B_CTRL.off()
    PIN_MOTOR_F_CTRL.off()
    PIN_MOTOR_R_CTRL.off()

    # Signal lights off
    PIN_TURN_L.off()
    PIN_TURN_R.off()
    PIN_BRAKE_LIGHT.off()

    print("[INIT] Hardware ready.")

# ═══════════════════════════════════════════════════════════════
# CONFIG MANAGEMENT
# ═══════════════════════════════════════════════════════════════

def load_config():
    """Load config from JSON file, or use defaults."""
    global config
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        print(f"[CONFIG] Loaded from {CONFIG_FILE}")
    except OSError:
        config = DEFAULT_CONFIG.copy()
        save_config()
        print(f"[CONFIG] Created default config at {CONFIG_FILE}")

def save_config():
    """Save config to JSON file."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        print("[CONFIG] Saved.")
    except Exception as e:
        print(f"[CONFIG] Save failed: {e}")

# ═══════════════════════════════════════════════════════════════
# SENSOR READING (I²C INA226 current sense)
# ═══════════════════════════════════════════════════════════════

class INA226:
    """I²C current sense module reader."""
    def __init__(self, i2c, address, shunt_ohms=0.1):
        self.i2c = i2c
        self.addr = address
        self.shunt_ohms = shunt_ohms
        self.current_lsb = 0.001  # 1 mA per LSB (typical)

    def read_current_ma(self):
        """Read current in mA from INA226."""
        try:
            # Register 0x01: Current register (16-bit signed)
            data = self.i2c.readfrom_mem(self.addr, 0x01, 2)
            current_raw = (data[0] << 8) | data[1]
            if current_raw & 0x8000:  # Sign extend if negative
                current_raw -= 65536
            current_ma = current_raw * self.current_lsb
            return current_ma
        except Exception as e:
            print(f"[INA226] Read error at 0x{self.addr:02x}: {e}")
            return 0.0

    def read_voltage_v(self):
        """Read bus voltage in V from INA226."""
        try:
            # Register 0x02: Bus voltage register (16-bit, 1.25mV per LSB)
            data = self.i2c.readfrom_mem(self.addr, 0x02, 2)
            voltage_raw = (data[0] << 8) | data[1]
            voltage_v = (voltage_raw >> 3) * 0.00125  # Shift right 3 bits, multiply by LSB
            return voltage_v
        except Exception as e:
            print(f"[INA226] Read error at 0x{self.addr:02x}: {e}")
            return 0.0

# Initialize INA226 instances
ina_batt_a = INA226(I2C_BUS, 0x40)
ina_batt_b = INA226(I2C_BUS, 0x41)
ina_motor_f = INA226(I2C_BUS, 0x42)
ina_motor_r = INA226(I2C_BUS, 0x43)

def read_sensors():
    """Read all sensor values and update state."""
    # Throttle (0–3.3V → 0–100%)
    throttle_raw = ADC_THROTTLE.read_u16() / 65535.0  # 0–1.0
    deadzone = config.get("throttle_deadzone", 0.05)
    if throttle_raw < deadzone:
        state.throttle = 0.0
    else:
        state.throttle = min(1.0, (throttle_raw - deadzone) / (1.0 - deadzone))

    # Brakes (active low)
    state.brake_f = not PIN_BRAKE_F.value()
    state.brake_r = not PIN_BRAKE_R.value()

    # Currents (INA226 modules)
    state.batt_a_current = ina_batt_a.read_current_ma() / 1000.0  # mA → A
    state.batt_b_current = ina_batt_b.read_current_ma() / 1000.0
    state.motor_f_current = ina_motor_f.read_current_ma() / 1000.0
    state.motor_r_current = ina_motor_r.read_current_ma() / 1000.0

    # Voltages (INA226 modules)
    state.batt_a_voltage = ina_batt_a.read_voltage_v()
    state.batt_b_voltage = ina_batt_b.read_voltage_v()
    state.motor_f_voltage = ina_motor_f.read_voltage_v()
    state.motor_r_voltage = ina_motor_r.read_voltage_v()

    # SoC estimation (simple: voltage-based)
    # 48V pack: 42V = 0%, 54V = 100% (typical LiPo/LiFePO4)
    state.batt_a_soc = max(0, min(100, (state.batt_a_voltage - 42.0) / (54.0 - 42.0) * 100))
    state.batt_b_soc = max(0, min(100, (state.batt_b_voltage - 42.0) / (54.0 - 42.0) * 100))

    # Range estimation
    total_current = state.motor_f_current + state.motor_r_current
    if total_current > 1.0:  # Avoid division by zero
        avg_current = total_current
        batt_capacity = 20.0  # Ah (20Ah pack)
        remaining_ah = batt_capacity * state.batt_a_soc / 100.0  # Crude estimate
        state.range_km = remaining_ah / avg_current * 5  # Assume 5 km/Ah (tune based on field data)
    else:
        state.range_km = 0.0

# ═══════════════════════════════════════════════════════════════
# MOTOR CONTROL & PWM
# ═══════════════════════════════════════════════════════════════

def update_motor_control():
    """Real-time motor control loop (call 100 Hz)."""
    # Brake priority: if brake active, kill PWM
    if state.brake_f or state.brake_r:
        PIN_MOTOR_F_PWM.duty_u16(0)
        PIN_MOTOR_R_PWM.duty_u16(0)
        PIN_BRAKE_LIGHT.on()
        return
    else:
        PIN_BRAKE_LIGHT.off()

    # Determine mode (range, mixed, performance)
    if state.throttle < 0.33:
        state.mode = "range"
        v_min, v_max = config["voltage_range"]["range"]
        i_min, i_max = config["current_limit"]["range"]
    elif state.throttle < 0.66:
        state.mode = "mixed"
        v_min, v_max = config["voltage_range"]["mixed"]
        i_min, i_max = config["current_limit"]["mixed"]
    else:
        state.mode = "performance"
        v_min, v_max = config["voltage_range"]["performance"]
        i_min, i_max = config["current_limit"]["performance"]

    # Calculate target voltage (linear ramp within mode)
    mode_throttle = (state.throttle % 0.33) / 0.33  # 0–1 within mode
    target_voltage = v_min + (v_max - v_min) * mode_throttle

    # Convert voltage to PWM duty (0–48V → 0–100% duty)
    pwm_duty = target_voltage / 48.0

    # PWM to 16-bit value (0–65535)
    pwm_value = int(pwm_duty * 65535)
    pwm_value = max(0, min(65535, pwm_value))

    # Apply to motors (both equal for now; future: stagger front/rear)
    PIN_MOTOR_F_PWM.duty_u16(pwm_value)
    PIN_MOTOR_R_PWM.duty_u16(pwm_value)
    state.pwm_f = pwm_duty
    state.pwm_r = pwm_duty

    # TODO: Current limiting feedback loop (compare actual vs. target)
    # If current exceeds limit, reduce PWM duty

# ═══════════════════════════════════════════════════════════════
# BATTERY SELECTION
# ═══════════════════════════════════════════════════════════════

def update_battery_selection():
    """Switch batteries based on SoC balance."""
    threshold = config.get("battery_balance_threshold", 15)

    if state.batt_a_soc > (state.batt_b_soc + threshold):
        # Battery A has more charge, use it
        state.batt_a_enabled = True
        state.batt_b_enabled = False
    elif state.batt_b_soc > (state.batt_a_soc + threshold):
        # Battery B has more charge, use it
        state.batt_a_enabled = False
        state.batt_b_enabled = True
    else:
        # SoC balanced, use both in parallel
        state.batt_a_enabled = True
        state.batt_b_enabled = True

    # Drive relay outputs
    PIN_BATT_A_CTRL.value(1 if state.batt_a_enabled else 0)
    PIN_BATT_B_CTRL.value(1 if state.batt_b_enabled else 0)

# ═══════════════════════════════════════════════════════════════
# BUTTON & MENU HANDLING
# ═══════════════════════════════════════════════════════════════

class MenuState:
    def __init__(self):
        self.menu_index = 0
        self.pin_entry = ""
        self.pin_mode = False
        self.last_btn_time = 0
        self.debounce_ms = 50

    def button_up(self):
        now = time.ticks_ms()
        if now - self.last_btn_time < self.debounce_ms:
            return
        self.last_btn_time = now

        if self.pin_mode:
            # Increment current digit (0–9)
            if len(self.pin_entry) < 4:
                digit = int(self.pin_entry[-1]) if self.pin_entry else 0
                digit = (digit + 1) % 10
                self.pin_entry = self.pin_entry[:-1] + str(digit)
        else:
            self.menu_index = max(0, self.menu_index - 1)

    def button_dn(self):
        now = time.ticks_ms()
        if now - self.last_btn_time < self.debounce_ms:
            return
        self.last_btn_time = now

        if self.pin_mode:
            # Decrement current digit (0–9)
            if len(self.pin_entry) < 4:
                digit = int(self.pin_entry[-1]) if self.pin_entry else 0
                digit = (digit - 1) % 10
                self.pin_entry = self.pin_entry[:-1] + str(digit)
        else:
            self.menu_index = min(5, self.menu_index + 1)

    def button_sel(self):
        now = time.ticks_ms()
        if now - self.last_btn_time < self.debounce_ms:
            return
        self.last_btn_time = now

        if self.pin_mode:
            if len(self.pin_entry) < 4:
                self.pin_entry += "0"
            else:
                # Check PIN
                if self.pin_entry == config.get("pin_code", "0000"):
                    state.unlocked = True
                    self.pin_mode = False
                else:
                    self.pin_entry = ""
        else:
            # Enter PIN mode
            self.pin_mode = True
            self.pin_entry = ""

menu = MenuState()

async def poll_buttons():
    """Background task: poll buttons every 50ms."""
    while True:
        if not PIN_BTN_UP.value():     # Active low
            menu.button_up()
        if not PIN_BTN_DN.value():
            menu.button_dn()
        if not PIN_BTN_SEL.value():
            menu.button_sel()
        await asyncio.sleep_ms(50)

# ═══════════════════════════════════════════════════════════════
# DISPLAY (LCD 20×4 I²C)
# ═══════════════════════════════════════════════════════════════

# TODO: Import LCD library (e.g., micropython-lcd, or bit-bang I²C commands)
# For now, placeholder:

async def update_display():
    """Background task: update LCD every 1 second."""
    while True:
        # LCD write:
        # Line 1: "Throttle: 45% | Mode: RANGE"
        # Line 2: "BattA: 23A (82%) | BattB: 10A (78%)"
        # Line 3: "MotorF: 18A 36V | MotorR: 16A 36V"
        # Line 4: "Total: 34A / 72V | Rng: 28km"

        print(
            f"Throttle: {state.throttle*100:.0f}% | Mode: {state.mode.upper()}\n"
            f"BattA: {state.batt_a_current:.1f}A ({state.batt_a_soc:.0f}%) | "
            f"BattB: {state.batt_b_current:.1f}A ({state.batt_b_soc:.0f}%)\n"
            f"MotorF: {state.motor_f_current:.1f}A {state.motor_f_voltage:.1f}V | "
            f"MotorR: {state.motor_r_current:.1f}A {state.motor_r_voltage:.1f}V\n"
            f"Total: {state.motor_f_current+state.motor_r_current:.1f}A | "
            f"Range: {state.range_km:.1f}km"
        )

        await asyncio.sleep(1)

# ═══════════════════════════════════════════════════════════════
# WEB SERVER (WiFi config + API)
# ═══════════════════════════════════════════════════════════════

app = Microdot()

def check_auth(request):
    """HTTP Basic Auth check."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Basic "):
        return False
    encoded = auth_header.split(" ")[1]
    decoded = ubinascii.a2b_base64(encoded).decode()
    user, passwd = decoded.split(":")
    expected_user = config.get("web_user", "davey")
    expected_pass = config.get("web_pass", "dfg9538")
    return user == expected_user and passwd == expected_pass

@app.route("/")
async def index(request):
    """Serve web UI (HTML form)."""
    if not check_auth(request):
        return Response(status=401, body="Unauthorized")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>eBike Controller</title>
        <style>
            body { font-family: Arial; margin: 20px; }
            .status { background: #f0f0f0; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .control { margin: 10px 0; }
            button { padding: 10px; margin: 5px; }
        </style>
    </head>
    <body>
        <h1>eBike Dual-Motor Controller</h1>

        <div class="status">
            <h3>Live Status</h3>
            <p id="status">Loading...</p>
            <button onclick="fetchStatus()">Refresh</button>
        </div>

        <div class="control">
            <h3>Motor Control</h3>
            <button onclick="toggleMotor('f')">Motor Front: OFF</button>
            <button onclick="toggleMotor('r')">Motor Rear: OFF</button>
        </div>

        <div class="control">
            <h3>Battery Control</h3>
            <button onclick="toggleBattery('a')">Battery A: OFF</button>
            <button onclick="toggleBattery('b')">Battery B: OFF</button>
        </div>

        <script>
            async function fetchStatus() {
                const resp = await fetch('/api/status');
                const data = await resp.json();
                document.getElementById('status').innerHTML = `
                    Throttle: ${(data.throttle*100).toFixed(0)}%<br>
                    Motor F: ${data.motor_f_current.toFixed(1)}A @ ${data.motor_f_voltage.toFixed(1)}V<br>
                    Motor R: ${data.motor_r_current.toFixed(1)}A @ ${data.motor_r_voltage.toFixed(1)}V<br>
                    Batt A: ${data.batt_a_current.toFixed(1)}A (${data.batt_a_soc.toFixed(0)}%)<br>
                    Batt B: ${data.batt_b_current.toFixed(1)}A (${data.batt_b_soc.toFixed(0)}%)
                `;
            }

            async function toggleMotor(m) {
                await fetch('/api/motor_control', {
                    method: 'POST',
                    body: JSON.stringify({motor: m, enable: true})
                });
                fetchStatus();
            }

            async function toggleBattery(b) {
                await fetch('/api/battery_control', {
                    method: 'POST',
                    body: JSON.stringify({battery: b, enable: true})
                });
                fetchStatus();
            }

            fetchStatus();
            setInterval(fetchStatus, 1000);
        </script>
    </body>
    </html>
    """
    return Response(body=html, headers={"Content-Type": "text/html"})

@app.route("/api/status")
async def api_status(request):
    """Return JSON status."""
    if not check_auth(request):
        return Response(status=401, body="Unauthorized")

    return {
        "throttle": state.throttle,
        "mode": state.mode,
        "batt_a_current": state.batt_a_current,
        "batt_b_current": state.batt_b_current,
        "batt_a_soc": state.batt_a_soc,
        "batt_b_soc": state.batt_b_soc,
        "motor_f_current": state.motor_f_current,
        "motor_r_current": state.motor_r_current,
        "motor_f_voltage": state.motor_f_voltage,
        "motor_r_voltage": state.motor_r_voltage,
        "range_km": state.range_km,
    }

@app.route("/api/motor_control", methods=["POST"])
async def api_motor_control(request):
    """Enable/disable motors."""
    if not check_auth(request):
        return Response(status=401, body="Unauthorized")

    data = await request.json()
    motor = data.get("motor")
    enable = data.get("enable", False)

    if motor == "f":
        state.motor_f_enabled = enable
        PIN_MOTOR_F_CTRL.value(1 if enable else 0)
    elif motor == "r":
        state.motor_r_enabled = enable
        PIN_MOTOR_R_CTRL.value(1 if enable else 0)

    return {"ok": True}

# ═══════════════════════════════════════════════════════════════
# MAIN LOOP & WIFI INIT
# ═══════════════════════════════════════════════════════════════

async def main_control_loop():
    """Main 100 Hz control loop."""
    while True:
        read_sensors()
        update_battery_selection()
        update_motor_control()
        await asyncio.sleep_ms(10)  # 100 Hz

async def main():
    """Entry point."""
    print("[BOOT] eBike Controller starting...")

    init_hardware()
    load_config()

    # WiFi init
    print("[WIFI] Connecting to network...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect("fahu", "7374033030")  # SSID, password

    # Wait for connection
    max_wait = 10
    while max_wait > 0:
        status = wlan.status()
        if status < 0 or status >= 3:
            break
        max_wait -= 1
        print(f"[WIFI] Waiting ({10-max_wait}/10)...")
        await asyncio.sleep(1)

    if wlan.status() == 3:
        print(f"[WIFI] Connected! IP: {wlan.ifconfig()[0]}")
    else:
        print("[WIFI] Failed to connect.")

    # Start async tasks
    asyncio.create_task(main_control_loop())
    asyncio.create_task(poll_buttons())
    asyncio.create_task(update_display())

    # Start web server
    await app.run(host="0.0.0.0", port=80)

# ═══════════════════════════════════════════════════════════════
# BOOT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[BOOT] Interrupted.")
    except Exception as e:
        print(f"[BOOT] Error: {e}")
        import traceback
        traceback.print_exc()
