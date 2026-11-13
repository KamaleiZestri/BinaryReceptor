"""Native Windows Bluetooth RFCOMM Server and SDP Advertiser for BinaryReceptor v3.0.0.

Completely replaces the legacy hxBluetooth C#/Haxe build chain with native Win32 Winsock
bindings (AF_BTH, SOCK_STREAM, BTPROTO_RFCOMM) and ws2_32.WSASetServiceW SDP registration.
Advertises the exact UUID required by BinaryEye (8a8478c9-2ca8-404b-a0de-101f34ab71ae).
"""
from __future__ import annotations

import ctypes
import logging
import os
import socket
import sys
import threading
import time
import uuid
from ctypes import wintypes
from typing import Callable, Any

from src.core.http_server import ScanPayload
from src.version import DEFAULT_BT_UUID, DEFAULT_BT_NAME

logger = logging.getLogger("BinaryReceptor.Bluetooth")

# Windows Sockets Bluetooth Constants
AF_BTH = 32
BTPROTO_RFCOMM = 3
NS_BTH = 16
RNRSERVICE_REGISTER = 0
RNRSERVICE_DEREGISTER = 1
RNRSERVICE_DELETE = 2


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_uuid_str(cls, u_str: str) -> "GUID":
        u = uuid.UUID(u_str)
        guid = cls()
        guid.Data1 = u.time_low
        guid.Data2 = u.time_mid
        guid.Data3 = u.time_hi_version
        for i in range(8):
            guid.Data4[i] = u.bytes[8 + i]
        return guid


class SOCKADDR_BTH(ctypes.Structure):
    _fields_ = [
        ("addressFamily", ctypes.c_ushort),
        ("btAddr", ctypes.c_ulonglong),
        ("serviceClassId", GUID),
        ("port", wintypes.ULONG),
    ]


class SOCKET_ADDRESS(ctypes.Structure):
    _fields_ = [
        ("lpSockaddr", ctypes.POINTER(SOCKADDR_BTH)),
        ("iSockaddrLength", ctypes.c_int),
    ]


class CSADDR_INFO(ctypes.Structure):
    _fields_ = [
        ("LocalAddr", SOCKET_ADDRESS),
        ("RemoteAddr", SOCKET_ADDRESS),
        ("iSocketType", ctypes.c_int),
        ("iProtocol", ctypes.c_int),
    ]


class WSAQUERYSETW(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("lpszServiceInstanceName", wintypes.LPWSTR),
        ("lpServiceClassId", ctypes.POINTER(GUID)),
        ("lpVersion", wintypes.LPVOID),
        ("lpszComment", wintypes.LPWSTR),
        ("dwNameSpace", wintypes.DWORD),
        ("lpNSProviderId", wintypes.LPVOID),
        ("lpszContext", wintypes.LPWSTR),
        ("dwNumberOfProtocols", wintypes.DWORD),
        ("lpafpProtocols", wintypes.LPVOID),
        ("lpszQueryString", wintypes.LPWSTR),
        ("dwNumberOfCsAddrs", wintypes.DWORD),
        ("lpcsaBuffer", ctypes.POINTER(CSADDR_INFO)),
        ("dwOutputFlags", wintypes.DWORD),
        ("lpBlob", wintypes.LPVOID),
    ]


ws2_32 = None
if os.name == "nt":
    try:
        ws2_32 = ctypes.WinDLL("ws2_32", use_last_error=True)
        ws2_32.WSASetServiceW.argtypes = [ctypes.POINTER(WSAQUERYSETW), wintypes.DWORD, wintypes.DWORD]
        ws2_32.WSASetServiceW.restype = ctypes.c_int
    except Exception:
        pass


def is_bluetooth_available() -> bool:
    """Check if native Windows Bluetooth socket support is available on this host."""
    if os.name != "nt":
        return False
    try:
        s = socket.socket(AF_BTH, socket.SOCK_STREAM, BTPROTO_RFCOMM)
        s.close()
        return True
    except Exception:
        return False


def get_local_bt_address() -> str:
    """Retrieve local Bluetooth adapter MAC address if available."""
    if os.name != "nt":
        return "N/A"
    try:
        s = socket.socket(AF_BTH, socket.SOCK_STREAM, BTPROTO_RFCOMM)
        s.bind(("00:00:00:00:00:00", 0))
        addr, _ = s.getsockname()
        s.close()
        return addr or "N/A"
    except Exception:
        return "N/A"


