"""Generate verified learning path definitions in content/paths/."""

import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path
_repo_root = Path(__file__).resolve().parent.parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from content.validators.schema import LearningPathSchema


def create_all_paths(target_dir: Path) -> int:
    target_dir.mkdir(parents=True, exist_ok=True)

    paths_data = [
        {
            "slug": "foundations",
            "title": "Foundations",
            "blurb": "Start here. Learn how to read arrays, search sorted data, and build solid algorithmic fundamentals.",
            "icon": "LayoutGrid",
            "track": "foundational",
            "ordinal": 1,
            "is_published": True,
            "steps": [
                {"ordinal": 1, "step_type": "visualizer", "ref_id": "array", "title": "Live Array Operations"},
                {"ordinal": 2, "step_type": "visualizer", "ref_id": "sorting", "title": "Five Sorting Algorithms"},
                {"ordinal": 3, "step_type": "quiz", "ref_id": "arrays", "title": "Arrays & Two Pointers Quiz"},
                {"ordinal": 4, "step_type": "problem", "ref_id": "two-sum", "title": "Two Sum"},
                {"ordinal": 5, "step_type": "problem", "ref_id": "contains-duplicate", "title": "Contains Duplicate"},
                {"ordinal": 6, "step_type": "problem", "ref_id": "valid-anagram", "title": "Valid Anagram"},
                {"ordinal": 7, "step_type": "problem", "ref_id": "valid-parentheses", "title": "Valid Parentheses"},
                {"ordinal": 8, "step_type": "problem", "ref_id": "maximum-subarray", "title": "Maximum Subarray"},
            ],
        },
        {
            "slug": "pointers",
            "title": "Pointers & Strings",
            "blurb": "Work through arrays and strings by sliding windows, binary searching, and inverting sequences.",
            "icon": "LayoutGrid",
            "track": "foundational",
            "ordinal": 2,
            "is_published": True,
            "steps": [
                {"ordinal": 1, "step_type": "visualizer", "ref_id": "searching", "title": "Binary Search Step-Through"},
                {"ordinal": 2, "step_type": "problem", "ref_id": "valid-palindrome", "title": "Valid Palindrome"},
                {"ordinal": 3, "step_type": "problem", "ref_id": "two-sum", "title": "Two Sum"},
                {"ordinal": 4, "step_type": "problem", "ref_id": "container-with-most-water", "title": "Container With Most Water"},
                {"ordinal": 5, "step_type": "problem", "ref_id": "product-of-array-except-self", "title": "Product of Array Except Self"},
                {"ordinal": 6, "step_type": "problem", "ref_id": "longest-substring-without-repeating", "title": "Longest Substring Without Repeating Characters"},
                {"ordinal": 7, "step_type": "quiz", "ref_id": "arrays", "title": "Pointers Mastery Quiz"},
            ],
        },
        {
            "slug": "structures",
            "title": "Data Structures",
            "blurb": "Lists, stacks, queues and trees — how they operate under the hood and where they show up.",
            "icon": "GitCommit",
            "track": "specialised",
            "ordinal": 3,
            "is_published": True,
            "steps": [
                {"ordinal": 1, "step_type": "visualizer", "ref_id": "linked-list", "title": "Singly Linked List"},
                {"ordinal": 2, "step_type": "visualizer", "ref_id": "stack", "title": "LIFO Stack"},
                {"ordinal": 3, "step_type": "visualizer", "ref_id": "queue", "title": "FIFO Queue"},
                {"ordinal": 4, "step_type": "visualizer", "ref_id": "binary-tree", "title": "Tree Traversals"},
                {"ordinal": 5, "step_type": "visualizer", "ref_id": "bst", "title": "Binary Search Tree"},
                {"ordinal": 6, "step_type": "visualizer", "ref_id": "heap", "title": "Binary Min/Max Heap"},
                {"ordinal": 7, "step_type": "visualizer", "ref_id": "hashmap", "title": "Hash Map Separate Chaining"},
                {"ordinal": 8, "step_type": "quiz", "ref_id": "trees", "title": "Trees & Heaps Quiz"},
                {"ordinal": 9, "step_type": "problem", "ref_id": "reverse-linked-list", "title": "Reverse Linked List"},
                {"ordinal": 10, "step_type": "problem", "ref_id": "maximum-depth-of-binary-tree", "title": "Maximum Depth of Binary Tree"},
            ],
        },
        {
            "slug": "algorithms",
            "title": "Graphs & Dynamic Programming",
            "blurb": "Graph traversals, topological sorting, shortest paths, and dynamic programming state transitions.",
            "icon": "Network",
            "track": "specialised",
            "ordinal": 4,
            "is_published": True,
            "steps": [
                {"ordinal": 1, "step_type": "visualizer", "ref_id": "graph", "title": "Graph BFS/DFS Explorer"},
                {"ordinal": 2, "step_type": "visualizer", "ref_id": "recursion-tree", "title": "Recursion Call Tree"},
                {"ordinal": 3, "step_type": "quiz", "ref_id": "graphs", "title": "Graphs Quiz"},
                {"ordinal": 4, "step_type": "quiz", "ref_id": "dp", "title": "Dynamic Programming Quiz"},
                {"ordinal": 5, "step_type": "problem", "ref_id": "number-of-islands", "title": "Number of Islands"},
                {"ordinal": 6, "step_type": "problem", "ref_id": "climbing-stairs", "title": "Climbing Stairs"},
                {"ordinal": 7, "step_type": "problem", "ref_id": "coin-change", "title": "Coin Change"},
                {"ordinal": 8, "step_type": "problem", "ref_id": "course-schedule", "title": "Course Schedule"},
            ],
        },
        {
            "slug": "placement-dsa",
            "title": "Placement DSA Sprint",
            "blurb": "Company-pattern interview questions, time-constrained problem solving, and top DSA patterns.",
            "icon": "Cpu",
            "track": "placement",
            "ordinal": 5,
            "is_published": True,
            "steps": [
                {"ordinal": 1, "step_type": "quiz", "ref_id": "complexity", "title": "Asymptotic Analysis & Big-O"},
                {"ordinal": 2, "step_type": "problem", "ref_id": "two-sum", "title": "Two Sum"},
                {"ordinal": 3, "step_type": "problem", "ref_id": "maximum-subarray", "title": "Maximum Subarray"},
                {"ordinal": 4, "step_type": "problem", "ref_id": "longest-substring-without-repeating", "title": "Longest Substring Without Repeating"},
                {"ordinal": 5, "step_type": "problem", "ref_id": "merge-two-sorted-lists", "title": "Merge Two Sorted Lists"},
                {"ordinal": 6, "step_type": "problem", "ref_id": "validate-binary-search-tree", "title": "Validate Binary Search Tree"},
                {"ordinal": 7, "step_type": "problem", "ref_id": "number-of-islands", "title": "Number of Islands"},
                {"ordinal": 8, "step_type": "problem", "ref_id": "coin-change", "title": "Coin Change"},
                {"ordinal": 9, "step_type": "quiz", "ref_id": "mixed", "title": "Comprehensive DSA Placement Mock Quiz"},
            ],
        },
    ]

    count = 0
    for p_data in paths_data:
        # Validate through schema
        validated = LearningPathSchema(**p_data)
        out_file = target_dir / f"{validated.slug}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(p_data, f, indent=2)
        count += 1

    print(f"Created and validated {count} learning paths.")
    return count


if __name__ == "__main__":
    paths_dir = Path(__file__).resolve().parent.parent / "paths"
    create_all_paths(paths_dir)
