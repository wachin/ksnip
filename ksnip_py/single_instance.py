from __future__ import annotations

import json
import os
from collections.abc import Callable

from PyQt6.QtCore import QObject
from PyQt6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstanceController(QObject):
    def __init__(self, server_name: str | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.server_name = server_name or f"ksnip-pyqt6-{os.getuid()}"
        self._server = QLocalServer(self)
        self._handler: Callable[[list[str]], None] | None = None
        self._sockets: set[QLocalSocket] = set()
        self._buffers: dict[QLocalSocket, bytearray] = {}
        self._server.newConnection.connect(self._accept_connections)

    def forward_to_running(self, arguments: list[str], timeout_ms: int = 500) -> bool:
        socket = QLocalSocket(self)
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(timeout_ms):
            return False
        payload = json.dumps({"arguments": arguments}).encode("utf-8") + b"\n"
        socket.write(payload)
        if not socket.waitForBytesWritten(timeout_ms):
            socket.abort()
            return True
        socket.waitForReadyRead(timeout_ms)
        socket.disconnectFromServer()
        return True

    def listen(self, handler: Callable[[list[str]], None]) -> bool:
        self._handler = handler
        if self._server.listen(self.server_name):
            return True
        QLocalServer.removeServer(self.server_name)
        return self._server.listen(self.server_name)

    def _accept_connections(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            self._sockets.add(socket)
            self._buffers[socket] = bytearray()
            socket.readyRead.connect(lambda current=socket: self._read_request(current))
            socket.disconnected.connect(lambda current=socket: self._forget_socket(current))
            if socket.bytesAvailable():
                self._read_request(socket)

    def _read_request(self, socket: QLocalSocket) -> None:
        buffer = self._buffers.setdefault(socket, bytearray())
        buffer.extend(bytes(socket.readAll()))
        if b"\n" not in buffer:
            return
        raw_payload, _separator, _remainder = bytes(buffer).partition(b"\n")
        try:
            payload = json.loads(raw_payload.decode("utf-8"))
            arguments = payload.get("arguments", [])
            if self._handler is not None and isinstance(arguments, list) and all(isinstance(arg, str) for arg in arguments):
                self._handler(arguments)
            socket.write(b"ok")
            socket.flush()
        except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
            socket.write(b"error")
            socket.flush()

    def _forget_socket(self, socket: QLocalSocket) -> None:
        self._sockets.discard(socket)
        self._buffers.pop(socket, None)
        socket.deleteLater()
