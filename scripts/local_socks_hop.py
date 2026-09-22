#!/usr/bin/env python3
"""Minimal local SOCKS5 hop for multi-hop lab chains (Ghost / Journalist).

Listens on a loopback port and dials destinations directly (or via optional
upstream SOCKS). Use this until a real VPN/VPS SOCKS is available.

  python scripts/local_socks_hop.py --port 1088 --label vpn-lab
  python scripts/local_socks_hop.py --port 1081 --label relay-lab

Replace with real endpoints by editing config hops (host/port/user/pass).
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import struct
import sys

log = logging.getLogger("trenchcoat.local_hop")


class LocalSocks5:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        upstream: str | None = None,
        label: str = "lab",
    ) -> None:
        self.host = host
        self.port = port
        self.upstream = upstream
        self.label = label
        self._server: asyncio.Server | None = None

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle, self.host, self.port)
        addrs = ", ".join(str(s.getsockname()) for s in (self._server.sockets or []))
        log.info("[%s] SOCKS5 listening on %s", self.label, addrs)

    async def serve_forever(self) -> None:
        assert self._server
        async with self._server:
            await self._server.serve_forever()

    async def _handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            header = await reader.readexactly(2)
            ver, nmethods = header[0], header[1]
            if ver != 5:
                writer.close()
                return
            await reader.readexactly(nmethods)
            writer.write(b"\x05\x00")
            await writer.drain()

            req = await reader.readexactly(4)
            if req[0] != 5 or req[1] != 1:
                writer.write(b"\x05\x07\x00\x01" + b"\x00" * 6)
                await writer.drain()
                return
            atyp = req[3]
            if atyp == 1:
                raw = await reader.readexactly(4)
                host = ".".join(str(b) for b in raw)
            elif atyp == 3:
                ln = (await reader.readexactly(1))[0]
                host = (await reader.readexactly(ln)).decode("utf-8", "replace")
            elif atyp == 4:
                raw = await reader.readexactly(16)
                host = ":".join(f"{raw[i]:02x}{raw[i+1]:02x}" for i in range(0, 16, 2))
            else:
                writer.write(b"\x05\x08\x00\x01" + b"\x00" * 6)
                await writer.drain()
                return
            port = struct.unpack("!H", await reader.readexactly(2))[0]

            remote_r, remote_w = await self._dial(host, port)
            writer.write(b"\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00")
            await writer.drain()
            await self._pipe(reader, writer, remote_r, remote_w)
        except Exception as exc:  # noqa: BLE001
            log.debug("client error: %s", exc)
            try:
                writer.write(b"\x05\x01\x00\x01" + b"\x00" * 6)
                await writer.drain()
            except Exception:  # noqa: BLE001
                pass
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass

    async def _dial(self, host: str, port: int):
        if self.upstream:
            from python_socks.async_.asyncio import Proxy

            proxy = Proxy.from_url(self.upstream)
            sock = await proxy.connect(dest_host=host, dest_port=port)
            return await asyncio.open_connection(sock=sock)
        return await asyncio.open_connection(host, port)

    async def _pipe(self, c_r, c_w, r_r, r_w) -> None:
        async def pump(src, dst):
            try:
                while True:
                    data = await src.read(65536)
                    if not data:
                        break
                    dst.write(data)
                    await dst.drain()
            except Exception:  # noqa: BLE001
                pass
            finally:
                try:
                    dst.close()
                except Exception:  # noqa: BLE001
                    pass

        await asyncio.gather(pump(c_r, r_w), pump(r_r, c_w))


async def _main_async(args: argparse.Namespace) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    hop = LocalSocks5(args.host, args.port, upstream=args.upstream, label=args.label)
    await hop.start()
    await hop.serve_forever()


def main() -> None:
    p = argparse.ArgumentList if False else argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--label", default="lab-hop")
    p.add_argument(
        "--upstream",
        default=None,
        help="Optional upstream proxy URL, e.g. socks5://127.0.0.1:9050",
    )
    args = p.parse_args()
    try:
        asyncio.run(_main_async(args))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
