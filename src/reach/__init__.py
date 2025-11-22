"""
REACH - pluggable web exploitation / payload framework.

Subpackages:
- reach.core  : backend server, DB, auth, routing, logging, REST API
- reach.forge : payload generation engine that can integrate with core
- reach.cli   : command-line interface entrypoints
"""

__all__ = ["core", "forge"]
__version__ = "0.1.0"
