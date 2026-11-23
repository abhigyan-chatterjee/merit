"""SQL and verbal screening question generators with exact oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


def _nums(ans: int) -> list[str]:
    vals: list[int] = []
    for off in (2, -2, 4, 3, -4, 6, -3):
        v = ans + off
        if v >= 0 and v != ans and v not in vals:
            vals.append(v)
        if len(vals) == 4:
            break
    k = 1
    while len(vals) < 4:
        v = ans + 10 * k + 1
        if v != ans and v not in vals:
            vals.append(v)
        k += 1
    return [str(v) for v in vals]


def _emit(out, rng, idx_ref, *, prefix, topic, gk, sub, diff, prompt, ans, distractors, explanation):
    idx_ref[0] += 1
    if ans.lower() not in explanation.lower():
        explanation = f"{explanation} The correct answer is {ans}."
    out.append(
        make_question(
            id_str=f"gen-{prefix}-{idx_ref[0]:03d}",
            topic=topic,
            subtopic=sub,
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=explanation,
            generator_key=gk,
            rng=rng,
        )
    )


def generate_sql_questions(count: int = 40, seed: int = 401) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    out: list[GeneratedQuestion] = []
    idx = [0]

    def add(gk, sub, diff, prompt, ans, distractors, explanation):
        _emit(out, rng, idx, prefix="sql", topic="sql", gk=gk, sub=sub, diff=diff,
              prompt=prompt, ans=ans, distractors=distractors, explanation=explanation)

    # 1. SELECT / WHERE
    for prompt, ans, dis, exp in [
        ("A table t has rows with id 1 through 5. What does SELECT COUNT(*) FROM t WHERE id > 2 "
         "return? Give only the number.", "3", _nums(3), "IDs 3, 4 and 5 qualify, so the count is 3."),
        ("A table t has ids 1 through 5. How many rows does SELECT * FROM t WHERE id IN (2, 4) return?",
         "2", _nums(2), "Only ids 2 and 4 match, so two rows are returned."),
        ("What value does SELECT 7 + 3 AS total return?", "10", _nums(10),
         "The expression evaluates to 10."),
        ("A users table has ages 18, 22, 28 and 35. How many rows match WHERE age BETWEEN 20 AND 30?",
         "2", _nums(2), "Ages 22 and 28 are in range, so two rows match."),
    ]:
        add("sql.select_where", "select-where", "Easy", prompt, ans, dis, exp)

    # 2. GROUP BY / HAVING
    for prompt, ans, dis, exp in [
        ("Rows have dept values A, A, B, C, C, C. How many groups does GROUP BY dept produce?",
         "3", _nums(3), "There are three distinct departments, so three groups."),
        ("Rows have dept values A, A, B, C, C, C. How many groups survive HAVING COUNT(*) > 2?",
         "1", _nums(1), "Only C occurs three times, so one group survives."),
        ("Three groups have SUM(score) values 90, 120 and 100. How many pass HAVING SUM(score) >= 100?",
         "2", _nums(2), "Sums 120 and 100 qualify, so two groups pass."),
        ("Rows have dept values A, A, B, B, C, C, D, D. How many groups does GROUP BY dept produce?",
         "4", _nums(4), "There are four distinct departments."),
    ]:
        add("sql.group_having", "group-having", "Medium", prompt, ans, dis, exp)

    # 3. JOINs
    for prompt, ans, dis, exp in [
        ("A users table has 4 rows and an orders table has 6 rows, with every order referencing a "
         "user. How many rows does an INNER JOIN produce?", "6", _nums(6),
         "Every order matches one user, so the join has 6 rows."),
        ("A users table has 4 rows and an orders table has 6 rows, of which 2 orders have a NULL "
         "user_id. How many rows does an INNER JOIN produce?", "4", _nums(4),
         "Only the 4 orders with a matching user survive."),
        ("A users table has 4 rows and an orders table has 6 rows, of which 2 orders have a NULL "
         "user_id. How many rows does a LEFT JOIN from users produce?", "6", _nums(6),
         "A LEFT JOIN keeps all 6 orders that reference a user."),
        ("Table A has 3 rows and table B has 4 rows with no matching keys. How many rows does a "
         "CROSS JOIN produce?", "12", _nums(12), "Cross join is the Cartesian product 3 * 4 = 12."),
    ]:
        add("sql.joins", "joins", "Hard", prompt, ans, dis, exp)

    # 4. NULL traps
    for prompt, ans, dis, exp in [
        ("A column x holds 1, 2, NULL and 4. What does COUNT(*) return?", "4", _nums(4),
         "COUNT(*) counts every row, including the NULL one."),
        ("A column x holds 1, 2, NULL and 4. What does COUNT(x) return?", "3", _nums(3),
         "COUNT(x) ignores NULL values."),
        ("A column x holds 1, 2, NULL and 4. What does SUM(x) return?", "7", _nums(7),
         "SUM ignores NULL and adds 1 + 2 + 4 = 7."),
        ("A column x contains a NULL in one row. How many rows match WHERE x = NULL?", "0", _nums(0),
         "NULL is never equal to NULL under SQL three-valued logic."),
    ]:
        add("sql.null_traps", "nulls", "Medium", prompt, ans, dis, exp)

    # 5. UNION vs UNION ALL
    for prompt, ans, dis, exp in [
        ("Set A has 3 rows and set B has 2 rows with 1 row in common. How many rows does UNION return?",
         "4", _nums(4), "UNION removes the duplicate, giving 3 + 2 - 1 = 4 rows."),
        ("Set A has 3 rows and set B has 2 rows with 1 row in common. How many rows does UNION ALL return?",
         "5", _nums(5), "UNION ALL keeps duplicates, giving 3 + 2 = 5 rows."),
        ("Set A has 3 rows and set B has 2 rows with 1 row in common. How many rows are common to both?",
         "1", _nums(1), "Exactly one row is shared."),
        ("Set A has 3 rows and set B has 3 rows that are all identical. How many rows does UNION ALL return?",
         "6", _nums(6), "UNION ALL keeps all six rows without deduplication."),
    ]:
        add("sql.union", "set-operations", "Medium", prompt, ans, dis, exp)

    # 6. Subqueries / EXISTS / IN
    for prompt, ans, dis, exp in [
        ("Five users exist and orders reference 3 distinct users. How many rows does a query with "
         "WHERE id IN (SELECT user_id FROM orders) return?", "3", _nums(3),
         "Only the three referenced users are returned."),
        ("An EXISTS subquery finds no matching rows for any outer row. How many outer rows are returned?",
         "0", _nums(0), "No row satisfies the EXISTS predicate."),
        ("A table t holds x values 5, 9 and 2. What does SELECT (SELECT MAX(x) FROM t) return?",
         "9", _nums(9), "The maximum value is 9."),
        ("The orders table contains 4 distinct non-null user_ids. How many distinct users placed an order?",
         "4", _nums(4), "There are four distinct user_ids."),
    ]:
        add("sql.subqueries", "subqueries", "Hard", prompt, ans, dis, exp)

    # 7. Window functions
    for prompt, ans, dis, exp in [
        ("Four rows have scores 100, 90, 90, 80. What ROW_NUMBER does the last row receive?",
         "4", _nums(4), "ROW_NUMBER assigns a unique sequence, so the last row is 4."),
        ("Four rows have scores 100, 90, 90, 80. What RANK does the first row with score 90 receive?",
         "2", _nums(2), "RANK gives both 90-score rows rank 2."),
        ("Four rows have scores 100, 90, 90, 80. What DENSE_RANK does the last row receive?",
         "3", _nums(3), "DENSE_RANK yields 1, 2, 2, 3."),
        ("LAG(score) is applied to the first row of a result set. What does it return?",
         "No previous value", ["The first score", "The last score", "Zero"],
         "There is no preceding row, so LAG returns no previous value."),
    ]:
        add("sql.window_functions", "window-functions", "Hard", prompt, ans, dis, exp)

    # 8. DISTINCT / ORDER BY / LIMIT
    for prompt, ans, dis, exp in [
        ("An emp table has dept values A, A, B and C. How many rows does SELECT DISTINCT dept return?",
         "3", _nums(3), "There are three distinct departments."),
        ("A query matches 10 rows but ends with LIMIT 5. How many rows are returned?",
         "5", _nums(5), "LIMIT caps the result at 5 rows."),
        ("Values 4, 7 and 2 are sorted with ORDER BY x DESC. What is the first value?",
         "7", _nums(7), "Descending order starts with the largest value 7."),
        ("A query matches 5 rows and uses OFFSET 2 LIMIT 2. How many rows are returned?",
         "2", _nums(2), "OFFSET skips two rows and LIMIT returns two."),
    ]:
        add("sql.distinct_order_limit", "result-shaping", "Easy", prompt, ans, dis, exp)

    # 9. DML & indexes
    for prompt, ans, dis, exp in [
        ("A table has 7 rows. How many rows remain after DELETE FROM t with no WHERE clause?",
         "0", _nums(0), "DELETE without a predicate removes every row."),
        ("A table has 7 rows. How many rows remain immediately after TRUNCATE TABLE t?",
         "0", _nums(0), "TRUNCATE empties the table."),
        ("Which index structure speeds up equality lookups on a single column?",
         "B-tree index", ["Bitmap index", "Full-text index", "Hash-only index"],
         "A B-tree index supports efficient equality and range searches."),
        ("What does CREATE UNIQUE INDEX enforce on the indexed column?",
         "Distinct values", ["Automatic sorting only", "Compression", "A foreign key"],
         "A unique index rejects duplicate values."),
    ]:
        add("sql.dml_indexes", "dml-indexes", "Medium", prompt, ans, dis, exp)

    # 10. Aggregate functions
    for values, fn, ans in [([10, 20, 30], "AVG", 20), ([10, 20, 30], "MIN", 10),
                            ([10, 20, 30], "MAX", 30), ([10, 20, 30], "SUM", 60)]:
        add(
            "sql.aggregates", "aggregates", "Easy",
            f"A column holds {values}. What does SELECT {fn}(x) return? Give only the number.",
            str(ans), _nums(ans), f"{fn} of {values} is {ans}.",
        )

    return out[:count]


def generate_verbal_questions(count: int = 40, seed: int = 402) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    out: list[GeneratedQuestion] = []
    idx = [0]

    def add(gk, sub, diff, prompt, ans, distractors, explanation):
        _emit(out, rng, idx, prefix="verbal", topic="verbal", gk=gk, sub=sub, diff=diff,
              prompt=prompt, ans=ans, distractors=distractors, explanation=explanation)

    # 1. Subject-verb agreement
    for prompt, ans, dis, exp in [
        ("Fill in the blank: The list of items ___ longer than expected.", "is",
         ["are", "were", "have"], "The subject is the singular 'list', so the verb is 'is'."),
        ("Fill in the blank: The items on the list ___ longer than expected.", "are",
         ["is", "was", "has"], "The subject 'items' is plural, so the verb is 'are'."),
        ("Fill in the blank: Each of the boys ___ a new pen.", "has",
         ["have", "had been", "were having"], "Each is singular, so the verb is 'has'."),
        ("Fill in the blank: All of the boys ___ new pens.", "have",
         ["has", "is having", "was having"], "All is plural here, so the verb is 'have'."),
    ]:
        add("verbal.subject_verb_agreement", "grammar", "Easy", prompt, ans, dis, exp)

    # 2. Tense & modifier errors
    for prompt, ans, dis, exp in [
        ("Fill in the blank: By the time we arrived, the film ___.", "had started",
         ["starts", "has started", "will start"], "The past perfect 'had started' describes an earlier past event."),
        ("Fill in the blank: She ___ in this city since 2010.", "has lived",
         ["lives", "lived", "is living"], "Since with a continuing state requires the present perfect."),
        ("Fill in the blank: If I ___ you, I would accept the offer.", "were",
         ["am", "was being", "will be"], "A hypothetical condition takes the subjunctive 'were'."),
        ("Fill in the blank: The report ___ before the meeting starts.", "will be finished",
         ["finishes", "has finished", "is finishing"], "The future passive 'will be finished' fits the future deadline."),
    ]:
        add("verbal.tense_modifiers", "grammar", "Medium", prompt, ans, dis, exp)

    # 3. Sentence correction
    for prompt, ans, dis, exp in [
        ("Choose the correct version of: 'He don't like tea.'", "He doesn't like tea.",
         ["He don't likes tea.", "He didn't liked tea.", "He doesn't likes tea."],
         "A singular subject takes 'doesn't' followed by the base verb."),
        ("Choose the correct version of: 'She is more taller than me.'", "She is taller than me.",
         ["She is more taller than I.", "She is tallest than me.", "She is more tall than me."],
         "Comparative 'taller' already expresses the comparison."),
        ("Choose the correct version of: 'Each students were present.'", "Each student was present.",
         ["Each students was present.", "Each student were present.", "Each of student were present."],
         "Each takes a singular noun and a singular verb."),
        ("Choose the correct version of: 'I have seen him yesterday.'", "I saw him yesterday.",
         ["I had seen him yesterday.", "I have saw him yesterday.", "I am seeing him yesterday."],
         "A finished past time such as yesterday takes the simple past."),
    ]:
        add("verbal.sentence_correction", "grammar", "Medium", prompt, ans, dis, exp)

    # 4. Prepositions & idioms
    for prompt, ans, dis, exp in [
        ("Fill in the blank: He is very good ___ mathematics.", "at",
         ["in", "on", "with"], "The idiom is 'good at' a subject."),
        ("Fill in the blank: She has been working here ___ 2015.", "since",
         ["for", "from", "during"], "Since is used with a starting point in time."),
        ("Fill in the blank: The book is ___ the table.", "on",
         ["at", "in", "by"], "A surface contact uses the preposition 'on'."),
        ("What does the idiom 'let the cat out of the bag' mean?", "He revealed a secret",
         ["He bought a pet", "He was frightened", "He made a mistake"],
         "The idiom means to reveal a secret."),
    ]:
        add("verbal.prepositions_idioms", "vocabulary", "Easy", prompt, ans, dis, exp)

    # 5. Active / passive voice
    for prompt, ans, dis, exp in [
        ("Convert to passive voice: 'The cat chased the mouse.'", "The mouse was chased by the cat.",
         ["The mouse is chased by the cat.", "The cat was chased by the mouse.",
          "The mouse was chasing the cat."], "The object becomes the subject with 'was chased'."),
        ("Convert to passive voice: 'They are building a bridge.'", "A bridge is being built.",
         ["A bridge was being built.", "A bridge is built.", "A bridge has built."],
         "Present continuous passive uses 'is being built'."),
        ("Convert to passive voice: 'She will finish the work.'", "The work will be finished by her.",
         ["The work is finished by her.", "The work will finish by her.", "The work will be finishing."],
         "The future passive uses 'will be finished'."),
        ("Convert to passive voice: 'The teacher praised the student.'", "The student was praised by the teacher.",
         ["The student is praised by the teacher.", "The teacher was praised by the student.",
          "The student has praised the teacher."], "Simple past passive uses 'was praised'."),
    ]:
        add("verbal.active_passive", "grammar", "Medium", prompt, ans, dis, exp)

    # 6. Direct / indirect speech
    for prompt, ans, dis, exp in [
        ("Change to indirect speech: He said, 'I am busy.'", "He said that he was busy.",
         ["He said that he is busy.", "He says that he was busy.", "He said that I was busy."],
         "The present tense shifts to the past in reported speech."),
        ("Change to indirect speech: She asked, 'Where do you live?'", "She asked where I lived.",
         ["She asked where do I live.", "She asked where I live.", "She asked where did I live."],
         "Questions become statements with shifted tense."),
        ("Change to indirect speech: He said, 'I finished it yesterday.'",
         "He said that he had finished it the previous day.",
         ["He said that he finished it yesterday.", "He said that he has finished it the previous day.",
          "He said that he had finished it yesterday."], "The past shifts to past perfect and time markers change."),
        ("Change to indirect speech: They said, 'We will come tomorrow.'",
         "They said that they would come the next day.",
         ["They said that they will come tomorrow.", "They said that they would come tomorrow.",
          "They said that they will come the next day."], "Will becomes would and tomorrow becomes the next day."),
    ]:
        add("verbal.direct_indirect", "grammar", "Hard", prompt, ans, dis, exp)

    # 7. Synonyms in context
    for word, ans, dis, exp in [
        ("meticulous", "Thorough", ["Careless", "Hasty", "Vague"],
         "Meticulous means showing great attention to detail, or thorough."),
        ("laconic", "Concise", ["Wordy", "Loud", "Angry"],
         "Laconic means using very few words, or concise."),
        ("ubiquitous", "Omnipresent", ["Rare", "Temporary", "Hidden"],
         "Ubiquitous means present everywhere, or omnipresent."),
        ("candid", "Frank", ["Secretive", "Hostile", "Timid"],
         "Candid means honest and direct, or frank."),
    ]:
        add("verbal.synonyms", "vocabulary", "Medium",
            f"Choose the word closest in meaning to '{word}'.", ans, dis, exp)

    # 8. Antonyms in context
    for word, ans, dis, exp in [
        ("abundant", "Scarce", ["Plentiful", "Ample", "Generous"],
         "Abundant means plentiful, so its opposite is scarce."),
        ("beneficial", "Harmful", ["Helpful", "Useful", "Advantageous"],
         "Beneficial means helpful, so its opposite is harmful."),
        ("explicit", "Implicit", ["Clear", "Direct", "Obvious"],
         "Explicit means stated clearly, so its opposite is implicit."),
        ("fragile", "Robust", ["Delicate", "Brittle", "Frail"],
         "Fragile means easily broken, so its opposite is robust."),
    ]:
        add("verbal.antonyms", "vocabulary", "Medium",
            f"Choose the word most opposite in meaning to '{word}'.", ans, dis, exp)

    # 9. Para-jumbles
    for prompt, ans, dis, exp in [
        ("Arrange: (1) He opened the door. (2) He heard a noise. (3) He woke up. (4) He went "
         "outside. Which sentence comes first?", "He woke up.",
         ["He heard a noise.", "He opened the door.", "He went outside."],
         "Waking up must precede the other actions."),
        ("Arrange: (A) The seeds were sown. (B) The soil was prepared. (C) The plants grew. "
         "(D) It rained. Which sentence comes first?", "The soil was prepared.",
         ["The seeds were sown.", "The plants grew.", "It rained."],
         "Preparing the soil must come before sowing."),
        ("Arrange: (A) The seeds were sown. (B) The soil was prepared. (C) The plants grew. "
         "(D) It rained. Which sentence comes last?", "The plants grew.",
         ["The seeds were sown.", "The soil was prepared.", "It rained."],
         "Growth is the final outcome of the sequence."),
        ("Arrange: (1) He opened the door. (2) He heard a noise. (3) He woke up. (4) He went "
         "outside. Which sentence comes second?", "He heard a noise.",
         ["He woke up.", "He opened the door.", "He went outside."],
         "He hears the noise right after waking."),
    ]:
        add("verbal.para_jumbles", "para-jumbles", "Hard", prompt, ans, dis, exp)

    # 10. Reading comprehension inference
    for passage, question, ans, dis, exp in [
        ("Riya studied every evening for months, failed her first mock test, but revised her plan "
         "and eventually topped her class.", "What is the central message of the passage?",
         "Persistence and adaptation lead to success",
         ["Luck is the only factor in exams", "Mock tests are a waste of time", "Toppers never fail"],
         "The passage emphasizes persistence and changing the plan after failure."),
        ("When the sky darkened, Arjun grabbed an umbrella before leaving for the market.",
         "Why did Arjun take an umbrella?", "He expected rain",
         ["He wanted to shield himself from the sun", "He was carrying it for a friend",
          "The market required one"], "Darkening skies signal expected rain."),
        ("The library closed early on Fridays, so Meera finished her research at home that evening.",
         "What caused Meera to work at home?", "The library's early closure",
         ["She disliked the library", "Her laptop was faster", "The internet was down"],
         "The early Friday closure forced her to work elsewhere."),
        ("The old bridge was rebuilt using stronger steel after repeated inspections found cracks.",
         "What can be inferred about the inspections?", "They revealed safety problems",
         ["They were purely ceremonial", "They found no issues", "They were done only once"],
         "Finding cracks means the inspections uncovered safety problems."),
    ]:
        add("verbal.reading_comprehension", "reading-comprehension", "Medium",
            f"{passage} {question}", ans, dis, exp)

    return out[:count]
