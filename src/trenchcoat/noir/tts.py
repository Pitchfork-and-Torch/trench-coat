"""Noir Mode TTS — gritty detective voice (Phase 4)."""

from __future__ import annotations

import logging
import platform
import subprocess
import threading

from trenchcoat.noir.narration import say

log = logging.getLogger("trenchcoat.tts")


def speak(text: str | None = None, event: str | None = None) -> bool:
    """Speak a noir line. Returns True if a speech backend accepted the job."""
    line = text or (say(event) if event else say("boot"))
    system = platform.system()
    try:
        if system == "Windows":
            return _sapi(line)
        if system == "Darwin":
            subprocess.Popen(["say", line], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        # Linux espeak/spd-say
        for cmd in (["espeak", line], ["spd-say", line], ["festival", "--tts"]):
            try:
                if cmd[0] == "festival":
                    p = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    assert p.stdin
                    p.stdin.write(line.encode())
                    p.stdin.close()
                else:
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except FileNotFoundError:
                continue
    except Exception as exc:  # noqa: BLE001
        log.debug("tts failed: %s", exc)
    return False


def speak_async(event: str = "engage") -> None:
    threading.Thread(target=speak, kwargs={"event": event}, daemon=True).start()


def _sapi(line: str) -> bool:
    # Escape for PowerShell single-quoted string
    safe = line.replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.Speak('{safe}')"
    )
    subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", ps],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True
