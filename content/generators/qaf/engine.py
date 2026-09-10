"""QAF Engine: generates verified GeneratedQuestions from declarative DesignSpecs."""

import json
import random
from typing import Any

from content.generators.base import (
    GeneratedQuestion,
    compute_content_hash,
    make_question,
)
from content.generators.qaf.spec import DesignSpec, get_all_specs


def _param_signature(params: dict[str, Any]) -> str:
    """Serialize parameters (excluding id/metadata) to detect duplicates."""
    filtered = {
        k: v
        for k, v in params.items()
        if k not in ("id", "distractors", "options", "correct_index")
    }
    try:
        return json.dumps(filtered, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(sorted(filtered.items()))


def generate_instances_for_spec(
    spec: DesignSpec,
    instance_cap: int = 4,
    rng: random.Random | None = None,
) -> list[GeneratedQuestion]:
    """Generate up to instance_cap distinct GeneratedQuestions for a single DesignSpec."""
    if rng is None:
        rng = random.Random(spec.seed)

    oracle_fn = spec.resolve_oracle()
    questions: list[GeneratedQuestion] = []
    seen_signatures: set[str] = set()
    seen_prompts: set[str] = set()

    max_draws = 200
    for _ in range(max_draws):
        if len(questions) >= instance_cap:
            break

        raw_params = spec.sample(rng)
        sig = _param_signature(raw_params)
        if sig in seen_signatures:
            continue

        clean_params = {
            k: v
            for k, v in raw_params.items()
            if k not in ("id", "distractors", "options", "correct_index")
        }

        # Determine instance ID
        if "id" in raw_params:
            qid = str(raw_params["id"])
        elif spec.instance_ids and len(questions) < len(spec.instance_ids):
            qid = spec.instance_ids[len(questions)]
        else:
            prefix = spec.id_prefix or spec.key.replace(".", "-")
            qid = f"{prefix}-{len(questions) + 1}"

        # Execute oracle
        try:
            computed_answer = oracle_fn(**clean_params)
        except TypeError:
            if len(clean_params) == 1:
                computed_answer = oracle_fn(next(iter(clean_params.values())))
            else:
                raise

        answer_str = str(computed_answer).strip()

        # Render prompt
        prompt = spec.render_prompt(clean_params)
        prompt_hash = compute_content_hash(prompt)
        if prompt_hash in seen_prompts:
            continue

        # Render explanation
        explanation = spec.render_explanation(clean_params, answer_str)

        # Resolve difficulty
        difficulty = spec.resolve_difficulty(clean_params)

        # Distractors
        distractor_list = spec.resolve_distractors(
            answer_str, raw_params, rng=rng
        )

        # Shuffled options & question assembly
        q = make_question(
            id_str=qid,
            topic=spec.topic,
            subtopic=spec.subtopic,
            difficulty=difficulty,
            prompt=prompt,
            correct_answer=answer_str,
            distractors=distractor_list,
            explanation=explanation,
            generator_key=spec.key,
            rng=rng,
        )

        seen_signatures.add(sig)
        seen_prompts.add(prompt_hash)
        questions.append(q)

    return questions


def generate_all_qaf(
    specs: list[DesignSpec] | None = None,
    instance_cap: int = 4,
) -> list[GeneratedQuestion]:
    """Generate questions for all registered or specified design specs."""
    if specs is None:
        specs = get_all_specs()

    all_questions: list[GeneratedQuestion] = []
    for spec in specs:
        all_questions.extend(
            generate_instances_for_spec(spec, instance_cap=instance_cap)
        )
    return all_questions
