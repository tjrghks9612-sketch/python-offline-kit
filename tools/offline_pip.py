"""Run pip with configuration disabled and all network sockets blocked."""

from __future__ import annotations

import os
import socket
import sys


def block_network(*args: object, **kwargs: object) -> None:
    raise OSError("Network access is disabled by the offline installer")


def main() -> int:
    os.environ["PIP_CONFIG_FILE"] = os.devnull
    os.environ["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    for name in tuple(os.environ):
        if name.startswith("PIP_") and name not in {
            "PIP_CONFIG_FILE",
            "PIP_DISABLE_PIP_VERSION_CHECK",
        }:
            del os.environ[name]
    socket.socket.connect = block_network
    socket.socket.connect_ex = block_network
    socket.create_connection = block_network
    socket.getaddrinfo = block_network
    from pip._internal.cli.main import main as pip_main

    return pip_main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
