"""TCP client for joining a host."""

from __future__ import annotations

import logging
import queue
import socket
import threading
from typing import Any, Optional

from src.network.protocol import (
    decode_line,
    encode_message,
    make_goodbye,
    make_hello,
    MsgType,
    PROTOCOL_VERSION,
)

logger = logging.getLogger(__name__)


class GameClient:
    def __init__(self, connect_timeout_sec: float = 10.0) -> None:
        self.connect_timeout_sec = connect_timeout_sec
        self.incoming: queue.Queue[dict[str, Any]] = queue.Queue()
        self._sock: Optional[socket.socket] = None
        self._send_lock = threading.Lock()
        self._stop = threading.Event()
        self._recv_thread: Optional[threading.Thread] = None
        self.connected = False
        self.player_name = ""

    def connect(self, host: str, port: int, player_name: str) -> bool:
        self.player_name = player_name
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connect_timeout_sec)
            sock.connect((host, port))
            sock.settimeout(0.5)
            self._sock = sock
            self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self._recv_thread.start()
            self.send(make_hello(player_name))
            logger.info("Connected to host %s:%s", host, port)
            return True
        except OSError as e:
            logger.error("Connect failed: %s", e)
            self.stop()
            return False

    def _recv_loop(self) -> None:
        buf = ""
        sock = self._sock
        if not sock:
            return
        while not self._stop.is_set():
            try:
                chunk = sock.recv(4096)
            except socket.timeout:
                continue
            except OSError:
                self._on_disconnect("connection lost")
                break
            if not chunk:
                self._on_disconnect("host disconnected")
                break
            buf += chunk.decode("utf-8", errors="replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                msg = decode_line(line)
                if msg:
                    self._handle_incoming(msg)

    def _handle_incoming(self, msg: dict[str, Any]) -> None:
        mtype = msg.get("type")
        if mtype == MsgType.WELCOME and not self.connected:
            if msg.get("protocol_version", 0) != PROTOCOL_VERSION:
                self.incoming.put({"type": "_connect_failed", "reason": "protocol mismatch"})
                self.stop()
                return
            self.connected = True
            self.incoming.put({"type": "_connected", "welcome": msg})
        elif mtype == MsgType.GOODBYE:
            self.incoming.put(msg)
            self._on_disconnect(msg.get("reason", "goodbye"))
            return
        self.incoming.put(msg)

    def _on_disconnect(self, reason: str) -> None:
        was = self.connected
        self.connected = False
        if was or self._sock:
            self.incoming.put({"type": "_peer_disconnected", "reason": reason})
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def send(self, msg: dict[str, Any]) -> bool:
        sock = self._sock
        if not sock:
            return False
        data = encode_message(msg)
        with self._send_lock:
            try:
                sock.sendall(data)
                return True
            except OSError as e:
                logger.warning("Client send failed: %s", e)
                self._on_disconnect("send failed")
                return False

    def stop(self) -> None:
        self._stop.set()
        if self._sock and self.connected:
            try:
                self.send(make_goodbye("client leaving"))
            except Exception:
                pass
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self.connected = False
