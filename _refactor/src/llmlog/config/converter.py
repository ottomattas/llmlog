from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .schema import (
    AnswerFormat,
    DatasetConfig,
    ParseConfig,
    PromptFixedConfig,
    PromptProfile,
    Representation,
    ResponseStyle,
    Subset,
    SuiteConfig,
    TargetConfig,
    TargetSetConfig,
    Task,
    ThinkingOptions,
)


STYLE_TO_REPRESENTATION: Dict[str, Representation] = {
    "horn_if_then": Representation.horn_rules,
    "cnf_v1": Representation.cnf_nl,
    "cnf_v2": Representation.cnf_compact,
    # aliases seen in prose/docs
    "horn_rules": Representation.horn_rules,
    "cnf_nl": Representation.cnf_nl,
    "cnf_compact": Representation.cnf_compact,
}


PARSE_TO_ANSWER_FORMAT: Dict[str, AnswerFormat] = {
    "yes_no": AnswerFormat.yes_no,
    "contradiction": AnswerFormat.contradiction_satisfiable,
}


def _strip_refactor_prefix(path: str) -> str:
    if path.startswith("_refactor/"):
        return path[len("_refactor/") :]
    return path


def _merge_target_defaults(old_cfg: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(target)
    for key in ("temperature", "seed", "max_tokens"):
        if key not in merged and old_cfg.get(key) is not None:
            merged[key] = old_cfg.get(key)
    if "thinking" not in merged and old_cfg.get("thinking") is not None:
        merged["thinking"] = old_cfg.get("thinking")
    return merged


def _convert_thinking(thinking: Optional[Dict[str, Any]]) -> Optional[ThinkingOptions]:
    if not thinking:
        return None
    return ThinkingOptions(**thinking)


def _template_for(representation: Representation, answer_format: AnswerFormat) -> str:
    if representation == Representation.horn_rules and answer_format == AnswerFormat.yes_no:
        return "prompts/sat_decision__horn_rules__answer_only.j2"
    if representation == Representation.cnf_compact and answer_format == AnswerFormat.contradiction_satisfiable:
        return "prompts/sat_decision__cnf_compact__answer_only.j2"
    if representation == Representation.cnf_nl and answer_format == AnswerFormat.contradiction_satisfiable:
        return "prompts/sat_decision__cnf_nl__answer_only.j2"
    # Fallback to mixed prompt (rare/legacy configs); caller can override explicitly.
    return "prompts/sat_decision__mixed_interpretation__answer_only.j2"


def convert_experiments_config_dict(
    old: Dict[str, Any],
    *,
    suite_name: Optional[str] = None,
    target_set_name: Optional[str] = None,
) -> Tuple[SuiteConfig, TargetSetConfig]:
    """Convert an `experiments/configs/*.yaml` dict into `_refactor` suite+target-set configs."""
    if not isinstance(old, dict):
        raise TypeError("Expected mapping/dict for old config")

    prompt = old.get("prompt") or {}
    style = (prompt.get("style") or "").strip()
    if style not in STYLE_TO_REPRESENTATION:
        raise ValueError(f"Unsupported prompt.style={style!r} (expected one of {sorted(STYLE_TO_REPRESENTATION)})")
    representation = STYLE_TO_REPRESENTATION[style]

    parse = old.get("parse") or {}
    parse_type = (parse.get("type") or "yes_no").strip()
    if parse_type == "both":
        # Legacy "both" isn't represented as a single answer_format; keep runner-side behavior
        # by defaulting to contradiction_satisfiable (more explicit) and allowing override later.
        answer_format = AnswerFormat.contradiction_satisfiable
    else:
        if parse_type not in PARSE_TO_ANSWER_FORMAT:
            raise ValueError(f"Unsupported parse.type={parse_type!r}")
        answer_format = PARSE_TO_ANSWER_FORMAT[parse_type]

    filters = old.get("filters") or {}
    subset = Subset.hornonly if bool(filters.get("horn_only")) else Subset.mixed

    dataset = DatasetConfig(
        path=_strip_refactor_prefix(str(old.get("input_file") or "")),
        skip_rows=int(filters.get("skip_rows", 1) or 1),
        limit_rows=filters.get("limit_rows"),
    )

    # Targets
    old_targets = old.get("targets") or []
    if not isinstance(old_targets, list) or not old_targets:
        raise ValueError("Old config must contain a non-empty targets: list")

    new_targets: List[TargetConfig] = []
    for t in old_targets:
        if not isinstance(t, dict):
            raise ValueError("Each entry in targets must be a mapping")
        merged = _merge_target_defaults(old, t)
        new_targets.append(
            TargetConfig(
                provider=str(merged.get("provider")),
                model=str(merged.get("model")),
                temperature=merged.get("temperature"),
                seed=merged.get("seed"),
                max_tokens=merged.get("max_tokens"),
                thinking=_convert_thinking(merged.get("thinking")),
            )
        )

    ts_name = target_set_name or f"targets__{(suite_name or old.get('name') or 'converted')}"
    target_set = TargetSetConfig(name=ts_name, targets=new_targets)

    # Prompting
    prompting = PromptFixedConfig(
        representation=representation,
        template=_template_for(representation, answer_format),
        prompt_profile=PromptProfile.direct,
        response_style=ResponseStyle.answer_only,
        answer_format=answer_format,
        variables=dict(prompt.get("variables") or {}),
    )

    parse_cfg = ParseConfig(
        yes_tokens=parse.get("yes_tokens"),
        no_tokens=parse.get("no_tokens"),
    )

    suite = SuiteConfig(
        name=suite_name or str(old.get("name") or "converted_suite"),
        description=f"Converted from experiments config: {suite_name or old.get('name') or 'unknown'}",
        task=Task.sat_decision,
        subset=subset,
        dataset=dataset,
        prompting=prompting,
        parse=parse_cfg,
        # targets_ref is set by the file-level converter which knows output paths
        targets=new_targets,
        output_pattern=str(old.get("output_pattern") or SuiteConfig.model_fields["output_pattern"].default),
        resume=bool(old.get("resume", True)),
    )
    return suite, target_set


def write_converted_configs(
    *,
    old_config: Dict[str, Any],
    out_dir: str,
    suite_filename: Optional[str] = None,
    targets_filename: Optional[str] = None,
    overwrite: bool = False,
) -> Tuple[Path, Path]:
    """Write converted suite + target-set YAMLs under out_dir/{suites,targets}/."""
    out = Path(out_dir)
    suites_dir = out / "suites"
    targets_dir = out / "targets"
    suites_dir.mkdir(parents=True, exist_ok=True)
    targets_dir.mkdir(parents=True, exist_ok=True)

    suite_name = str(old_config.get("name") or "converted_suite")
    suite, target_set = convert_experiments_config_dict(old_config, suite_name=suite_name)

    suite_file = suites_dir / (suite_filename or f"{suite.name}.yaml")
    target_file = targets_dir / (targets_filename or f"{target_set.name}.yaml")

    if not overwrite and (suite_file.exists() or target_file.exists()):
        raise FileExistsError(f"Refusing to overwrite existing files: {suite_file} / {target_file}")

    # Make suite refer to target file relatively; avoid duplicating targets inline.
    suite.targets = None
    suite.targets_ref = [str(Path("../targets") / target_file.name)]

    import yaml

    suite_file.write_text(yaml.safe_dump(suite.model_dump(mode="json", exclude_none=True), sort_keys=False))
    target_file.write_text(yaml.safe_dump(target_set.model_dump(mode="json", exclude_none=True), sort_keys=False))
    return suite_file, target_file


