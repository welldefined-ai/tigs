"""Delta parsers for specification changes."""

from .capability_parser import CapabilityDeltaParser
from .capability_merger import CapabilityMerger

__all__ = ["CapabilityDeltaParser", "CapabilityMerger"]
