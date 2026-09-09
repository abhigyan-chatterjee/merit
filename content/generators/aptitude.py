"""Aptitude question generator (quant, logical reasoning, verbal) with exact oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


def usable_hosts_oracle(prefix: int) -> int:
    return (2 ** (32 - prefix)) - 2


def train_meet_oracle(d1: int, s1: int, d2: int, s2: int) -> int:
    """Two trains apart by d1+d2 km approaching at s1+s2 km/h; meet time in minutes."""
    return round(((d1 + d2) / (s1 + s2)) * 60)


def work_time_oracle(a_days: int, b_days: int) -> float:
    """A does job in a_days, B in b_days; together in days (1-decimal)."""
    return round(1 / (1 / a_days + 1 / b_days), 1)


def generate_aptitude_questions(count: int = 100, seed: int = 201) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # 1. Percentages / profit-loss (oracle: arithmetic)
    pct_cases = [
        ("A shopkeeper marks goods 40% above cost and gives a 10% discount. Net profit?", 26, "%", "Easy"),
        ("A number increased by 20% then decreased by 20%. Net change?", -4, "%", "Easy"),
        ("An article sold for Rs. 720 at 20% profit. Cost price?", 600, "Rs.", "Easy"),
        ("If A's salary is 25% more than B's, B's is what % less than A's?", 20, "%", "Medium"),
        ("A value 30% of X equals 60. X?", 200, "", "Easy"),
    ]
    for prompt, ans, unit, diff in pct_cases:
        suffix = f" {unit}" if unit else ""
        ans_s = f"{ans}{suffix}"
        distractors = [f"{ans + 5}{suffix}", f"{ans - 5}{suffix}", f"{ans + 10}{suffix}", f"{ans * 2}{suffix}"]
        questions.append(
            make_question(
                id_str=f"gen-apt-pct-{q_idx}",
                topic="aptitude",
                subtopic="percentages",
                difficulty=diff,  # type: ignore[arg-type]
                prompt=f"{prompt} Give only the number{suffix}.",
                correct_answer=ans_s,
                distractors=distractors,
                explanation=f"Direct percentage arithmetic gives {ans_s}.",
                generator_key="aptitude.percentages",
                rng=rng,
            )
        )
        q_idx += 1

    # 2. Time-speed-distance (oracle: meet time)
    tsd_cases = [
        (100, 40, 100, 60),
        (120, 30, 80, 50),
        (60, 20, 60, 40),
        (150, 50, 150, 70),
        (90, 45, 90, 45),
    ]
    for d1, s1, d2, s2 in tsd_cases:
        mins = train_meet_oracle(d1, s1, d2, s2)
        ans_s = f"{mins} minutes"
        distractors = [f"{mins + 10} minutes", f"{mins - 10} minutes", f"{mins + 30} minutes"]
        questions.append(
            make_question(
                id_str=f"gen-apt-tsd-{q_idx}",
                topic="aptitude",
                subtopic="time-speed-distance",
                difficulty="Medium",  # type: ignore[arg-type]
                prompt=(
                    f"Two stations are {d1 + d2} km apart. Trains leave toward each other at "
                    f"{s1} km/h and {s2} km/h. After how long do they meet?"
                ),
                correct_answer=ans_s,
                distractors=distractors,
                explanation=f"Relative speed {s1 + s2} km/h over {d1 + d2} km gives {mins} minutes.",
                generator_key="aptitude.tsd",
                rng=rng,
            )
        )
        q_idx += 1

    # 3. Time-work (oracle: harmonic combination)
    work_cases = [(10, 15), (12, 18), (8, 24), (6, 12), (20, 30)]
    for a, b in work_cases:
        days = work_time_oracle(a, b)
        ans_s = f"{days} days"
        distractors = [f"{round((a + b) / 2, 1)} days", f"{a} days", f"{a + 1} days"]
        questions.append(
            make_question(
                id_str=f"gen-apt-work-{q_idx}",
                topic="aptitude",
                subtopic="time-work",
                difficulty="Medium",  # type: ignore[arg-type]
                prompt=f"A finishes a job in {a} days, B in {b} days. Together, how long?",
                correct_answer=ans_s,
                distractors=distractors,
                explanation=f"Combined rate 1/{a} + 1/{b} per day gives {days} days.",
                generator_key="aptitude.work",
                rng=rng,
            )
        )
        q_idx += 1

    # 4. Number series (oracle: closed-form next term)
    series_cases = [
        ("2, 6, 12, 20, 30, ?", "42", "Differences 4, 6, 8, 10, 12 (n(n+1) pattern).", "Easy"),
        ("1, 1, 2, 3, 5, 8, ?", "13", "Fibonacci: each term sums the previous two.", "Easy"),
        ("3, 9, 27, 81, ?", "243", "Powers of 3.", "Easy"),
        ("1, 4, 9, 16, 25, ?", "36", "Perfect squares n^2.", "Easy"),
        ("2, 3, 5, 7, 11, ?", "13", "Prime numbers in order.", "Medium"),
        ("5, 11, 23, 47, ?", "95", "Each term is 2x + 1.", "Medium"),
    ]
    for seq, ans, why, diff in series_cases:
        distractors = [str(int(ans) + 1), str(int(ans) - 1), str(int(ans) + 2)]
        questions.append(
            make_question(
                id_str=f"gen-apt-series-{q_idx}",
                topic="aptitude",
                subtopic="number-series",
                difficulty=diff,  # type: ignore[arg-type]
                prompt=f"Find the next term: {seq}",
                correct_answer=ans,
                distractors=distractors,
                explanation=why,
                generator_key="aptitude.series",
                rng=rng,
            )
        )
        q_idx += 1

    # 5. Logical reasoning: syllogisms, directions, blood relations
    logic_cases = [
        (
            "All A are B. All B are C. Which conclusion always follows?",
            "All A are C",
            ["All C are A", "Some B are not C", "No A is C"],
            "Transitivity of universal affirmatives: A ⊆ B ⊆ C.",
            "Easy",
        ),
        (
            "A man walks 3 km north, then 4 km east. How far is he from the start?",
            "5 km",
            ["6 km", "7 km", "4 km"],
            "3-4-5 right triangle by Pythagoras.",
            "Easy",
        ),
        (
            "Pointing to a photo, Ram says 'She is the daughter of my grandfather's only son'. Who is she?",
            "Ram's sister",
            ["Ram's mother", "Ram's aunt", "Ram's cousin"],
            "Grandfather's only son is Ram's father; his daughter is Ram's sister.",
            "Medium",
        ),
        (
            "If SOME pens are books and ALL books are chairs, which follows?",
            "Some pens are chairs",
            ["All pens are chairs", "No pen is a chair", "All chairs are pens"],
            "The pens that are books inherit book properties, including being chairs.",
            "Medium",
        ),
        (
            "A is B's brother. B is C's mother. What is A to C?",
            "Maternal uncle",
            ["Father", "Brother", "Grandfather"],
            "A is the brother of C's mother, hence maternal uncle.",
            "Easy",
        ),
    ]
    for prompt, ans, distractors, exp, diff in logic_cases:
        questions.append(
            make_question(
                id_str=f"gen-apt-logic-{q_idx}",
                topic="aptitude",
                subtopic="logical-reasoning",
                difficulty=diff,  # type: ignore[arg-type]
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="aptitude.logic",
                rng=rng,
            )
        )
        q_idx += 1

    # 6. Ratios, averages, mixtures (oracle: arithmetic)
    misc_cases = [
        ("The average of 5 consecutive even numbers starting at 10 is?", "14", ["12", "15", "16"], "Mean of symmetric sequence equals the middle term 14.", "Easy"),
        ("A:B = 2:3 and B:C = 4:5. A:C?", "8:15", ["2:5", "6:5", "8:9"], "A:C = (2*4):(3*5) = 8:15.", "Medium"),
        ("A mixture has milk:water 5:1. After adding 6L water, ratio is 5:2. Original milk?", "30 litres", ["24 litres", "36 litres", "25 litres"], "Milk unchanged: 5x milk, water x+6=2x gives x=6, milk=30L.", "Medium"),
    ]
    for prompt, ans, distractors, exp, diff in misc_cases:
        questions.append(
            make_question(
                id_str=f"gen-apt-misc-{q_idx}",
                topic="aptitude",
                subtopic="ratios-averages",
                difficulty=diff,  # type: ignore[arg-type]
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key="aptitude.misc",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