class BluetoothServerController:
    """Manages the native Windows AF_BTH RFCOMM listener and SDP advertisement."""

    def __init__(
        self,
        service_uuid: str = DEFAULT_BT_UUID,
        service_name: str = DEFAULT_BT_NAME,
        on_scan: Callable[[ScanPayload], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> None:
        self.service_uuid = service_uuid
        self.service_name = service_name
        self.on_scan = on_scan or (lambda p: None)
        self.on_status_change = on_status_change or (lambda s: None)

        self._server_sock: socket.socket | None = None
        self._is_running = threading.Event()
        self._stop_requested = threading.Event()
        self._thread: threading.Thread | None = None
        self._connected_client: socket.socket | None = None
        self._client_lock = threading.Lock()
        self._status: str = "Stopped"

        # Anchor ctypes buffers in memory so GC does not discard them during service registration
        self._guid: GUID | None = None
        self._sockaddr: SOCKADDR_BTH | None = None
        self._csaddr: CSADDR_INFO | None = None
        self._queryset: WSAQUERYSETW | None = None
        self._name_buf: Any = None
        self._comment_buf: Any = None

    @property
    def is_running(self) -> bool:
        return self._is_running.is_set()

    @property
    def status(self) -> str:
        return self._status

    def _set_status(self, status: str) -> None:
        self._status = status
        try:
            self.on_status_change(status)
        except Exception:
            pass

    def _register_sdp(self, sock: socket.socket) -> bool:
        """Register the BinaryEye RFCOMM service record in Windows SDP."""
        if not ws2_32:
            return False

        try:
            self._guid = GUID.from_uuid_str(self.service_uuid)

            self._sockaddr = SOCKADDR_BTH()
            sa_len = ctypes.c_int(ctypes.sizeof(self._sockaddr))
            ret = ws2_32.getsockname(
                sock.fileno(),
                ctypes.byref(self._sockaddr),
                ctypes.byref(sa_len),
            )
            if ret != 0:
                logger.error("ws2_32.getsockname failed for BT socket: %s", ctypes.get_last_error())
                return False

            self._sockaddr.serviceClassId = self._guid

            self._csaddr = CSADDR_INFO()
            self._csaddr.LocalAddr.lpSockaddr = ctypes.pointer(self._sockaddr)
            self._csaddr.LocalAddr.iSockaddrLength = ctypes.sizeof(self._sockaddr)
            self._csaddr.RemoteAddr.lpSockaddr = ctypes.pointer(self._sockaddr)
            self._csaddr.RemoteAddr.iSockaddrLength = ctypes.sizeof(self._sockaddr)
            self._csaddr.iSocketType = socket.SOCK_STREAM
            self._csaddr.iProtocol = BTPROTO_RFCOMM

            self._name_buf = ctypes.create_unicode_buffer(self.service_name)
            self._comment_buf = ctypes.create_unicode_buffer("BinaryEye Android Barcode Companion")

            self._queryset = WSAQUERYSETW()
            self._queryset.dwSize = ctypes.sizeof(WSAQUERYSETW)
            self._queryset.lpszServiceInstanceName = ctypes.cast(self._name_buf, wintypes.LPWSTR)
            self._queryset.lpszComment = ctypes.cast(self._comment_buf, wintypes.LPWSTR)
            self._queryset.lpServiceClassId = ctypes.pointer(self._guid)
            self._queryset.dwNumberOfCsAddrs = 1
            self._queryset.dwNameSpace = NS_BTH
            self._queryset.lpcsaBuffer = ctypes.pointer(self._csaddr)

            res = ws2_32.WSASetServiceW(ctypes.byref(self._queryset), RNRSERVICE_REGISTER, 0)
            if res != 0:
                logger.error("WSASetServiceW registration failed: %s", ctypes.get_last_error())
                return False
            return True
        except Exception as e:
            logger.exception("Exception during SDP registration: %s", e)
            return False

    def _deregister_sdp(self) -> None:
        """Deregister SDP service record from Windows."""
        if ws2_32 and self._queryset is not None:
            try:
                ws2_32.WSASetServiceW(ctypes.byref(self._queryset), RNRSERVICE_DELETE, 0)
            except Exception:
                try:
                    ws2_32.WSASetServiceW(ctypes.byref(self._queryset), RNRSERVICE_DEREGISTER, 0)
                except Exception:
                    pass
            self._queryset = None

    def start(self) -> tuple[bool, str]:
        """Start listening for incoming Bluetooth connections from paired devices."""
        if self.is_running:
            return True, "Bluetooth server already running"

        if os.name != "nt":
            self._set_status("Unavailable (Windows Only)")
            return False, "Native Bluetooth RFCOMM requires Windows"

        self._stop_requested.clear()

        try:
            srv = socket.socket(AF_BTH, socket.SOCK_STREAM, BTPROTO_RFCOMM)
            srv.bind(("00:00:00:00:00:00", 0))
            srv.listen(2)
            self._server_sock = srv
        except OSError as e:
            msg = f"Bluetooth adapter not found or disabled: {e}"
            self._set_status("Adapter Off")
            return False, msg

        # Register SDP record
        if not self._register_sdp(srv):
            logger.warning("Could not register SDP record; proceeding with raw RFCOMM socket")

        self._is_running.set()
        self._set_status("Listening")

        self._thread = threading.Thread(
            target=self._accept_loop,
            name="BinaryReceptor-Bluetooth",
            daemon=True,
        )
        self._thread.start()
        return True, "Bluetooth RFCOMM listening"

    def _accept_loop(self) -> None:
        """Continuously accept connections from paired Android devices."""
        srv = self._server_sock
        while not self._stop_requested.is_set() and srv:
            try:
                srv.settimeout(1.5)
                try:
                    client, client_info = srv.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self._stop_requested.is_set():
                        break
                    continue

                client_addr = client_info[0] if client_info else "paired-device"
                logger.info("Accepted Bluetooth connection from %s", client_addr)
                self._set_status(f"Connected ({client_addr})")

                with self._client_lock:
                    self._connected_client = client

                self._handle_client_stream(client, client_addr)

                with self._client_lock:
                    self._connected_client = None

                if not self._stop_requested.is_set():
                    self._set_status("Listening")

            except Exception as e:
                if not self._stop_requested.is_set():
                    logger.error("Error in Bluetooth accept loop: %s", e)
                    time.sleep(0.5)

        self._is_running.clear()
        if not self._stop_requested.is_set():
            self._set_status("Stopped")

    def _handle_client_stream(self, client: socket.socket, client_addr: str) -> None:
        """Read and buffer stream chunks, dispatching scans on delimiter."""
        buffer = ""
        client.settimeout(2.0)

        while not self._stop_requested.is_set():
            try:
                chunk_bytes = client.recv(4096)
                if not chunk_bytes:
                    logger.info("Bluetooth client disconnected: %s", client_addr)
                    break

                text = chunk_bytes.decode("utf-8", errors="replace")
                buffer += text

                # Handle line delimiters
                while "\n" in buffer or "\r" in buffer:
                    # Normalize CRLF
                    if "\r\n" in buffer:
                        line, buffer = buffer.split("\r\n", 1)
                    elif "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                    elif "\r" in buffer:
                        line, buffer = buffer.split("\r", 1)
                    else:
                        break

                    clean_line = line.strip()
                    if clean_line:
                        payload = ScanPayload(
                            content=clean_line,
                            format="",
                            source="Bluetooth",
                            client_address=client_addr,
                        )
                        try:
                            self.on_scan(payload)
                        except Exception:
                            logger.exception("Error in BT on_scan callback")

            except socket.timeout:
                continue
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                break

        # Process any trailing content in buffer upon disconnect
        clean_trailing = buffer.strip()
        if clean_trailing:
            payload = ScanPayload(
                content=clean_trailing,
                format="",
                source="Bluetooth",
                client_address=client_addr,
            )
            try:
                self.on_scan(payload)
            except Exception:
                pass

        try:
            client.close()
        except Exception:
            pass

    def stop(self) -> None:
        """Stop listening and cleanly disconnect any active clients and SDP."""
        self._stop_requested.set()
        self._set_status("Stopping")

        with self._client_lock:
            if self._connected_client:
                try:
                    self._connected_client.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self._connected_client.close()
                except Exception:
                    pass
                self._connected_client = None

        if self._server_sock:
            sock = self._server_sock
            self._server_sock = None
            try:
                sock.close()
            except Exception:
                pass

        self._deregister_sdp()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self._is_running.clear()
        self._set_status("Stopped")
