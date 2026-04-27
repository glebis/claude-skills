---
name: timebuzzer-led
description: Control timeBuzzer hardware LED via MIDI — set color, effects (pulse, strobe, rainbow, fade), and semantic status signals. Use when the user asks to change the buzzer LED color, signal status through the buzzer, or sync the buzzer with other lighting.
---

# timeBuzzer LED

Control the timeBuzzer hardware LED over MIDI. The device has 3 RGB segments controllable independently or together.

## Requirements

- timeBuzzer device connected via USB-C
- `python-rtmidi` installed (`pip install python-rtmidi`)
- timeBuzzer app may be running (MIDI port is shared)

## Script

Single CLI: `scripts/buzzer_led.py`

### Color commands

```bash
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py color red
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py color --hex "#FF8800"
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py rgb 255 100 0
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py off
```

Named colors: red, orange, yellow, green, cyan, blue, purple, magenta, pink, white, warm, off.

### Effects

```bash
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py pulse blue --bpm 30 --seconds 5
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py strobe red --count 5 --interval 0.15
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py rainbow --seconds 5
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py fade warm --seconds 2
```

### Status signals (parallel to `hue` skill)

```bash
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py signal success
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py signal thinking --seconds 5
```

| signal | color | effect |
|---|---|---|
| success/done | green | solid |
| error | red | strobe |
| warning | orange | pulse |
| thinking | blue | pulse |
| working | cyan | pulse |
| idle | warm | solid |
| attention | magenta | strobe |
| focus | purple | solid |

### Per-segment control

```bash
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py segment 0 255 0 0   # seg 0 red
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py segment 1 0 255 0   # seg 1 green
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py segment 2 0 0 255   # seg 2 blue
```

## Protocol details

- USB MIDI device (vendor 0x16D0, product 0x1170)
- Sends/receives MIDI CC on channel 12 (status byte 187/0xBB)
- LED output: CC 70-78 for 3 segments x 3 channels (R, G, B)
- Values: 0-127 (half of standard 0-255 RGB)
- The timeBuzzer app controls LED based on active project color; this script overrides it directly

## Syncing with Hue

Use the same signal vocabulary as the `hue` skill. Example combined command:

```bash
python3 ~/.claude/skills/timebuzzer-led/scripts/buzzer_led.py signal success &
python3 ~/.claude/skills/hue/scripts/hue.py signal success --group 1
```
