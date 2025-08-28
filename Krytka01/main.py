# main.py – Japysoft Pico Servo Controller + LED (robust + better stdin)
# kod pre pico h
# Príkazy:
#  OPEN / CLOSE / STATE / PING / ECHO <text> / ADMINCHECK
#  GET_US
#  SET_US <min_us> <max_us> [SAVE]
#  JOG +N | JOG -N
#  MOVE_US <us>          # priamy test (napr. 1500)
#  SAVE / LOAD

import sys, time, machine, os, gc

# ===== KONFIG =====
SERVO_PIN = 15
FREQ = 50
LED_PULSE_MS = 30
CFG_FILE = "servo_cfg.json"

# Bezpečná východzia kalibrácia (doladíš podľa mechaniky)
US_CLOSE = 1100
US_OPEN  = 1900

# ===== LED =====
try:
    led = machine.Pin("LED", machine.Pin.OUT)
    led.value(1)  # zapni po štarte
except Exception:
    led = None

def pulse_led(ms=LED_PULSE_MS):
    if not led: return
    try:
        led.value(0); time.sleep_ms(ms); led.value(1)
    except Exception:
        pass

# ===== Pomocné =====
def _duty_from_us(us, freq=FREQ):
    return int(us * freq * 65535 // 1_000_000)

def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def _limits_ok(us_min, us_max):
    return (500 <= us_min < us_max <= 2500)

def println(msg):
    try:
        sys.stdout.write(str(msg) + "\n")
        sys.stdout.flush()
    except Exception:
        pass

# ===== Konfigurácia (flash) =====
def cfg_load():
    global US_CLOSE, US_OPEN
    try:
        import ujson
        with open(CFG_FILE, "r") as f:
            d = ujson.load(f)
        us_min = int(d.get("US_CLOSE", US_CLOSE))
        us_max = int(d.get("US_OPEN",  US_OPEN))
        if _limits_ok(us_min, us_max):
            US_CLOSE, US_OPEN = us_min, us_max
            return True
    except Exception:
        pass
    return False

def cfg_save():
    try:
        import ujson
        with open(CFG_FILE, "w") as f:
            ujson.dump({"US_CLOSE": US_CLOSE, "US_OPEN": US_OPEN}, f)
        return True
    except Exception:
        return False

cfg_load()

# ===== Servo init =====
servo = None
servo_available = False
servo_init_error = None
last_state = 0  # 0=CLOSE, 1=OPEN

try:
    pwm = machine.PWM(machine.Pin(SERVO_PIN))
    pwm.freq(FREQ)
    pwm.duty_u16(_duty_from_us(US_CLOSE))
    servo = pwm
    servo_available = True
    last_state = 0
except Exception as e:
    servo = None
    servo_available = False
    servo_init_error = repr(e)

def set_servo_us(us):
    if not servo_available or servo is None:
        println("call japysoft"); return False
    try:
        us = _clamp(int(us), 500, 2500)
        servo.duty_u16(_duty_from_us(us))
        return True
    except Exception as e:
        println("ERR:SERVO " + repr(e)); return False

def set_servo(position):
    global last_state
    if not servo_available or servo is None:
        println("call japysoft"); return
    try:
        if position == "OPEN":
            if set_servo_us(US_OPEN):
                last_state = 1; println("OK")
        elif position == "CLOSE":
            if set_servo_us(US_CLOSE):
                last_state = 0; println("OK")
        time.sleep_ms(250)
    except Exception as e:
        println("ERR:SERVO " + repr(e))

# ===== Diagnostika =====
def admin_check():
    L = []
    try:
        L.append("manufacturer: Japysoft")
        L.append("product: Brain of Japysoft Telescope Cover")
        L.append("servo_available: {}".format(servo_available))
        if not servo_available and servo_init_error:
            L.append("servo_error: {}".format(servo_init_error))
        L.append("last_state: {}".format(last_state))
        L.append("servo_freq: {}".format(FREQ if servo_available else "N/A"))
        try: L.append("cpu_freq: {}".format(machine.freq()))
        except Exception as e: L.append("cpu_freq: ERR {}".format(repr(e)))
        try: L.append("mem_free: {}".format(gc.mem_free()))
        except Exception as e: L.append("mem_free: ERR {}".format(repr(e)))
        try:
            u = os.uname(); L.append("platform: {}".format(u.sysname)); L.append("version: {}".format(u.release))
        except Exception as e: L.append("uname: ERR {}".format(repr(e)))
        try:
            uid = machine.unique_id()
            if isinstance(uid, (bytes, bytearray)): uid = uid.hex()
            L.append("unique_id: {}".format(uid))
        except Exception as e: L.append("unique_id: ERR {}".format(repr(e)))
        L.append("US_CLOSE: {}".format(US_CLOSE))
        L.append("US_OPEN: {}".format(US_OPEN))
        L.append("led_present: {}".format(bool(led)))
    except Exception as e:
        L.append("ADMINCHECK ERROR: " + repr(e))
    for line in L:
        println(line)

# ===== Neblokujúci reader s perzistentným bufferom =====
_inbuf = ""

try:
    import uselect
    _poll = uselect.poll()
    _poll.register(sys.stdin, uselect.POLLIN)
    _HAVE_POLL = True
except Exception:
    _HAVE_POLL = False

def _read_one_char_nonblock():
    # Skús prečítať 1 znak; ak nič, vráť None bez blokovania
    try:
        ch = sys.stdin.read(1)
        if not ch:
            return None
        if isinstance(ch, bytes):
            try: ch = ch.decode()
            except Exception: return None
        return ch
    except Exception:
        return None

def read_available(timeout_ms=100):
    global _inbuf
    # Čakaj na „niečo“ na vstupe, ale blokuj max timeout_ms
    end = time.ticks_add(time.ticks_ms(), timeout_ms)
    got_any = False

    while True:
        # Skonči, ak uplynul timeout
        if time.ticks_diff(end, time.ticks_ms()) <= 0:
            break
        # Ak máme poll, čakaj krátko na event
        if _HAVE_POLL:
            ev = _poll.poll(0)
            if not ev:
                time.sleep_ms(5); continue
        # Prečítaj, čo je – po 1 znaku, s krátkym „oknom“
        ch = _read_one_char_nonblock()
        if ch is None:
            # nič neprišlo, krátko počkaj a skús znova
            time.sleep_ms(2)
            continue
        got_any = True
        _inbuf += ch
        # Keď dorazí \n alebo \r, vráť riadok
        if ("\n" in _inbuf) or ("\r" in _inbuf):
            # nájdi prvý koniec riadku (\r\n, \n, \r – čokoľvek prvé)
            idx_n = _inbuf.find("\n"); idx_r = _inbuf.find("\r")
            cut = -1
            if idx_n == -1: cut = idx_r
            elif idx_r == -1: cut = idx_n
            else: cut = min(idx_n, idx_r)
            line = _inbuf[:cut].strip()
            _inbuf = _inbuf[cut+1:]
            return line if line else None

    # Ak sme niečo nabrali, ale bez newline – čakaj na ďalšie kolo
    return None

# ===== Handler =====
def handle(cmd):
    global US_CLOSE, US_OPEN
    c = cmd.strip()
    if not c: return
    C = c.upper()

    pulse_led()

    # rýchle
    if C == "PING": println("PONG"); return
    if C.startswith("ECHO "): println(c[5:]); return

    # diagnostika
    if C == "ADMINCHECK": admin_check(); return
    if C == "STATE":
        if not servo_available or servo is None: println("call japysoft")
        else: println("1" if last_state else "0")
        return

    # kalibrácia
    if C == "GET_US":
        println("US_CLOSE={} US_OPEN={}".format(US_CLOSE, US_OPEN)); return

    if C.startswith("SET_US"):
        parts = c.split()
        if len(parts) < 3:
            println("ERR:SET_US usage: SET_US <min_us> <max_us> [SAVE]"); return
        try:
            us_min = int(parts[1]); us_max = int(parts[2])
        except Exception:
            println("ERR:SET_US not integers"); return
        if not _limits_ok(us_min, us_max):
            println("ERR:SET_US limits (500..2500) and min<max"); return
        US_CLOSE, US_OPEN = us_min, us_max
        println("OK SET_US US_CLOSE={} US_OPEN={}".format(US_CLOSE, US_OPEN))
        if len(parts) >= 4 and parts[3].upper() == "SAVE":
            println("OK SAVED" if cfg_save() else "ERR:SAVE_FAILED")
        return

    if C.startswith("JOG"):
        parts = c.split()
        if len(parts) < 2:
            println("ERR:JOG usage: JOG +N | JOG -N"); return
        s = parts[1].strip(); sign = 1
        if s.startswith("+"): s = s[1:]; sign = 1
        elif s.startswith("-"): s = s[1:]; sign = -1
        try: val = int(s) * sign
        except Exception: println("ERR:JOG not integer"); return
        if last_state == 1:
            US_OPEN = _clamp(US_OPEN + val, 500, 2500)
            println("OK JOG OPEN -> {}us".format(US_OPEN)); set_servo("OPEN")
        else:
            US_CLOSE = _clamp(US_CLOSE + val, 500, 2500)
            println("OK JOG CLOSE -> {}us".format(US_CLOSE)); set_servo("CLOSE")
        return

    if C.startswith("MOVE_US"):
        parts = c.split()
        if len(parts) != 2:
            println("ERR:MOVE_US usage: MOVE_US <us>"); return
        try: us = int(parts[1])
        except Exception: println("ERR:MOVE_US not integer"); return
        if set_servo_us(us): println("OK MOVE_US {}".format(us))
        return

    if C == "SAVE": println("OK SAVED" if cfg_save() else "ERR:SAVE_FAILED"); return
    if C == "LOAD":
        if cfg_load():
            println("OK LOADED US_CLOSE={} US_OPEN={}".format(US_CLOSE, US_OPEN))
            set_servo("OPEN" if last_state else "CLOSE")
        else:
            println("ERR:LOAD_FAILED")
        return

    # pohyb
    if C == "OPEN": set_servo("OPEN"); return
    if C == "CLOSE": set_servo("CLOSE"); return

    println("ERR:UNKNOWN:" + c)

# ===== Štart =====
println("READY Japysoft Telescope Cover v1")
if not servo_available and servo_init_error:
    println("NOTE: servo not available: " + servo_init_error)
else:
    println("US_CLOSE={} US_OPEN={}".format(US_CLOSE, US_OPEN))

def main_loop():
    while True:
        line = read_available(120)
        if line is None:
            time.sleep_ms(5); continue
        handle(line)

if __name__ == "__main__":
    main_loop()
