"""Tor control-port NEWNYM / status (Phase 1 leftover + Phase 3 polish)."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

log = logging.getLogger("trenchcoat.torctl")


async def signal_newnym(
    host: str = "127.0.0.1",
    port: int = 9051,
    password: str | None = None,
    cookie_path: str | None = None,
    timeout: float = 5.0,
) -> tuple[bool, str]:
    """
    Send SIGNAL NEWNYM to Tor control port.
    Auth: password or cookie file (CookieAuthentication 1).
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
    except Exception as exc:  # noqa: BLE001
        return False, f"control port unreachable: {exc}"

    async def read_reply() -> str:
        lines = []
        while True:
            line = await asyncio.wait_for(reader.readline(), timeout=timeout)
            if not line:
                break
            s = line.decode("utf-8", errors="replace").rstrip()
            lines.append(s)
            if len(s) >= 4 and s[3] == " ":
                break
        return "\n".join(lines)

    try:
        await read_reply()  # banner
        if password is not None:
            writer.write(f'AUTHENTICATE "{password}"\r\n'.encode())
        elif cookie_path and Path(cookie_path).exists():
            cookie = Path(cookie_path).read_bytes().hex()
            writer.write(f"AUTHENTICATE {cookie}\r\n".encode())
        else:
            writer.write(b'AUTHENTICATE ""\r\n')
        await writer.drain()
        auth = await read_reply()
        if not auth.startswith("250"):
            return False, f"auth failed: {auth}"
        writer.write(b"SIGNAL NEWNYM\r\n")
        await writer.drain()
        resp = await read_reply()
        writer.write(b"QUIT\r\n")
        await writer.drain()
        ok = resp.startswith("250")
        return ok, resp
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:  # noqa: BLE001
            pass
