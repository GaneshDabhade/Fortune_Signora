"""Provider mappers — the border between vendor languages and Signora's.

**No vendor field name appears outside this package** (AC-23). When
authentic payloads replace the fixtures, only these files change.
"""

from modules.provider_normalization.domain.mapper import ProviderMapper
from modules.provider_normalization.infrastructure.mappers.enrichment import (
    ApolloMapper,
    BuiltWithMapper,
    CoreSignalMapper,
    CrunchbaseMapper,
)
from modules.provider_normalization.infrastructure.mappers.intent import BomboraMapper

#: Registry. A provider with no mapper is a typed failure at translation
#: time, not an empty result — an unmapped provider must never look like a
#: provider with nothing to say.
MAPPERS: dict[str, ProviderMapper] = {
    mapper.provider: mapper
    for mapper in (
        ApolloMapper(),
        BuiltWithMapper(),
        CrunchbaseMapper(),
        CoreSignalMapper(),
        BomboraMapper(),
    )
}

__all__ = [
    "MAPPERS",
    "ApolloMapper",
    "BomboraMapper",
    "BuiltWithMapper",
    "CoreSignalMapper",
    "CrunchbaseMapper",
    "ProviderMapper",
]
