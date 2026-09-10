"""Base generator interface and helpers for programmatic question generation."""

import hashlib
import random
import re
from dataclasses import dataclass
from typing import Literal


def compute_content_hash(text: str) -> str:
    """Compute sha256 of lowercase whitespace-normalized text."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


@dataclass
class GeneratedQuestion:
    id: str
    topic: str
    subtopic: str
    difficulty: Literal["Easy", "Medium", "Hard"]
    prompt: str
    options: list[str]
    correct_index: int
    explanation: str
    source: Literal["curated", "generated"]
    generator_key: str
    content_hash: str
    review_status: Literal["draft", "verified"] = "verified"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "difficulty": self.difficulty,
            "qtype": "mcq",
            "prompt": self.prompt,
            "options": self.options,
            "correct_index": self.correct_index,
            "explanation": self.explanation,
            "source": self.source,
            "generator_key": self.generator_key,
            "content_hash": self.content_hash,
            "review_status": self.review_status,
        }


def make_question(
    id_str: str,
    topic: str,
    subtopic: str,
    difficulty: Literal["Easy", "Medium", "Hard"],
    prompt: str,
    correct_answer: str,
    distractors: list[str],
    explanation: str,
    generator_key: str,
    rng: random.Random,
) -> GeneratedQuestion:
    """Build a validated GeneratedQuestion with shuffled options and computed hash."""
    clean_correct = correct_answer.strip()
    clean_distractors = sorted({d.strip() for d in distractors if d.strip() != clean_correct})
    if len(clean_distractors) < 3:
        raise ValueError(f"Need at least 3 distinct distractors for question {id_str}. Got: {distractors}")

    chosen_distractors = rng.sample(clean_distractors, 3)
    options = [clean_correct] + chosen_distractors
    rng.shuffle(options)
    correct_index = options.index(clean_correct)

    content_hash = compute_content_hash(prompt)

    return GeneratedQuestion(
        id=id_str,
        topic=topic,
        subtopic=subtopic,
        difficulty=difficulty,
        prompt=prompt,
        options=options,
        correct_index=correct_index,
        explanation=explanation,
        source="generated",
        generator_key=generator_key,
        content_hash=content_hash,
        review_status="verified",
    )
