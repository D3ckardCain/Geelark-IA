"""Clasificación estricta de direcciones permitidas para el plano privado."""
from __future__ import annotations

import ipaddress
from ipaddress import IPv4Address, IPv6Address

Address = IPv4Address | IPv6Address
_PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(cidr)
    for cidr in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "fc00::/7",
    )
)


def is_private_lan_address(address: Address) -> bool:
    """Acepta solo RFC1918, IPv6 ULA y loopback; no doc/link-local/CGNAT."""
    if address.is_loopback:
        return True
    return any(address.version == network.version and address in network for network in _PRIVATE_NETWORKS)
