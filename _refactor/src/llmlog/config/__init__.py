"""Config models and loaders for `_refactor/configs/*`.

We deliberately keep configs *semantic* (what you want to measure) rather than
implementation-specific. The runner consumes a resolved config with expanded targets.
"""

from .schema import (
    AnswerFormat,
    PromptProfile,
    RenderPolicy,
    Representation,
    ResponseStyle,
    Subset,
    SuiteConfig,
    TargetConfig,
    TargetSetConfig,
    Task,
)
from .loader import load_suite_config, load_target_set_config, resolve_suite

__all__ = [
    "Task",
    "Subset",
    "Representation",
    "PromptProfile",
    "ResponseStyle",
    "AnswerFormat",
    "RenderPolicy",
    "TargetConfig",
    "TargetSetConfig",
    "SuiteConfig",
    "load_target_set_config",
    "load_suite_config",
    "resolve_suite",
]


