from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class RetrySettings(BaseModel):
    max_attempts: int = 3
    backoff_seconds: List[int] = Field(default_factory=lambda: [2, 5, 10])


class ConcurrencySettings(BaseModel):
    workers: int = 4
    targets_workers: int = 1
    lockstep: bool = False
    rate_limit_per_min: Optional[int] = None
    retry: RetrySettings = Field(default_factory=RetrySettings)


class ParseConfig(BaseModel):
    type: Literal["yes_no", "contradiction"] = "yes_no"
    yes_tokens: Optional[List[str]] = None
    no_tokens: Optional[List[str]] = None


class PromptConfig(BaseModel):
    template: str
    style: Optional[str] = None  # e.g., horn_if_then | cnf_v1 | cnf_v2
    variables: Dict[str, Any] = Field(default_factory=dict)


class FiltersConfig(BaseModel):
    horn_only: bool = False
    skip_rows: int = 0
    limit_rows: Optional[int] = None


class SingleTarget(BaseModel):
    provider: str
    model: str
    temperature: float = 0.0
    seed: Optional[int] = None
    max_tokens: Optional[int] = None


class RunConfig(BaseModel):
    name: str

    # Either single-target or multitarget via `targets`
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    seed: Optional[int] = None
    max_tokens: Optional[int] = None
    targets: Optional[List[SingleTarget]] = None

    input_file: str
    output_file: Optional[str] = None
    output_pattern: Optional[str] = None

    filters: FiltersConfig = Field(default_factory=FiltersConfig)
    prompt: PromptConfig
    parse: ParseConfig = Field(default_factory=ParseConfig)
    concurrency: ConcurrencySettings = Field(default_factory=ConcurrencySettings)
    resume: bool = True
    save_prompt: bool = False
    save_response: bool = True
    # When true, writes a parallel <base>.responses.jsonl file with full text and raw metadata
    save_full_responses_file: bool = False

    # Unified outputs configuration (preferred)
    class OutputsResults(BaseModel):
        enabled: bool = True

    class OutputsProvenance(BaseModel):
        enabled: bool = False
        include_prompt: bool = True
        include_raw_response: bool = True

    class Outputs(BaseModel):
        results: 'RunConfig.OutputsResults' = Field(default_factory=lambda: RunConfig.OutputsResults())
        provenance: 'RunConfig.OutputsProvenance' = Field(default_factory=lambda: RunConfig.OutputsProvenance())

    outputs: Outputs = Field(default_factory=lambda: RunConfig.Outputs())


class ProblemMeta(BaseModel):
    maxvars: Optional[int] = None
    maxlen: Optional[int] = None
    horn: Optional[int] = None
    satflag: Optional[int] = None
    proof: Optional[List[Any]] = None


class ResultRow(BaseModel):
    id: Union[int, str]
    meta: ProblemMeta = Field(default_factory=ProblemMeta)
    provider: Optional[str] = None
    model: Optional[str] = None
    # Prompt fields
    prompt: Optional[str] = None
    prompt_template: Optional[str] = None
    # Provider response fields
    completion_text: Optional[str] = None
    normalized_text: Optional[str] = None
    raw_response: Optional[Any] = None
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    parsed_answer: Optional[int] = None  # 0=yes/contradiction, 1=no/satisfiable, 2=unclear
    correct: Optional[bool] = None
    timing_ms: Optional[int] = None
    seed: Optional[int] = None
    temperature: Optional[float] = None
    error: Optional[str] = None
    error_class: Optional[str] = None


