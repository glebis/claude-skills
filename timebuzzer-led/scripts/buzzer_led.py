#!/usr/bin/env python3
"""timeBuzzer LED CLI — set color, effects, signals.

Requires: python-rtmidi (pip install python-rtmidi)

The timeBuzzer has 3 LED segments (0, 1, 2) each with independent RGB.
Protocol: MIDI CC on channel 12, CC numbers 70-78.
  Segment 0: CC 70=R, 71=G, 72=B
  Segment 1: CC 73=R, 74=G, 75=B
  Segment 2: CC 76=R, 77=G, 78=B
Values: 0-127 (input RGB 0-255 divided by 2).
"""
import argparse
import math
import sys
import time

COLORS = {
    "red":     (255, 0,   0),
    "orange":  (255, 127, 0),
    "yellow":  (255, 255, 0),
    "green":   (0,   255, 0),
    "cyan":    (0,   200, 255),
    "blue":    (0,   0,   255),
    "purple":  (127, 0,   255),
    "magenta": (255, 0,   200),
    "pink":    (255, 80,  120),
    "white":   (255, 255, 255),
    "warm":    (255, 180, 60),
    "off":     (0,   0,   0),
}

SIGNALS = {
    "success":  ("green",  "solid"),
    "done":     ("green",  "solid"),
    "error":    ("red",    "strobe"),
    "warning":  ("orange", "pulse"),
    "thinking": ("blue",   "pulse"),
    "working":  ("cyan",   "pulse"),
    "idle":     ("warm",   "solid"),
    "attention":("magenta","strobe"),
    "focus":    ("purple", "solid"),
}


