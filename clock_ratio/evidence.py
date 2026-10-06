"""Shared evidence-status vocabulary for audit outputs."""
from __future__ import annotations

from enum import Enum


class EvidenceStatus(str, Enum):
    established = "established"
    supported_with_limitations = "supported-with-limitations"
    pending_verification = "pending-verification"
    external_unverified = "external-unverified"
