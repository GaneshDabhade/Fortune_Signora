"""Provider Platform's public contract.

Other modules and the composition root import from here. Nothing imports
`domain/`, `application/`, or `infrastructure/` directly (CLAUDE.md §5).
"""

from modules.provider_platform.domain.provider import (
    ProviderAdapter,
    ProviderCapability,
    ProviderCapabilityUnsupportedError,
    ProviderDescriptor,
    ProviderError,
    ProviderName,
    ProviderPayloadInvalidError,
    ProviderPermanentError,
    ProviderRateLimitedError,
    ProviderRecord,
    ProviderRegistry,
    ProviderRequest,
    ProviderResponse,
    ProviderTransientError,
    ReplayContext,
)
from modules.provider_platform.public.records import RawRecordReader, RawRecordView

__all__ = [
    "ProviderAdapter",
    "ProviderCapability",
    "ProviderCapabilityUnsupportedError",
    "ProviderDescriptor",
    "ProviderError",
    "ProviderName",
    "ProviderPayloadInvalidError",
    "ProviderPermanentError",
    "ProviderRateLimitedError",
    "ProviderRecord",
    "ProviderRegistry",
    "ProviderRequest",
    "ProviderResponse",
    "ProviderTransientError",
    "RawRecordReader",
    "RawRecordView",
    "ReplayContext",
]
