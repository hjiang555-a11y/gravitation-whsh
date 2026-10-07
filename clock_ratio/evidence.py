"""Single source of the evidence-status vocabulary for audit outputs (budget, manifest, ledgers)."""
from __future__ import annotations

from enum import Enum


class EvidenceStatus(str, Enum):
    established = "established"
    supported_with_limitations = "supported-with-limitations"
    pending_verification = "pending-verification"
    external_unverified = "external-unverified"
