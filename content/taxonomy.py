"""Canonical 18-category problem taxonomy (hard replace for the old 6 topics)."""

CATEGORIES: list[dict] = [
    {
        "slug": "arrays-hashing",
        "title": "Arrays & Hashing",
        "description": "Contiguous storage, frequency maps, prefix products, and complement lookups.",
        "icon": "LayoutGrid",
    },
    {
        "slug": "two-pointers",
        "title": "Two Pointers",
        "description": "Converging and parallel pointers on sorted data and linked structures.",
        "icon": "MoveHorizontal",
    },
    {
        "slug": "sliding-windows",
        "title": "Sliding Windows",
        "description": "Fixed and variable windows for subarrays and substrings.",
        "icon": "PanelRight",
    },
    {
        "slug": "stack",
        "title": "Stack",
        "description": "LIFO matching, monotonic stacks, and expression evaluation.",
        "icon": "Layers",
    },
    {
        "slug": "linked-lists",
        "title": "Linked Lists",
        "description": "Pointer rewiring, fast-slow detection, and in-place reversal.",
        "icon": "GitCommit",
    },
    {
        "slug": "trees",
        "title": "Trees",
        "description": "DFS traversals, BST invariants, and path/diameter reasoning.",
        "icon": "Network",
    },
    {
        "slug": "binary-search",
        "title": "Binary Search",
        "description": "Halving invariants on sorted arrays, rotated data, and answer spaces.",
        "icon": "Search",
    },
    {
        "slug": "heap",
        "title": "Heap",
        "description": "Priority queues, k-way merges, and top-k selection.",
        "icon": "ChevronsUp",
    },
    {
        "slug": "graphs",
        "title": "Graphs",
        "description": "BFS/DFS, connectivity, topological sort, and shortest paths.",
        "icon": "Share2",
    },
    {
        "slug": "intervals",
        "title": "Intervals",
        "description": "Merging, inserting, and scheduling overlapping ranges.",
        "icon": "AlignHorizontalDistributeCenter",
    },
    {
        "slug": "dynamic-programming",
        "title": "Dynamic Programming",
        "description": "1D and 2D memoization and tabulation over optimal substructure.",
        "icon": "Cpu",
    },
    {
        "slug": "greedy",
        "title": "Greedy",
        "description": "Locally optimal choices with exchange arguments and intervals.",
        "icon": "Zap",
    },
    {
        "slug": "backtracking",
        "title": "Backtracking",
        "description": "Choice trees, pruning, permutations, and constraint search.",
        "icon": "Split",
    },
    {
        "slug": "bit-manipulation",
        "title": "Bit Manipulation",
        "description": "Masks, shifts, popcounts, and XOR invariants.",
        "icon": "Binary",
    },
    {
        "slug": "sorting",
        "title": "Sorting",
        "description": "Comparison sorts, partitioning, and order statistics.",
        "icon": "ArrowDownWideNarrow",
    },
    {
        "slug": "math-matrices",
        "title": "Math & Matrices",
        "description": "Number theory, combinatorics, and matrix traversal/rotation.",
        "icon": "Sigma",
    },
    {
        "slug": "trie",
        "title": "Trie",
        "description": "Prefix trees for word sets, autocomplete, and XOR queries.",
        "icon": "ListTree",
    },
    {
        "slug": "data-structures",
        "title": "Data Structures",
        "description": "Design problems composing maps, queues, and caches.",
        "icon": "Database",
    },
]

CATEGORY_SLUGS: list[str] = [c["slug"] for c in CATEGORIES]

CATEGORY_BY_SLUG: dict[str, dict] = {c["slug"]: c for c in CATEGORIES}

# Old 6-topic values -> new 18-category slugs (for migrating existing rows).
LEGACY_TOPIC_MAP: dict[str, str] = {
    "arrays": "arrays-hashing",
    "strings": "sliding-windows",
    "linked-list": "linked-lists",
    "trees": "trees",
    "graphs": "graphs",
    "dp": "dynamic-programming",
}
