# timeBuzzer LED

Control the [timeBuzzer](https://timebuzzer.com) hardware LED via MIDI — set colors, run effects (pulse, strobe, rainbow, fade), and send semantic status signals.

## Usage

```bash
# Solid color
/timebuzzer-led color red
/timebuzzer-led color --hex "#FF8800"

# Effects
/timebuzzer-led pulse blue --bpm 30 --seconds 5
/timebuzzer-led strobe red --count 5
/timebuzzer-led rainbow --seconds 5

# Status signals
/timebuzzer-led signal success    # green solid
/timebuzzer-led signal thinking   # blue pulse
/timebuzzer-led signal error      # red strobe

# Per-segment control (3 RGB segments)
/timebuzzer-led segment 0 255 0 0
```

## Signals

| Signal | Color | Effect |
|---|---|---|
| success/done | green | solid |
| error | red | strobe |
| warning | orange | pulse |
| thinking | blue | pulse |
| working | cyan | pulse |
| idle | warm | solid |
| attention | magenta | strobe |
| focus | purple | solid |

## Requirements

- timeBuzzer device connected via USB-C
- `python-rtmidi` (`pip install python-rtmidi`)

## How it works

The timeBuzzer exposes a USB MIDI interface. The script sends MIDI CC messages on channel 12 to control 3 independent RGB LED segments (CC 70–78). Values are 0–127 (half of standard 0–255 RGB). Effects are software-driven loops on top of the same protocol.

Pairs with the [hue](../hue/) skill using the same signal vocabulary for synchronized ambient + desk feedback.
