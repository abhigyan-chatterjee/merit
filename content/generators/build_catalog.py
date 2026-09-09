"""Build the canonical Algovista DSA catalog from Mimo-scraped CSVs.

Canonical source: /mnt/code/dsa_database/final/dsa_database_final.csv
(the cleaner of the two mains: only 41 junk-topic rows vs 1336 in
dsa_questions_final.csv; the 219 extra GFG/InterviewBit rows that exist
only in dsa_questions_final.csv are folded in as a supplement).

What this does:
  1. Normalizes titles (strips NeetCode '0001 - ' prefixes, lowercases,
     collapses punctuation/whitespace) and re-dedups. The scrape's own
     dedup was exact-title only, so ~400 LeetCode/NeetCode pairs survive
     as false distinct rows (e.g. 'Two Sum' + '0001 - Two Sum').
  2. Merges dup groups, preferring the LeetCode row (real difficulty +
     full company list) and unioning topics/companies.
  3. Splits combo company strings into clean per-company lists, dropping
     scraper artifacts ('Multiple Companies', 'Unknown'), normalizing
     case ('tcs' -> 'TCS'), flagging truncated rows ('+ N more').
  4. Maps the 173 raw topics onto the 6 Algovista problem topics the
     frontend actually routes on (18 categories, e.g. arrays-hashing |
     trees | graphs | dp), keeping raw topics + pattern alongside.
  5. Normalizes difficulty (MEDIUM -> Medium); blanks stay 'Unknown' --
     never invented.

Output (metadata ONLY -- no scraped statements, per the original-content
rule; titles/concepts may be classic, statements are written fresh in
the enrichment step):
  content/catalog/catalog.json      -- one entry per canonical question
  content/catalog/companies.json    -- individual company frequency
  content/catalog/topic_map.json    -- raw topic -> algovista topic map
  content/catalog/BUILD_REPORT.txt  -- human-readable build summary

Nothing here touches content/problems, content/questions or content/paths,
so seed + validators + CI are unaffected by construction.
"""

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SCRAPE_DIR = Path("/mnt/code/dsa_database/final")
CANONICAL_CSV = SCRAPE_DIR / "dsa_database_final.csv"
SUPPLEMENT_CSV = SCRAPE_DIR / "dsa_questions_final.csv"

CATALOG_DIR = REPO_ROOT / "content" / "catalog"

from content.taxonomy import (
    CATEGORY_SLUGS as ALGOVISTA_TOPICS,  # noqa: F401 (re-export)
)

COMPANY_BLOCKLIST = {"multiple companies", "unknown", ""}
COMPANY_CASE_FIXES = {
    "tcs": "TCS",
    "persistent systems": "Persistent Systems",
}
COMPANY_DROP = {"pornhub"}

DIFFICULTY_MAP = {"EASY": "Easy", "MEDIUM": "Medium", "HARD": "Hard", "": "Unknown"}


def normalize_title(title: str) -> str:
    t = (title or "").strip().lower()
    t = re.sub(r"^\d+\s*[-.:)]\s*", "", t)
    t = re.sub(r"[^a-z0-9 ]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def slugify(title: str) -> str:
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-") or "untitled"


def split_topics(raw: str) -> list[str]:
    return [t.strip() for t in (raw or "").split(",") if t.strip()]


def split_companies(raw: str) -> tuple[list[str], bool]:
    """Returns (clean companies, truncated flag)."""
    raw = (raw or "").strip()
    truncated = "more companies" in raw
    parts = [p.strip() for p in raw.split(",")]
    clean: list[str] = []
    seen: set[str] = set()
    for p in parts:
        if "more companies" in p:
            continue
        key = p.lower()
        if key in COMPANY_BLOCKLIST or key in COMPANY_DROP:
            continue
        label = COMPANY_CASE_FIXES.get(key, p)
        if label not in seen:
            seen.add(label)
            clean.append(label)
    return clean, truncated


# Raw topic -> 18-category slug. Checked in priority order per entry:
# linked-lists > trees > graphs > dynamic-programming > sliding-windows,
# else arrays-hashing.
RAW_TOPIC_MAP: dict[str, str] = {
    "Linked Lists": "linked-lists",
    "Floyd's Cycle Finding Algorithm": "linked-lists",
    "Trees": "trees",
    "BST": "trees",
    "Trie": "trie",
    "DP on Trees": "trees",
    "Lowest Common Ancestor": "trees",
    "Cartesian Tree": "trees",
    "Binary Lifting": "trees",
    "Inorder Traversal": "trees",
    "K-D Tree": "trees",
    "Splay Tree": "trees",
    "Treap": "trees",
    "Graphs": "graphs",
    "Graphs (DFS)": "graphs",
    "Graphs (BFS)": "graphs",
    "Graph Theory": "graphs",
    "Union-Find": "graphs",
    "Directed Acyclic Graph": "graphs",
    "Dijkstra's Algorithm": "graphs",
    "Dijkstra": "graphs",
    "BFS": "graphs",
    "DFS": "graphs",
    "Topological Sort": "graphs",
    "Bellman–Ford Algorithm": "graphs",
    "Bellman-Ford": "graphs",
    "Floyd–Warshall Algorithm": "graphs",
    "Shortest Path": "graphs",
    "K Shortest Path": "graphs",
    "0-1 Bfs": "graphs",
    "Bidirectional Search": "graphs",
    "A* Search": "graphs",
    "Flow Network": "graphs",
    "Maximum Flow": "graphs",
    "Minimum-Cost Flow": "graphs",
    "Minimum Cut": "graphs",
    "Maximum Matching": "graphs",
    "Perfect Matching": "graphs",
    "Matching (Graph)": "graphs",
    "Bipartite Graph": "graphs",
    "Graph Coloring": "graphs",
    "Eulerian Path": "graphs",
    "Eulerian Graph": "graphs",
    "Eulerian Circuit": "graphs",
    "Semi-Eulerian Graph": "graphs",
    "Hamiltonian Path": "graphs",
    "Strongly Connected Component": "graphs",
    "Kosaraju's Algorithm": "graphs",
    "Tarjan's SCC Algorithm": "graphs",
    "Bridge (Graph)": "graphs",
    "Articulation Point": "graphs",
    "Borůvka's Algorithm": "graphs",
    "Kruskal's Algorithm": "graphs",
    "Prim's Algorithm": "graphs",
    "Dinic's Algorithm": "graphs",
    "Edmonds–Karp Algorithm": "graphs",
    "MPM Algorithm": "graphs",
    "Push-Relabel Algorithm": "graphs",
    "Successive Shortest Path Algorithm": "graphs",
    "Heuristic Search": "graphs",
    "Planar Graph": "graphs",
    "Sparse Table": "graphs",
    "Binary Indexed Tree": "graphs",
    "Range Minimum/Maximum Query": "graphs",
    "Dynamic Programming": "dynamic-programming",
    "Knapsack Problem": "dynamic-programming",
    "0-1 Knapsack": "dynamic-programming",
    "Complete Knapsack": "dynamic-programming",
    "Multiple Knapsack": "dynamic-programming",
    "Mixed Knapsack": "dynamic-programming",
    "Knapsack": "dynamic-programming",
    "Longest Increasing Subsequence": "dynamic-programming",
    "Longest Common Subsequence": "dynamic-programming",
    "Game Theory": "dynamic-programming",
    "Minimax": "dynamic-programming",
    "Zero-Sum Game": "dynamic-programming",
    "Impartial Game": "dynamic-programming",
    "Nim Game": "dynamic-programming",
    "Sprague–Grundy Theorem": "dynamic-programming",
    "Strings": "sliding-windows",
    "String": "sliding-windows",
    "String Matching": "sliding-windows",
    "KMP Algorithm": "sliding-windows",
    "Knuth–Morris–Pratt Algorithm": "sliding-windows",
    "Z Algorithm": "sliding-windows",
    "Suffix Automaton": "sliding-windows",
    "Aho–Corasick Algorithm": "sliding-windows",
    "Boyer–Moore String-Search Algorithm": "sliding-windows",
    "Manacher": "sliding-windows",
    "Lyndon Factorization": "sliding-windows",
    "Lexicographically Minimal String Rotation": "sliding-windows",
    "Bracket Sequences": "stack",
    "Regex": "sliding-windows",
    "Arrays": "arrays-hashing",
    "Array": "arrays-hashing",
    "Hashing": "arrays-hashing",
    "Counting": "arrays-hashing",
    "Sets": "arrays-hashing",
    "Prefix Sum": "arrays-hashing",
    "Matrix": "math-matrices",
    "Math": "math-matrices",
    "Combinatorics": "math-matrices",
    "Geometry": "math-matrices",
    "Probability and Statistics": "math-matrices",
    "Probability": "math-matrices",
    "Linear Algebra": "math-matrices",
    "Sorting": "sorting",
    "Quicksort": "sorting",
    "Bubble Sort": "sorting",
    "Merge Sort": "sorting",
    "Timsort": "sorting",
    "Tournament Sort": "sorting",
    "Ordered Sets": "sorting",
    "Divide & Conquer": "sorting",
    "Binary Search": "binary-search",
    "Ternary Search": "binary-search",
    "Two Pointers": "two-pointers",
    "Fast-Slow Pointers": "two-pointers",
    "Sliding Window": "sliding-windows",
    "Stacks & Queues": "stack",
    "Stack": "stack",
    "Queue": "data-structures",
    "Monotonic Stack": "stack",
    "Heap (Priority Queue)": "heap",
    "Heap": "heap",
    "Heaps / Priority Queue": "heap",
    "Greedy": "greedy",
    "Recursion & Backtracking": "backtracking",
    "Recursion": "backtracking",
    "Backtracking": "backtracking",
    "Enumeration": "backtracking",
    "Brute-Force Search": "backtracking",
    "Meet in the Middle": "backtracking",
    "Bit Manipulation": "bit-manipulation",
    "Simulation": "data-structures",
    "Design": "data-structures",
    "Concurrency": "data-structures",
    "Database": "data-structures",
    "SQL": "data-structures",
    "Pandas": "data-structures",
    "JavaScript": "data-structures",
    "Interactive": "data-structures",
}

_PRIORITY = {
    "linked-lists": 0, "trees": 1, "graphs": 2, "dynamic-programming": 3,
    "sliding-windows": 4, "stack": 5, "trie": 6,
}


def map_topic(raw_topics: list[str]) -> tuple[str, dict[str, str]]:
    """Map raw topics to one category by priority; unmapped -> arrays-hashing."""
    mapped = {RAW_TOPIC_MAP[t]: t for t in raw_topics if t in RAW_TOPIC_MAP}
    if not mapped:
        return "arrays-hashing", {}
    best = min(mapped, key=lambda k: _PRIORITY.get(k, 99))
    return best, {k: v for k, v in mapped.items() if k != best}


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def merge_group(rows: list[dict]) -> dict:
    """Merge normalized-dup rows, preferring the LeetCode row as base."""
    def rank(r: dict) -> tuple:
        return (
            0 if r.get("source") == "LeetCode" else 1,
            0 if (r.get("difficulty") or "").strip() else 1,
            -len(r.get("company") or ""),
        )
    base = min(rows, key=rank)
    topics: list[str] = []
    for r in rows:
        for t in split_topics(r.get("topics")):
            if t not in topics:
                topics.append(t)
    companies: list[str] = []
    truncated = False
    for r in rows:
        cl, tr = split_companies(r.get("company"))
        truncated = truncated or tr
        for c in cl:
            if c not in companies:
                companies.append(c)
    sources = sorted({r.get("source", "") for r in rows if r.get("source")})
    difficulty = (base.get("difficulty") or "").strip().upper()
    return {
        "title": base["question"].strip(),
        "difficulty": DIFFICULTY_MAP.get(difficulty, "Unknown"),
        "topics_raw": topics,
        "companies": companies,
        "company_count": len(companies),
        "companies_truncated": truncated,
        "sources": sources,
        "source_url": (base.get("url") or "").strip(),
    }


def build() -> dict:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    canonical = read_csv(CANONICAL_CSV)
    supplement = read_csv(SUPPLEMENT_CSV)

    canon_titles = {(r.get("question") or "").strip().lower() for r in canonical}
    extra = [r for r in supplement if (r.get("question") or "").strip().lower() not in canon_titles]

    groups: dict[str, list[dict]] = {}
    for r in canonical + extra:
        if not (r.get("question") or "").strip():
            continue
        groups.setdefault(normalize_title(r["question"]), []).append(r)

    existing_slugs = {p.stem for p in (REPO_ROOT / "content" / "problems").glob("*.json")}
    catalog: list[dict] = []
    slug_seen: set[str] = set()
    for rows in groups.values():
        entry = merge_group(rows)
        slug = slugify(entry["title"])
        i, base_slug = 2, slug
        while slug in slug_seen:
            slug = f"{base_slug}-{i}"
            i += 1
        slug_seen.add(slug)
        algo_topic, _ = map_topic(entry["topics_raw"])
        entry["slug"] = slug
        entry["algo_topic"] = algo_topic
        entry["pattern"] = next(
            (t for t in entry["topics_raw"] if t not in ("Arrays", "Dsa", "Coding")),
            (entry["topics_raw"][0] if entry["topics_raw"] else algo_topic),
        )
        entry["already_in_algovista"] = slug in existing_slugs
        entry["merged_rows"] = len(rows)
        catalog.append(entry)

    catalog.sort(key=lambda e: (-e["company_count"], e["title"].lower()))

    company_freq = Counter(c for e in catalog for c in e["companies"])
    topic_freq = Counter(e["algo_topic"] for e in catalog)
    diff_freq = Counter(e["difficulty"] for e in catalog)

    with open(CATALOG_DIR / "catalog.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=1, ensure_ascii=False)
    with open(CATALOG_DIR / "companies.json", "w", encoding="utf-8") as f:
        json.dump(company_freq.most_common(), f, indent=1, ensure_ascii=False)
    with open(CATALOG_DIR / "topic_map.json", "w", encoding="utf-8") as f:
        json.dump(RAW_TOPIC_MAP, f, indent=1, ensure_ascii=False)

    merged_extra = sum(1 for e in catalog if e["merged_rows"] > 1)
    new_from_supplement = sum(
        1 for norm, rows in groups.items()
        if any((r.get("question") or "").strip().lower() not in canon_titles for r in rows)
    )
    report = [
        "ALGOVISTA DSA CATALOG -- BUILD REPORT",
        "=====================================",
        f"Source rows: {len(canonical)} canonical + {len(extra)} supplement-only = {len(canonical) + len(extra)}",
        f"Canonical entries after normalized re-dedup: {len(catalog)}",
        f"Merged dup groups (exact-title missed): {merged_extra}",
        f"Supplement-only titles folded in: {new_from_supplement}",
        "",
        "DIFFICULTY: " + ", ".join(f"{k}={v}" for k, v in diff_freq.most_common()),
        "ALGO TOPICS: " + ", ".join(f"{k}={v}" for k, v in topic_freq.most_common()),
        f"Already in content/problems: {sum(1 for e in catalog if e['already_in_algovista'])}",
        f"New candidates: {sum(1 for e in catalog if not e['already_in_algovista'])}",
        "",
        "TOP 25 COMPANIES (individual, cleaned):",
    ]
    report += [f"  {n:5d}  {c}" for c, n in company_freq.most_common(25)]
    report += [
        "",
        "TOP 20 CANDIDATES (by company count, not yet in Algovista):",
    ]
    shown = 0
    for e in catalog:
        if e["already_in_algovista"]:
            continue
        report.append(
            f"  {e['company_count']:3d} cos | {e['algo_topic']:11s} | {e['difficulty']:7s} | "
            f"{e['title']} [{e['slug']}]"
        )
        shown += 1
        if shown >= 20:
            break
    report_text = "\n".join(report) + "\n"
    with open(CATALOG_DIR / "BUILD_REPORT.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    print(report_text)
    return {
        "entries": len(catalog),
        "merged_groups": merged_extra,
        "topic_freq": dict(topic_freq),
        "diff_freq": dict(diff_freq),
    }


if __name__ == "__main__":
    build()
