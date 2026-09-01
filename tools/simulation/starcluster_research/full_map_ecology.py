"""Compatibility facade for the canonical finite-map combat kernel.

CP126 introduced the full-map research consumer under this historical module
name. CP132 promotes that implementation, after mechanics reconciliation, as
the canonical combat kernel used by active/future research studies. Historical
imports remain valid so accepted study definitions do not need to be rewritten
merely to follow the shared implementation.
"""
from .canonical_combat import *  # noqa: F401,F403
