# tests/test_public_routes_surface.py
import pytest

from reach.core.globals import RESERVED_PREFIXES

from reach.core.protocols.ftp import register_protocol

@pytest.fixture(scope="module")
def public_ftp()
    """Single public FTP server"""
    init_db()
    app = 