class BuzzerLED:
    MIDI_CC_CH12 = 187

    def __init__(self):
        try:
            import rtmidi
        except ImportError:
            sys.exit("python-rtmidi required: pip install python-rtmidi")

        self.mo = rtmidi.MidiOut()
        port = None
        for i, name in enumerate(self.mo.get_ports()):
            if "timeBuzzer" in name:
                port = i
                break
        if port is None:
            sys.exit("timeBuzzer MIDI port not found. Is the device connected?")
        self.mo.open_port(port)

    def close(self):
        self.mo.close_port()

    def set_segment(self, seg, r, g, b):
        cc_base = 70 + 3 * seg
        self.mo.send_message([self.MIDI_CC_CH12, cc_base,     r // 2])
        time.sleep(0.002)
        self.mo.send_message([self.MIDI_CC_CH12, cc_base + 1, g // 2])
        time.sleep(0.002)
        self.mo.send_message([self.MIDI_CC_CH12, cc_base + 2, b // 2])
        time.sleep(0.002)

    def set_all(self, r, g, b):
        for seg in range(3):
            self.set_segment(seg, r, g, b)
            time.sleep(0.1)

    def set_hex(self, hexcolor):
        h = hexcolor.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        self.set_all(r, g, b)

    def pulse(self, r, g, b, bpm=30, seconds=5):
        period = 60.0 / bpm
        end = time.time() + seconds
        while time.time() < end:
            t = time.time()
            phase = (t % period) / period
            brightness = 0.2 + 0.8 * (0.5 + 0.5 * math.sin(2 * math.pi * phase))
            self.set_all(int(r * brightness), int(g * brightness), int(b * brightness))
            time.sleep(0.05)

    def strobe(self, r, g, b, count=5, interval=0.15):
        for _ in range(count):
            self.set_all(r, g, b)
            time.sleep(interval)
            self.set_all(0, 0, 0)
            time.sleep(interval)

    def rainbow(self, seconds=5):
        end = time.time() + seconds
        while time.time() < end:
            t = time.time()
            hue = (t * 60) % 360
            r, g, b = hsv_to_rgb(hue, 1.0, 1.0)
            self.set_all(r, g, b)
            time.sleep(0.05)

    def fade(self, r, g, b, seconds=2):
        steps = int(seconds / 0.05)
        for i in range(steps + 1):
            frac = i / max(steps, 1)
            self.set_all(int(r * frac), int(g * frac), int(b * frac))
            time.sleep(0.05)


def hsv_to_rgb(h, s, v):
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:    r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else:         r, g, b = c, 0, x
    return int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)


# ── commands ──────────────────────────────────────────────────────────────

def cmd_color(args):
    led = BuzzerLED()
    if args.hex:
        led.set_hex(args.hex)
    elif args.name:
        if args.name not in COLORS:
            sys.exit(f"Unknown color '{args.name}'. Known: {', '.join(sorted(COLORS))}")
        r, g, b = COLORS[args.name]
        led.set_all(r, g, b)
    led.close()


def cmd_rgb(args):
    led = BuzzerLED()
    led.set_all(args.r, args.g, args.b)
    led.close()


def cmd_off(args):
    led = BuzzerLED()
    led.set_all(0, 0, 0)
    led.close()


def cmd_signal(args):
    if args.name not in SIGNALS:
        sys.exit(f"Unknown signal. Known: {', '.join(sorted(SIGNALS))}")
    color_name, effect = SIGNALS[args.name]
    r, g, b = COLORS[color_name]
    led = BuzzerLED()
    if effect == "solid":
        led.set_all(r, g, b)
    elif effect == "pulse":
        led.pulse(r, g, b, bpm=30, seconds=args.seconds)
        led.set_all(r, g, b)
    elif effect == "strobe":
        led.strobe(r, g, b, count=5)
        led.set_all(r, g, b)
    led.close()


def cmd_pulse(args):
    r, g, b = COLORS.get(args.color, COLORS["blue"])
    led = BuzzerLED()
    led.pulse(r, g, b, bpm=args.bpm, seconds=args.seconds)
    led.set_all(r, g, b)
    led.close()


def cmd_strobe(args):
    r, g, b = COLORS.get(args.color, COLORS["white"])
    led = BuzzerLED()
    led.strobe(r, g, b, count=args.count, interval=args.interval)
    led.close()


def cmd_rainbow(args):
    led = BuzzerLED()
    led.rainbow(seconds=args.seconds)
    led.set_all(0, 0, 0)
    led.close()


def cmd_fade(args):
    r, g, b = COLORS.get(args.color, COLORS["white"])
    led = BuzzerLED()
    led.fade(r, g, b, seconds=args.seconds)
    led.close()


def cmd_segment(args):
    led = BuzzerLED()
    led.set_segment(args.seg, args.r, args.g, args.b)
    led.close()


# ── argparse ──────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(description="timeBuzzer LED control via MIDI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("color", help="Set named color or hex")
    sp.add_argument("name", nargs="?", help=f"One of: {', '.join(sorted(COLORS))}")
    sp.add_argument("--hex", help="Hex color e.g. #FF8800")
    sp.set_defaults(func=cmd_color)

    sp = sub.add_parser("rgb", help="Set raw RGB (0-255)")
    sp.add_argument("r", type=int)
    sp.add_argument("g", type=int)
    sp.add_argument("b", type=int)
    sp.set_defaults(func=cmd_rgb)

    sp = sub.add_parser("off", help="Turn LED off")
    sp.set_defaults(func=cmd_off)

    sp = sub.add_parser("signal", help=f"Status signal: {', '.join(sorted(SIGNALS))}")
    sp.add_argument("name")
    sp.add_argument("--seconds", type=float, default=3.0)
    sp.set_defaults(func=cmd_signal)

    sp = sub.add_parser("pulse", help="Breathing pulse")
    sp.add_argument("color", nargs="?", default="blue")
    sp.add_argument("--bpm", type=float, default=30)
    sp.add_argument("--seconds", type=float, default=5)
    sp.set_defaults(func=cmd_pulse)

    sp = sub.add_parser("strobe", help="Flash on/off")
    sp.add_argument("color", nargs="?", default="white")
    sp.add_argument("--count", type=int, default=5)
    sp.add_argument("--interval", type=float, default=0.15)
    sp.set_defaults(func=cmd_strobe)

    sp = sub.add_parser("rainbow", help="Rainbow cycle")
    sp.add_argument("--seconds", type=float, default=5)
    sp.set_defaults(func=cmd_rainbow)

    sp = sub.add_parser("fade", help="Fade in from black")
    sp.add_argument("color", nargs="?", default="white")
    sp.add_argument("--seconds", type=float, default=2)
    sp.set_defaults(func=cmd_fade)

    sp = sub.add_parser("segment", help="Set single segment (0-2) RGB")
    sp.add_argument("seg", type=int, choices=[0, 1, 2])
    sp.add_argument("r", type=int)
    sp.add_argument("g", type=int)
    sp.add_argument("b", type=int)
    sp.set_defaults(func=cmd_segment)

    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
