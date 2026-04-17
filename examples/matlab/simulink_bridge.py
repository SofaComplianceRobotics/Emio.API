import socket
import warnings
from enum import Enum

import numpy as np


class CommStatus(Enum):
    """Status returned by :meth:`SimulinkBridge.send_and_receive`.

    Attributes:
        OK: Reply received, sequence numbers match (one-tick delay).
        OK_NO_DELAY: Reply received with no delay (seq matches exactly).
        DESYNC: Sequence mismatch detected; bridge is flushing the buffer.
        TIMEOUT: No reply received within ``recv_timeout``.
        RECONNECTED: Bridge lost sync and successfully re-handshaked.
    """
    OK           = "OK"
    OK_NO_DELAY  = "OK_NO_DELAY"
    DESYNC       = "DESYNC"
    TIMEOUT      = "TIMEOUT"
    RECONNECTED  = "RECONNECTED"


class SimulinkBridge:
    """UDP bridge between Python and Simulink.

    Python is the clock master: it sends a vector of ``send_size`` doubles at
    each tick (prepended with a sequence number) and blocks until Simulink
    replies with a vector of ``recv_size`` doubles (also prepended with a
    sequence number).

    Wire format (both directions)::

        [ seq (float64) | data[0] | data[1] | ... ]
        total bytes = (1 + send_size) * 8   (Python -> Simulink)
        total bytes = (1 + recv_size) * 8   (Simulink -> Python)

    Not thread-safe: ``send_and_receive`` must be called from a single thread.

    Typical usage::

        with SimulinkBridge(send_size=3, recv_size=2) as bridge:
            bridge.handshake()
            while True:
                reply, status = bridge.send_and_receive(my_data)

    Args:
        send_size: Number of data doubles sent to Simulink each tick.
        recv_size: Number of data doubles expected from Simulink each tick.
        simulink_ip: IP address of the Simulink host.
        simulink_port: UDP port Simulink listens on (Python -> Simulink).
        python_port: UDP port Python listens on (Simulink -> Python).
        bind_port: Local port used for sending.
        recv_timeout: Socket timeout in seconds while waiting for a reply.
    """

    MAX_RECONNECT_ATTEMPTS = 3
    _MAX_DESYNC_COUNT      = 5

    def __init__(
        self,
        send_size: int,
        recv_size: int,
        simulink_ip: str    = "127.0.0.1",
        simulink_port: int  = 25000,
        python_port: int    = 25001,
        bind_port: int      = 9090,
        recv_timeout: float = 0.1,
    ):
        self.send_size      = send_size
        self.recv_size      = recv_size
        self.simulink_addr  = (simulink_ip, simulink_port)
        self.recv_timeout   = recv_timeout

        self._sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_send.bind(("127.0.0.1", bind_port))

        self._sock_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock_recv.bind(("127.0.0.1", python_port))

        self._seq           = 0
        self._last_reply    = np.zeros((recv_size, 1))
        self._timeout_count = 0
        self._desync_count  = 0

    # --------------------------------------------------------------------------
    # Context manager
    # --------------------------------------------------------------------------

    def __enter__(self) -> "SimulinkBridge":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # --------------------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------------------

    def handshake(self, handshake_timeout: float = 0.05) -> None:
        """Block until Simulink acknowledges the connection.

        Sends ``seq=-1`` with a zero payload of ``send_size`` doubles so the
        wire size is identical to the main loop. Resets the sequence counter
        on success.

        Args:
            handshake_timeout: Per-attempt socket timeout in seconds.
        """
        print("  -> Start the Simulink simulation now (waiting for handshake...)")

        payload    = np.zeros(1 + self.send_size, dtype=np.float64)
        payload[0] = -1.0

        self._sock_recv.settimeout(handshake_timeout)

        while True:
            self._sock_send.sendto(self._pack(payload), self.simulink_addr)
            try:
                self._sock_recv.recvfrom((self.recv_size + 1) * 8)
                print("  Handshake OK - ready!\n")
                break
            except socket.timeout:
                pass

        self._seq           = 0
        self._timeout_count = 0
        self._desync_count  = 0
        self._last_reply    = np.zeros((self.recv_size, 1))
        self._sock_recv.settimeout(self.recv_timeout)

    def send_and_receive(self, data: np.ndarray) -> tuple[np.ndarray, CommStatus]:
        """Send a data vector and return the reply from Simulink.

        ``data`` is silently padded with zeros or truncated to match
        ``send_size`` if needed (a warning is emitted).

        On consecutive timeouts (>= ``MAX_RECONNECT_ATTEMPTS``) or persistent
        desyncs (>= ``_MAX_DESYNC_COUNT``), a new handshake is triggered
        automatically.

        Args:
            data: Vector of doubles, ideally shape ``(send_size,)`` or
                ``(send_size, 1)``.

        Returns:
            A tuple ``(reply, status)`` where ``reply`` has shape
            ``(recv_size, 1)`` and ``status`` is one of:
            :class:`CommStatus`.

        Raises:
            RuntimeError: If the packet received from Simulink has an
                unexpected size (mismatch between ``recv_size`` and the
                Simulink UDP Send block configuration).
        """
        data    = self._coerce_send_data(np.asarray(data, dtype=np.float64).flatten())
        seq     = self._seq
        payload = np.concatenate([[float(seq)], data])
        self._sock_send.sendto(self._pack(payload), self.simulink_addr)

        try:
            raw, _ = self._sock_recv.recvfrom((self.recv_size + 1) * 8)

            expected = (self.recv_size + 1) * 8
            if len(raw) != expected:
                raise RuntimeError(
                    f"Unexpected packet size from Simulink: got {len(raw)} bytes, "
                    f"expected {expected}. "
                    f"Check that recv_size={self.recv_size} matches your "
                    f"Simulink UDP Send block."
                )

            response            = self._unpack(raw, self.recv_size + 1)
            seq_back            = int(response[0, 0])
            reply               = response[1:]
            self._last_reply    = reply
            self._timeout_count = 0
            status              = self._sync_status(seq_back, seq)

            if status == CommStatus.DESYNC:
                self._desync_count += 1
                self._flush_recv_buffer()
                if self._desync_count >= self._MAX_DESYNC_COUNT:
                    print(f"\n  {self._MAX_DESYNC_COUNT} consecutive desyncs "
                          f"- restarting handshake...")
                    self.handshake()
                    return self._last_reply, CommStatus.RECONNECTED
            else:
                self._desync_count = 0

        except socket.timeout:
            reply = self._last_reply
            self._timeout_count += 1
            status = CommStatus.TIMEOUT

            if self._timeout_count >= self.MAX_RECONNECT_ATTEMPTS:
                print(f"\n  {self.MAX_RECONNECT_ATTEMPTS} consecutive timeouts "
                      f"- restarting handshake...")
                self.handshake()
                return self._last_reply, CommStatus.RECONNECTED

        self._seq += 1
        return reply, status

    def close(self) -> None:
        """Release UDP sockets."""
        self._sock_send.close()
        self._sock_recv.close()

    @property
    def seq(self) -> int:
        """Current sequence counter."""
        return self._seq

    # --------------------------------------------------------------------------
    # Private helpers
    # --------------------------------------------------------------------------

    def _coerce_send_data(self, data: np.ndarray) -> np.ndarray:
        """Pad or truncate ``data`` to ``send_size``, warning if needed."""
        n = len(data)
        if n == self.send_size:
            return data
        if n < self.send_size:
            warnings.warn(
                f"send_and_receive: data has {n} value(s), expected "
                f"{self.send_size}. Padding with zeros.",
                stacklevel=3,
            )
            return np.pad(data, (0, self.send_size - n))
        warnings.warn(
            f"send_and_receive: data has {n} value(s), expected "
            f"{self.send_size}. Truncating to first {self.send_size}.",
            stacklevel=3,
        )
        return data[: self.send_size]

    def _flush_recv_buffer(self) -> None:
        """Drain any stale packets so the next read is up to date."""
        self._sock_recv.settimeout(0)
        try:
            while True:
                self._sock_recv.recvfrom((self.recv_size + 1) * 8)
        except (socket.timeout, BlockingIOError):
            pass
        finally:
            self._sock_recv.settimeout(self.recv_timeout)

    @staticmethod
    def _pack(arr: np.ndarray) -> bytes:
        return arr.astype(np.float64).flatten().tobytes()

    @staticmethod
    def _unpack(data: bytes, n: int) -> np.ndarray:
        return np.frombuffer(data, dtype=np.float64).reshape(n, 1)

    @staticmethod
    def _sync_status(seq_back: int, seq: int) -> CommStatus:
        if seq_back == seq - 1:
            return CommStatus.OK
        if seq_back == seq:
            return CommStatus.OK_NO_DELAY
        return CommStatus.DESYNC
