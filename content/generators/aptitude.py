"""Aptitude question generator (quant + reasoning) with exact Python oracles."""

import math
import random

from content.generators.base import GeneratedQuestion, make_question


def _nums(ans: int) -> list[str]:
    """Four small, distinct, numerically sane distractors for an integer answer."""
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


def generate_aptitude_questions(count: int = 96, seed: int = 201) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    out: list[GeneratedQuestion] = []
    idx = 0

    def add(gk, sub, diff, prompt, ans, distractors, explanation):
        nonlocal idx
        idx += 1
        if ans.lower() not in explanation.lower():
            explanation = f"{explanation} The correct answer is {ans}."
        out.append(
            make_question(
                id_str=f"gen-apt-{idx:03d}",
                topic="aptitude",
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

    # 1. Percentages
    for base, pct in [(450, 18), (800, 35), (240, 25), (600, 15)]:
        ans = base * pct // 100
        add(
            "aptitude.percentages", "percentages", "Easy",
            f"What is {pct}% of {base}? Give only the number.",
            str(ans), _nums(ans),
            f"{pct}% of {base} = {base} * {pct}/100 = {ans}.",
        )

    # 2. Profit & loss
    for cp, pct, profit in [(200, 15, True), (500, 12, False), (800, 20, True), (1200, 25, True)]:
        ans = cp * (100 + pct) // 100 if profit else cp * (100 - pct) // 100
        kind = "profit" if profit else "loss"
        add(
            "aptitude.profit_loss", "profit-loss", "Easy",
            f"An article with cost price Rs. {cp} is sold at a {pct}% {kind}. "
            "What is the selling price? Give only the number.",
            str(ans), _nums(ans),
            f"Selling price = {cp} * (100 {'+' if profit else '-'} {pct})/100 = {ans}.",
        )

    # 3. Simple interest
    for principal, rate, years in [(1000, 5, 3), (2500, 8, 2), (4000, 6, 5), (1500, 10, 4)]:
        ans = principal * rate * years // 100
        add(
            "aptitude.simple_interest", "simple-interest", "Easy",
            f"Find the simple interest on Rs. {principal} at {rate}% per annum for {years} years. "
            "Give only the number.",
            str(ans), _nums(ans),
            f"Simple interest = {principal} * {rate} * {years}/100 = {ans}.",
        )

    # 4. Compound interest
    for principal, rate in [(1000, 10), (2000, 5), (5000, 4), (10000, 10)]:
        ans = int(round(principal * ((1 + rate / 100) ** 2 - 1)))
        add(
            "aptitude.compound_interest", "compound-interest", "Medium",
            f"Find the compound interest on Rs. {principal} at {rate}% per annum for 2 years, "
            "compounded annually. Give only the number.",
            str(ans), _nums(ans),
            f"CI = {principal} * ((1 + {rate}/100)^2 - 1) = {ans}.",
        )

    # 5. Ratios & proportions
    ratio_cases = [
        ("If A:B = 2:3 and B:C = 4:5, what is A:C?", "8:15", ["2:5", "6:5", "8:9", "4:15"],
         "A:C = (2*4):(3*5) = 8:15."),
        ("Divide 900 in the ratio 4:5. What is the first part?", "400", ["450", "360", "500", "480"],
         "First part = 900 * 4/9 = 400."),
        ("If 3:5 = x:20, what is x?", "12", ["15", "10", "18", "16"],
         "x = 20 * 3/5 = 12."),
        ("Two numbers are in the ratio 3:4 and their sum is 140. What is the larger number?",
         "80", ["60", "70", "84", "100"], "Numbers are 60 and 80; the larger is 80."),
    ]
    for prompt, ans, dis, exp in ratio_cases:
        add("aptitude.ratios_proportions", "ratios-proportions", "Medium", prompt, ans, dis, exp)

    # 6. Mixtures & alligations
    for prompt, ans, dis, exp in [
        ("Milk and water are in the ratio 4:1 in 40 litres. How much water must be added to make "
         "the ratio 2:1? Give only the number.", "8", ["6", "10", "12", "16"],
         "Milk is 32 L and water is 8 L; 32/(8+x) = 2 gives x = 8."),
        ("10 litres of a 20% solution is mixed with 30 litres of a 40% solution. What is the "
         "resulting concentration? Give only the number.", "35", ["30", "40", "25", "32"],
         "Solute = 2 + 12 = 14 L in 40 L, so concentration = 14/40 = 35%."),
        ("200 kg costing Rs. 15 per kg is mixed with 100 kg costing Rs. 30 per kg. What is the "
         "average cost per kg? Give only the number.", "20", ["22", "18", "25", "24"],
         "Average cost = (200*15 + 100*30)/300 = 6000/300 = 20."),
        ("Two ingredients costing Rs. 10 and Rs. 20 per kg are mixed to get a mean price of Rs. 14. "
         "What is the ratio of cheap to dear ingredient?", "3:2", ["2:3", "4:3", "3:4", "5:2"],
         "Alligation gives (20-14):(14-10) = 6:4 = 3:2."),
    ]:
        add("aptitude.mixtures_alligations", "mixtures-alligations", "Hard", prompt, ans, dis, exp)

    # 7. Averages
    for ans, prompt, dis, exp in [
        (6, "Find the average of 2, 4, 6, 8 and 10. Give only the number.",
         ["5", "7", "8", "4"], "Sum 30 divided by 5 gives 6."),
        (4, "Find the average of the first 7 natural numbers. Give only the number.",
         ["3", "5", "6", "4.5"], "Sum 28 divided by 7 gives 4."),
        (15, "The average of 5 numbers is 20. If one number, 40, is removed, what is the "
         "average of the rest? Give only the number.", ["18", "16", "12", "10"],
         "Total 100, remaining 60 over 4 numbers gives 15."),
        (36, "Four items average 30 and six items average 40. What is the combined average? "
         "Give only the number.", ["35", "34", "38", "37"],
         "Weighted total (4*30 + 6*40)/10 = 360/10 = 36."),
    ]:
        add("aptitude.averages", "averages", "Easy", prompt, str(ans), dis, exp)

    # 8. Time, speed & distance
    for prompt, ans, dis, exp in [
        ("A car covers 180 km in 3 hours. Find its speed in km/h. Give only the number.",
         "60", ["90", "45", "54", "72"], "Speed = 180/3 = 60 km/h."),
        ("How long does it take to cover 120 km at 40 km/h? Give only the number of hours.",
         "3", ["4", "2", "5", "6"], "Time = 120/40 = 3 hours."),
        ("A runner moves at 15 m/s for 20 seconds. How far does he travel in metres? Give only the number.",
         "300", ["250", "350", "280", "320"], "Distance = 15 * 20 = 300 m."),
        ("Convert 72 km/h to m/s. Give only the number.",
         "20", ["18", "25", "24", "22"], "72 km/h = 72 * 5/18 = 20 m/s."),
    ]:
        add("aptitude.time_speed_distance", "time-speed-distance", "Easy", prompt, ans, dis, exp)

    # 9. Trains & boats
    for prompt, ans, dis, exp in [
        ("A 150 m train crosses a pole in 10 seconds. Find its speed in km/h. Give only the number.",
         "54", ["48", "60", "45", "72"], "Speed = 150/10 = 15 m/s = 15*18/5 = 54 km/h."),
        ("A 200 m train travelling at 20 m/s crosses a 300 m bridge. How many seconds does it take?",
         "25", ["15", "20", "30", "10"], "Distance = 200 + 300 = 500 m, time = 500/20 = 25 s."),
        ("A boat's downstream speed is 20 km/h and upstream speed is 12 km/h. Find the speed of the "
         "boat in still water. Give only the number.", "16", ["14", "18", "8", "12"],
         "Still-water speed = (20 + 12)/2 = 16 km/h."),
        ("A boat covers 36 km downstream in 3 hours and 24 km upstream in 4 hours. Find the speed "
         "of the stream. Give only the number.", "3", ["4", "5", "6", "2"],
         "Downstream 12 km/h, upstream 6 km/h, stream = (12 - 6)/2 = 3 km/h."),
    ]:
        add("aptitude.trains_boats", "trains-boats", "Medium", prompt, ans, dis, exp)

    # 10. Time & work
    for a, b in [(6, 12), (10, 15), (12, 24), (20, 30)]:
        days = round(1 / (1 / a + 1 / b), 2)
        ans_s = f"{days:g}"
        add(
            "aptitude.time_work", "time-work", "Medium",
            f"A finishes a job in {a} days and B in {b} days. Working together, how many days do "
            "they take? Give only the number.",
            ans_s, _nums(int(days)),
            f"Combined rate 1/{a} + 1/{b} per day gives {days} days.",
        )

    # 11. Pipes & cisterns
    for a, b in [(4, 12), (6, 12), (10, 15), (12, 24)]:
        hours = round(1 / (1 / a + 1 / b), 2)
        ans_s = f"{hours:g}"
        add(
            "aptitude.pipes_cisterns", "pipes-cisterns", "Medium",
            f"Pipe A fills a tank in {a} hours and pipe B in {b} hours. If both are opened "
            "together, how many hours fill the tank? Give only the number.",
            ans_s, [f"{hours + 1:g}", f"{hours + 2:g}", f"{hours + 3:g}", f"{hours + 5:g}"],
            f"Net rate 1/{a} + 1/{b} per hour fills the tank in {hours} hours.",
        )

    # 12. Permutations
    for n, r in [(5, 3), (6, 2), (7, 3), (8, 2)]:
        ans = math.perm(n, r)
        add(
            "aptitude.permutations", "permutations", "Medium",
            f"Compute the number of permutations P({n}, {r}) = {n}P{r}. Give only the number.",
            str(ans), _nums(ans), f"{n}P{r} = {n}!/({n}-{r})! = {ans}.",
        )

    # 13. Combinations
    for n, r in [(5, 2), (6, 3), (7, 2), (8, 4)]:
        ans = math.comb(n, r)
        add(
            "aptitude.combinations", "combinations", "Medium",
            f"Compute the number of combinations C({n}, {r}) = {n}C{r}. Give only the number.",
            str(ans), _nums(ans), f"{n}C{r} = {n}!/({r}!*({n}-{r})!) = {ans}.",
        )

    # 14. Probability
    for prompt, ans, dis, exp in [
        ("A fair coin is tossed 3 times. What is the probability of getting exactly 2 heads?",
         "3/8", ["1/8", "1/2", "1/4", "5/8"], "Favourable C(3,2)=3 of 8 outcomes, so 3/8."),
        ("A fair die is rolled once. What is the probability of getting an even number?",
         "1/2", ["1/3", "1/6", "2/3", "1/4"], "Three even faces of six give 1/2."),
        ("A bag has 5 red and 3 blue balls. Two are drawn without replacement. What is the "
         "probability both are red?", "5/14", ["10/28", "3/14", "5/28", "1/2"],
         "C(5,2)/C(8,2) = 10/28 = 5/14."),
        ("Two fair coins are tossed. What is the probability that both show heads?",
         "1/4", ["1/2", "1/3", "1/8", "3/4"], "One favourable outcome of four gives 1/4."),
    ]:
        add("aptitude.probability", "probability", "Medium", prompt, ans, dis, exp)

    # 15. LCM & HCF
    for kind, a, b in [("LCM", 12, 18), ("HCF", 12, 18), ("LCM", 8, 12), ("HCF", 24, 36)]:
        ans = math.lcm(a, b) if kind == "LCM" else math.gcd(a, b)
        add(
            "aptitude.lcm_hcf", "number-system", "Easy",
            f"Find the {kind} of {a} and {b}. Give only the number.",
            str(ans), _nums(ans), f"{kind}({a}, {b}) = {ans}.",
        )

    # 16. Divisibility & remainders
    for prompt, ans, dis, exp in [
        ("Find the smallest number divisible by 12, 18 and 24. Give only the number.",
         str(math.lcm(12, 18, 24)), ["36", "48", "144", "216"],
         "The number is LCM(12,18,24) = 72."),
        ("Find the remainder when 17^3 is divided by 5. Give only the number.",
         str(pow(17, 3, 5)), ["2", "4", "1", "0"], "17 mod 5 is 2 and 2^3 mod 5 is 3."),
        ("Find the HCF of 36 and 60. Give only the number.", str(math.gcd(36, 60)),
         ["6", "18", "24", "12"], "HCF(36, 60) = 12."),
        ("Find the smallest number that leaves remainder 2 when divided by 5, 7 and 9. "
         "Give only the number.", str(math.lcm(5, 7, 9) + 2), ["107", "158", "212", "632"],
         "LCM(5,7,9) = 315, so the number is 315 + 2 = 317."),
    ]:
        add("aptitude.divisibility_remainders", "number-system", "Medium", prompt, ans, dis, exp)

    # 17. Number series
    for seq, ans, dis, exp, diff in [
        ("2, 6, 12, 20, 30, ?", "42", ["40", "44", "36", "38"],
         "Differences are 4, 6, 8, 10, 12, so the next term is 42.", "Easy"),
        ("1, 4, 9, 16, 25, ?", "36", ["35", "49", "30", "37"],
         "The series is n^2, so the next term is 6^2 = 36.", "Easy"),
        ("3, 9, 27, 81, ?", "243", ["162", "324", "244", "242"],
         "Each term is multiplied by 3, so the next term is 243.", "Easy"),
        ("1, 1, 2, 3, 5, 8, ?", "13", ["12", "14", "11", "16"],
         "Fibonacci: 5 + 8 = 13.", "Medium"),
    ]:
        add("aptitude.number_series", "number-series", diff, f"Find the next term: {seq}",
            ans, dis, exp)

    # 18. Syllogisms
    for prompt, ans, dis, exp in [
        ("All pens are books. All books are papers. Which conclusion always follows?",
         "All pens are papers", ["All papers are pens", "Some books are not papers", "No pen is paper"],
         "Universal affirmative statements are transitive."),
        ("No cats are dogs. Some dogs are pets. Which conclusion follows?",
         "Some pets are not cats", ["All pets are cats", "No pets are cats", "All dogs are cats"],
         "The dogs that are pets cannot be cats."),
        ("Some roses are red. All red things are bright. Which conclusion follows?",
         "Some roses are bright", ["All roses are bright", "No rose is bright", "All bright things are roses"],
         "The red roses inherit the brightness of all red things."),
        ("Some flying things are insects. Which conclusion is definitely true?",
         "Some insects fly", ["All insects fly", "No insect flies", "All flying things are insects"],
         "The statement directly asserts an overlap between insects and flying things."),
    ]:
        add("aptitude.syllogisms", "syllogisms", "Medium", prompt, ans, dis, exp)

    # 19. Blood relations
    for prompt, ans, dis, exp in [
        ("A is B's brother and B is C's mother. What is A to C?",
         "Maternal uncle", ["Father", "Paternal uncle", "Grandfather"],
         "A is the brother of C's mother."),
        ("Pointing to a man, a woman said, 'His mother is the only daughter of my mother.' "
         "How is the woman related to the man?", "Mother", ["Sister", "Aunt", "Grandmother"],
         "The only daughter of her mother is the woman herself."),
        ("X's father has only one son. Y is that son's wife. How is Y related to X?",
         "Wife", ["Mother", "Sister", "Daughter"], "The only son is X, so Y is X's wife."),
        ("P is Q's sister and R is P's father. What is R to Q?",
         "Father", ["Brother", "Uncle", "Grandfather"], "R is the father of both siblings."),
    ]:
        add("aptitude.blood_relations", "blood-relations", "Medium", prompt, ans, dis, exp)

    # 20. Direction sense
    for prompt, ans, dis, exp in [
        ("A man walks 3 km north and then 4 km east. How far is he from the start?",
         "5 km", ["7 km", "6 km", "4 km"], "By Pythagoras, sqrt(3^2 + 4^2) = 5 km."),
        ("A person faces north and turns right twice. Which direction do they face?",
         "South", ["East", "West", "North"], "Two right turns from north give south."),
        ("Ravi walks 10 m south, turns left and walks 10 m, then turns left and walks 10 m. "
         "Where is he relative to the start?", "10 m east", ["10 m west", "10 m north", "20 m east"],
         "He ends 10 m east of the starting point."),
        ("A man faces west. He turns 90 degrees clockwise and then another 90 degrees clockwise. "
         "Which direction does he face?", "East", ["North", "South", "West"],
         "Two clockwise turns from west give east."),
    ]:
        add("aptitude.direction_sense", "direction-sense", "Easy", prompt, ans, dis, exp)

    # 21. Coding-decoding
    for prompt, ans, dis, exp in [
        ("If TODAY is coded as UQEBZ by shifting every letter one place forward, how is WATER coded?",
         "XBUFS", ["XBVFT", "WAUFS", "XATFS"], "Each letter advances by one: W->X, A->B, T->U, E->F, R->S."),
        ("If CAT is coded as DBU, how is DOG coded?", "EPH", ["EPI", "CNF", "DOH"],
         "Each letter advances by one."),
        ("If MANGO is coded as NBOHP, how is APPLE coded?", "BQQMF", ["BQQNF", "APQMF", "BOPMF"],
         "Each letter advances by one."),
        ("If a word's code is the sum of letter positions (A=1), what is the code for BLUE?",
         "40", ["38", "42", "36"], "B=2, L=12, U=21, E=5, summing to 40."),
    ]:
        add("aptitude.coding_decoding", "coding-decoding", "Medium", prompt, ans, dis, exp)

    # 22. Seating & ranking
    for prompt, ans, dis, exp in [
        ("In a row of 25, Ravi is 9th from the left. What is his position from the right?",
         "17th", ["16th", "15th", "18th"], "25 - 9 + 1 = 17th."),
        ("A is 12th from the left and 18th from the right in a row. How many people are in the row?",
         "29", ["30", "28", "31"], "12 + 18 - 1 = 29."),
        ("In a queue of 30 people, Ravi is 10th from the front. What is his position from the back?",
         "21st", ["20th", "19th", "22nd"], "30 - 10 + 1 = 21st."),
        ("Priya ranks 8th from the top among 20 students. What is her rank from the bottom?",
         "13th", ["12th", "14th", "11th"], "20 - 8 + 1 = 13th."),
    ]:
        add("aptitude.seating_ranking", "seating-ranking", "Easy", prompt, ans, dis, exp)

    # 23. Clocks & calendars
    for prompt, ans, dis, exp, diff in [
        ("What is the angle between the hour and minute hands at 3:00?",
         "90 degrees", ["60 degrees", "120 degrees", "30 degrees"],
         "Each hour mark is 30 degrees; at 3:00 the hands are 3 marks apart.", "Easy"),
        ("What is the angle between the hour and minute hands at 4:00?",
         "120 degrees", ["90 degrees", "150 degrees", "60 degrees"],
         "At 4:00 the hands are 4 marks apart, each worth 30 degrees.", "Easy"),
        ("How many times do the hour and minute hands coincide in 24 hours?",
         "22", ["24", "12", "23"], "The hands overlap 11 times in 12 hours, so 22 times a day.", "Medium"),
        ("If 1 January 2024 was a Monday, what day was 1 January 2025?",
         "Wednesday", ["Tuesday", "Thursday", "Sunday"],
         "2024 is a leap year of 366 days, shifting the day by two.", "Medium"),
    ]:
        add("aptitude.clocks_calendars", "clocks-calendars", diff, prompt, ans, dis, exp)

    # 24. Data interpretation
    for prompt, ans, dis, exp in [
        ("Daily sales were 40, 60 and 50 on Monday, Tuesday and Wednesday. What was the average "
         "daily sale? Give only the number.", "50", ["45", "55", "60", "48"],
         "Average = (40 + 60 + 50)/3 = 50."),
        ("In a survey of 800 students, 25% chose Mathematics. How many chose Mathematics? "
         "Give only the number.", "200", ["250", "180", "225", "160"],
         "25% of 800 = 200."),
        ("Three categories have values A=120, B=180, C=100. What percentage of the total is B? "
         "Give only the number.", "45", ["40", "50", "36", "48"],
         "Total is 400, so B is 180/400 = 45%."),
        ("Monthly sales rose from 200 to 250 units. What was the percentage growth? "
         "Give only the number.", "25", ["20", "30", "50", "15"],
         "Growth = (250 - 200)/200 = 25%."),
    ]:
        add("aptitude.data_interpretation", "data-interpretation", "Medium", prompt, ans, dis, exp)

    return out[:count]
