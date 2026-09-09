"""Graph algorithms generator with programmatic graph traversal & shortest path oracles."""

import heapq
import random
from content.generators.base import GeneratedQuestion, make_question


def dijkstra_oracle(graph: dict[str, list[tuple[str, int]]], source: str) -> dict[str, int]:
    dist = {node: float("inf") for node in graph}
    dist[source] = 0
    pq = [(0, source)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, weight in graph[u]:
            if dist[u] + weight < dist[v]:
                dist[v] = dist[u] + weight
                heapq.heappush(pq, (dist[v], v))
    return dist


def generate_graph_questions(count: int = 120, seed: int = 45) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # 1. Dijkstra Shortest Path calculations
    dijkstra_graphs = [
        (
            {"A": [("B", 4), ("C", 2)], "B": [("D", 5), ("C", 1)], "C": [("B", 1), ("D", 8), ("E", 10)], "D": [("E", 2)], "E": []},
            "A", "E",
            "Dijkstra shortest path from A to E",
        ),
        (
            {"S": [("A", 2), ("B", 5)], "A": [("B", 1), ("C", 4)], "B": [("C", 2), ("D", 6)], "C": [("D", 1)], "D": []},
            "S", "D",
            "Dijkstra shortest path from S to D",
        ),
        (
            {"1": [("2", 3), ("3", 6)], "2": [("3", 2), ("4", 7)], "3": [("4", 1), ("5", 5)], "4": [("5", 2)], "5": []},
            "1", "5",
            "Dijkstra shortest path from 1 to 5",
        ),
        (
            {"A": [("B", 1), ("C", 4)], "B": [("C", 2), ("D", 5)], "C": [("D", 1)], "D": [("E", 3)], "E": []},
            "A", "E",
            "Shortest path from A to E",
        ),
        (
            {"A": [("B", 2), ("C", 5)], "B": [("C", 2), ("D", 4)], "C": [("D", 1), ("E", 7)], "D": [("E", 3)], "E": []},
            "A", "E",
            "Shortest path A to E",
        ),
        (
            {"1": [("2", 4), ("3", 3)], "2": [("4", 5)], "3": [("2", 1), ("4", 8), ("5", 6)], "4": [("5", 2)], "5": []},
            "1", "5",
            "Shortest path 1 to 5",
        ),
        (
            {"S": [("A", 3), ("B", 6)], "A": [("C", 4), ("B", 2)], "B": [("D", 5)], "C": [("D", 2), ("T", 7)], "D": [("T", 3)], "T": []},
            "S", "T",
            "Shortest path S to T",
        ),
        (
            {"U": [("V", 2), ("W", 4)], "V": [("W", 1), ("X", 7)], "W": [("X", 3)], "X": [("Y", 1)], "Y": []},
            "U", "Y",
            "Shortest path U to Y",
        ),
        (
            {"0": [("1", 2), ("2", 4)], "1": [("2", 1), ("3", 7)], "2": [("4", 3)], "3": [("5", 1)], "4": [("3", 2), ("5", 5)], "5": []},
            "0", "5",
            "Shortest path 0 to 5",
        ),
        (
            {"A": [("B", 5), ("C", 2)], "C": [("B", 1), ("D", 4)], "B": [("D", 2)], "D": []},
            "A", "D",
            "Shortest path A to D",
        ),
        (
            {"P": [("Q", 3), ("R", 8)], "Q": [("R", 2), ("S", 6)], "R": [("S", 3)], "S": []},
            "P", "S",
            "Shortest path P to S",
        ),
        (
            {"1": [("2", 1), ("3", 5)], "2": [("3", 2), ("4", 4)], "3": [("4", 1)], "4": []},
            "1", "4",
            "Shortest path 1 to 4",
        ),
    ]

    for graph, src, dst, desc in dijkstra_graphs:
        distances = dijkstra_oracle(graph, src)
        shortest_dist = distances[dst]
        ans = str(int(shortest_dist))
        cand_d = [int(shortest_dist + 2), int(shortest_dist + 4), int(shortest_dist + 6)]
        if shortest_dist > 2:
            cand_d.append(int(shortest_dist - 2))
        distractors = [str(d) for d in cand_d if d != int(shortest_dist)]

        adj_list_str = "\n".join(f"  {u} -> " + ", ".join(f"({v}, w={w})" for v, w in edges) for u, edges in graph.items())
        prompt = (
            f"Consider a directed graph with weighted edges:\n```text\n{adj_list_str}\n```\n"
            f"Using Dijkstra's algorithm, what is the length of the shortest path from vertex `{src}` to vertex `{dst}`?"
        )
        q = make_question(
            id_str=f"gen-graph-dijk-{q_idx}",
            topic="graphs",
            subtopic="shortest-path",
            difficulty="Medium",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Applying Dijkstra's algorithm from source {src} greedily relaxes edges. The shortest distance to {dst} is {shortest_dist}.",
            generator_key="graph_algorithms.dijkstra",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 2. Graph Theory & Algorithm Conceptual Invariants
    concept_cases = [
        (
            "Which condition guarantees that Dijkstra's algorithm will always find the correct shortest path?",
            "All edge weights must be non-negative",
            ["The graph must be a Directed Acyclic Graph (DAG)", "The graph must be planar", "All edge weights must be integers"],
            "Dijkstra relies on greedy choices assuming that visiting a node establishes its final shortest distance. Negative edge weights invalidate this premise, requiring Bellman-Ford instead.",
            "Easy",
        ),
        (
            "What is the time complexity of detecting a cycle in a directed graph of V vertices and E edges using Kahn's algorithm (indegree BFS)?",
            "O(V + E)",
            ["O(V * E)", "O(V²)", "O(E log V)"],
            "Kahn's algorithm initializes indegrees in O(V + E), then processes each vertex and decrements edge counts in O(V + E) total time.",
            "Easy",
        ),
        (
            "In Kruskal's algorithm for finding a Minimum Spanning Tree of a connected weighted graph with V vertices and E edges, what dominates the time complexity?",
            "Sorting the edges in O(E log E) time",
            ["Finding disjoint set components in O(V²)", "Checking tree connectivity in O(V + E)", "Inserting edges into an adjacency list in O(V)"],
            "Kruskal's algorithm sorts all edges by weight, taking O(E log E) = O(E log V) time. Subsequent DSU find/union operations take nearly linear O(E α(V)) time, so edge sorting dominates.",
            "Medium",
        ),
        (
            "Which algorithmic technique finds the shortest path between all pairs of vertices in a weighted graph with possible negative edges (no negative cycles) in O(V³) time?",
            "Floyd-Warshall algorithm",
            ["Bellman-Ford repeated V times", "Dijkstra with Fibonacci heaps", "Johnson's algorithm"],
            "Floyd-Warshall is a dynamic programming algorithm using recurrence `dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])` with three nested loops over V vertices, running in O(V³) time.",
            "Medium",
        ),
        (
            "What property characterizes a bipartite graph?",
            "It contains no odd-length cycles",
            ["It contains no even-length cycles", "Every vertex has even degree", "It is a planar tree"],
            "A graph is bipartite (2-colorable) if and only if it contains no odd-length cycles. If a cycle of odd length exists, 2 colors cannot alternate without adjacent collision.",
            "Medium",
        ),
        (
            "What is the maximum number of edges in a simple connected undirected graph with V vertices?",
            "V(V - 1) / 2",
            ["V²", "V(V - 1)", "2^(V - 1)"],
            "Each vertex can connect to at most (V - 1) other vertices. Dividing by 2 because edges are undirected yields C(V, 2) = V(V - 1) / 2 edges in a complete graph K_V.",
            "Easy",
        ),
        (
            "What is the worst-case space complexity of Kosaraju's algorithm for finding Strongly Connected Components in a directed graph?",
            "O(V + E)",
            ["O(V²)", "O(V * E)", "O(log V)"],
            "Kosaraju's algorithm creates a transposed graph of size O(V + E) and performs two DFS passes, each requiring O(V) stack space and O(V) visited tracking.",
            "Hard",
        ),
    ]

    for prompt, ans, distractors, exp, diff in concept_cases:
        q = make_question(
            id_str=f"gen-graph-concept-{q_idx}",
            topic="graphs",
            subtopic="graph-theory",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=exp,
            generator_key="graph_algorithms.concepts",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    return questions[:count]
