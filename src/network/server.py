"""TCP host server (single client, v1)."""

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
    make_welcome,
    MsgType,
    PROTOCOL_VERSION,
)

logger = logging.getLogger(__name__)


class GameServer:
    def __init__(self, port: int, host_name: str, session_id: str) -> None:
        self.port = port
        self.host_name = host_name
        self.session_id = session_id
        self.incoming: queue.Queue[dict[str, Any]] = queue.Queue()
        self._sock: Optional[socket.socket] = None
        self._client_sock: Optional[socket.socket] = None
        self._send_lock = threading.Lock()
        self._stop = threading.Event()
        self._accept_thread: Optional[threading.Thread] = None
        self._recv_thread: Optional[threading.Thread] = None
        self.client_connected = False
        self.client_name = ""

    def start(self) -> bool:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.bind(("0.0.0.0", self.port))
            self._sock.listen(1)
            self._sock.settimeout(0.5)
            self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._accept_thread.start()
            logger.info("Multiplayer host listening on port %s", self.port)
            return True
        except OSError as e:
            logger.error("Failed to start host server: %s", e)
            self.stop()
            return False

    def _accept_loop(self) -> None:
        assert self._sock is not None
        while not self._stop.is_set():
            try:
                client, addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            if self._client_sock is not None:
                try:
                    client.close()
                except OSError:
                    pass
                continue
            logger.info("Client connected from %s", addr)
            self._client_sock = client
            self._client_sock.settimeout(0.5)
            self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self._recv_thread.start()
            break

    def _recv_loop(self) -> None:
        buf = ""
        sock = self._client_sock
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
                self._on_disconnect("client disconnected")
                break
            buf += chunk.decode("utf-8", errors="replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                msg = decode_line(line)
                if msg:
                    self._handle_incoming(msg)

    def _handle_incoming(self, msg: dict[str, Any]) -> None:
        mtype = msg.get("type")
        if mtype == MsgType.HELLO and not self.client_connected:
            if msg.get("protocol_version", 0) != PROTOCOL_VERSION:
                self.send(make_goodbye("protocol mismatch"))
                return
            self.client_name = str(msg.get("player_name", "Player"))[:64]
            self.client_connected = True
            self.send(
                make_welcome(self.session_id, player_id=1, host_name=self.host_name)
            )
            self.incoming.put({"type": "_client_connected", "player_name": self.client_name})
        self.incoming.put(msg)

    def _on_disconnect(self, reason: str) -> None:
        if self.client_connected or self._client_sock:
            self.incoming.put({"type": "_peer_disconnected", "reason": reason})
        self.client_connected = False
        if self._client_sock:
            try:
                self._client_sock.close()
            except OSError:
                pass
            self._client_sock = None

    def send(self, msg: dict[str, Any]) -> bool:
        sock = self._client_sock
        if not sock:
            return False
        data = encode_message(msg)
        with self._send_lock:
            try:
                sock.sendall(data)
                return True
            except OSError as e:
                logger.warning("Host send failed: %s", e)
                self._on_disconnect("send failed")
                return False

    def broadcast(self, msg: dict[str, Any]) -> bool:
        return self.send(msg)

    def stop(self) -> None:
        self._stop.set()
        if self._client_sock:
            try:
                self.send(make_goodbye("host shutdown"))
            except Exception:
                pass
        if self._client_sock:
            try:
                self._client_sock.close()
            except OSError:
                pass
            self._client_sock = None
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self.client_connected = False
