from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class Task(str, Enum):
    sat_decision = "sat_decision"


class Subset(str, Enum):
    hornonly = "hornonly"
    nonhornonly = "nonhornonly"
    mixed = "mixed"


class Representation(str, Enum):
    horn_rules = "horn_rules"
    cnf_nl = "cnf_nl"
    cnf_compact = "cnf_compact"


class PromptProfile(str, Enum):
    direct = "direct"
    mixed_interpretation = "mixed_interpretation"


class ResponseStyle(str, Enum):
    answer_only = "answer_only"
    explain_then_answer = "explain_then_answer"


class AnswerFormat(str, Enum):
    yes_no = "yes_no"
    contradiction_satisfiable = "contradiction_satisfiable"


class RenderPolicy(str, Enum):
    fixed = "fixed"
    match_formula = "match_formula"


class RetrySettings(BaseModel):
    max_attempts: int = 3
    backoff_seconds: List[int] = Field(default_factory=lambda: [2, 5, 10])


class ConcurrencySettings(BaseModel):
    # per-problem fanout in lockstep mode
    workers: int = 4
    # number of target groups run concurrently (non-lockstep mode)
    targets_workers: int = 1
    lockstep: bool = False
    rate_limit_per_min: Optional[int] = None
    retry: RetrySettings = Field(default_factory=RetrySettings)


class ThinkingOptions(BaseModel):
    enabled: bool = False
    # Anthropic/Gemini
    budget_tokens: Optional[int] = None
    # OpenAI
    effort: Optional[Literal["low", "medium", "high"]] = None


class OutputsConfig(BaseModel):
    class Results(BaseModel):
        enabled: bool = True

    class Provenance(BaseModel):
        enabled: bool = True
        include_prompt: bool = True
        include_raw_response: bool = True
        include_thinking_text: bool = True
        include_usage: bool = True

    results: Results = Field(default_factory=Results)
    provenance: Provenance = Field(default_factory=Provenance)


class TargetConfig(BaseModel):
    provider: str
    model: str
    temperature: Optional[float] = None
    seed: Optional[int] = None
    max_tokens: Optional[int] = None
    thinking: Optional[ThinkingOptions] = None


class TargetSetConfig(BaseModel):
    name: str
    targets: List[TargetConfig]


class DatasetConfig(BaseModel):
    path: str
    skip_rows: int = 1
    limit_rows: Optional[int] = None


class PromptFixedConfig(BaseModel):
    render_policy: Literal["fixed"] = "fixed"
    representation: Representation
    template: str
    prompt_profile: PromptProfile = PromptProfile.direct
    response_style: ResponseStyle = ResponseStyle.answer_only
    answer_format: AnswerFormat
    variables: Dict[str, Any] = Field(default_factory=dict)


class PromptMatchFormulaConfig(BaseModel):
    render_policy: Literal["match_formula"] = "match_formula"
    prompt_profile: PromptProfile = PromptProfile.direct
    response_style: ResponseStyle = ResponseStyle.answer_only

    class Branch(BaseModel):
        representation: Representation
        template: str
        answer_format: AnswerFormat
        variables: Dict[str, Any] = Field(default_factory=dict)

    horn: Branch
    nonhorn: Branch


PromptingConfig = Union[PromptFixedConfig, PromptMatchFormulaConfig]


class ParseConfig(BaseModel):
    # Optional explicit parser config; runner can derive from answer_format.
    yes_tokens: Optional[List[str]] = None
    no_tokens: Optional[List[str]] = None


class SuiteConfig(BaseModel):
    name: str
    description: Optional[str] = None

    task: Task = Task.sat_decision
    subset: Subset = Subset.mixed

    dataset: DatasetConfig
    prompting: PromptingConfig
    parse: ParseConfig = Field(default_factory=ParseConfig)

    # Targets: either inline list or reference(s) to target-set YAMLs
    targets: Optional[List[TargetConfig]] = None
    targets_ref: Optional[List[str]] = None

    # Run outputs
    output_pattern: str = "runs/${name}/${run}/${provider}/${model}/${thinking_mode}/results.jsonl"
    resume: bool = True
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)
    concurrency: ConcurrencySettings = Field(default_factory=ConcurrencySettings)


