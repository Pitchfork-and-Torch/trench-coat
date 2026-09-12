"""HTTP/HTTPS forward-proxy hop."""

from __future__ import annotations

import asyncio
import base64
import time

from trenchcoat.hops.base import Hop, HopHealth, HopStatus


class HttpProxyHop(Hop):
    async def probe(self, timeout: float = 5.0) -> HopStatus:
        start = time.perf_counter()
        try:
            await asyncio.wait_for(self._connect_probe(), timeout=timeout)
            latency = (time.perf_counter() - start) * 1000
            self.status = HopStatus(
                hop_id=self.config.id,
                health=HopHealth.HEALTHY if latency < 2500 else HopHealth.DEGRADED,
                latency_ms=round(latency, 2),
                last_check=time.time(),
            )
        except Exception as exc:  # noqa: BLE001
            self.status = HopStatus(
                hop_id=self.config.id,
                health=HopHealth.DEAD,
                last_check=time.time(),
                error=str(exc),
            )
        return self.status

    async def _connect_probe(self) -> None:
        reader, writer = await asyncio.open_connection(self.config.host, self.config.port)
        try:
            headers = [
                b"CONNECT example.com:443 HTTP/1.1",
                b"Host: example.com:443",
                b"Proxy-Connection: keep-alive",
            ]
            if self.config.username:
                token = base64.b64encode(
                    f"{self.config.username}:{self.config.password or ''}".encode()
                ).decode()
                headers.append(f"Proxy-Authorization: Basic {token}".encode())
            writer.write(b"\r\n".join(headers) + b"\r\n\r\n")
            await writer.drain()
            line = await reader.readline()
            if b"200" not in line and b"Connection established" not in line:
                # Proxy answered — alive even if CONNECT policy denies
                if line.startswith(b"HTTP/"):
                    return
                raise ConnectionError(f"HTTP proxy bad response: {line[:80]!r}")
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass
