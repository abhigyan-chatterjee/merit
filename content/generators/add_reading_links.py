"""Populate missing curated reading links for problem JSON artifacts."""

import json
from pathlib import Path

PROBLEMS_DIR = Path(__file__).resolve().parents[1] / "problems"

TOPIC_LINKS = {
    "arrays-hashing": "https://en.wikipedia.org/wiki/Array_data_structure",
    "two-pointers": "https://en.wikipedia.org/wiki/Two-pointer_technique",
    "sliding-windows": "https://en.wikipedia.org/wiki/Sliding_window_protocol",
    "stack": "https://en.wikipedia.org/wiki/Stack_(abstract_data_type)",
    "linked-lists": "https://en.wikipedia.org/wiki/Linked_list",
    "binary-search": "https://en.wikipedia.org/wiki/Binary_search_algorithm",
    "trees": "https://en.wikipedia.org/wiki/Tree_traversal",
    "heap": "https://en.wikipedia.org/wiki/Heap_(data_structure)",
    "backtracking": "https://en.wikipedia.org/wiki/Backtracking",
    "graphs": "https://en.wikipedia.org/wiki/Graph_traversal",
    "dynamic-programming": "https://en.wikipedia.org/wiki/Dynamic_programming",
    "greedy": "https://en.wikipedia.org/wiki/Greedy_algorithm",
    "trie": "https://en.wikipedia.org/wiki/Trie",
    "intervals": "https://en.wikipedia.org/wiki/Interval_scheduling",
    "math-matrices": "https://en.wikipedia.org/wiki/Matrix_(mathematics)",
    "bit-manipulation": "https://en.wikipedia.org/wiki/Bitwise_operation",
    "sorting": "https://en.wikipedia.org/wiki/Sorting_algorithm",
    "data-structures": "https://en.wikipedia.org/wiki/Abstract_data_type",
}

PATTERN_LINKS = {
    "backtracking": "https://www.geeksforgeeks.org/dsa/backtracking-algorithms/",
    "bfs": "https://en.wikipedia.org/wiki/Breadth-first_search",
    "binary search": "https://cp-algorithms.com/num_methods/binary_search.html",
    "dfs": "https://en.wikipedia.org/wiki/Depth-first_search",
    "divide": "https://en.wikipedia.org/wiki/Divide-and-conquer_algorithm",
    "dynamic programming": "https://cp-algorithms.com/dynamic_programming/intro-to-dp.html",
    "greedy": "https://www.geeksforgeeks.org/greedy-algorithms/",
    "hash": "https://en.wikipedia.org/wiki/Hash_table",
    "heap": "https://en.wikipedia.org/wiki/Heap_(data_structure)",
    "interval": "https://en.wikipedia.org/wiki/Interval_scheduling",
    "monotonic": "https://www.geeksforgeeks.org/introduction-to-monotonic-stack-2/",
    "sliding window": "https://www.geeksforgeeks.org/window-sliding-technique/",
    "sorting": "https://visualgo.net/en/sorting",
    "stack": "https://en.wikipedia.org/wiki/Stack_(abstract_data_type)",
    "two pointer": "https://en.wikipedia.org/wiki/Two-pointer_technique",
    "trie": "https://en.wikipedia.org/wiki/Trie",
    "union find": "https://en.wikipedia.org/wiki/Disjoint-set_data_structure",
}


def links_for(problem: dict) -> list[str]:
    """Choose a topic reference and, when available, a pattern reference."""
    links = [TOPIC_LINKS[problem["topic"]]]
    pattern = problem.get("pattern", "").lower()
    for key, url in PATTERN_LINKS.items():
        if key in pattern and url not in links:
            links.append(url)
            break
    return links[:3]


def main() -> None:
    updated = 0
    for path in sorted(PROBLEMS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("reading_links"):
            continue
        data["reading_links"] = links_for(data)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        updated += 1
    print(f"Added reading links to {updated} problem files")


if __name__ == "__main__":
    main()
