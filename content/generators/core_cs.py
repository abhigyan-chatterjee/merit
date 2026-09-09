"""Core CS question generator (OS, DBMS, CN, system design) with exact oracles."""

import random

from content.generators.base import GeneratedQuestion, make_question


def generate_core_questions(count: int = 100, seed: int = 202) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    core_cases = [
        # OS
        ("Which scheduling algorithm can cause starvation of long processes under heavy short-job load?", "Shortest Job First (non-preemptive)", ["Round Robin with large quantum", "First Come First Served", "Multilevel Feedback with aging"], "SJF always prefers short jobs; without aging, long jobs can wait indefinitely.", "Medium", "os-scheduling"),
        ("What does a counting semaphore initialized to N directly control?", "Up to N concurrent accesses to a resource pool", ["Exactly one thread total", "Deadlock freedom", "CPU affinity"], "The semaphore value tracks N identical resource units.", "Easy", "os-sync"),
        ("In demand paging, what happens on a page fault for a valid but not-resident page?", "OS loads the page from disk, updates the page table, restarts the instruction", ["The process is always killed", "The TLB is disabled permanently", "The disk is reformatted"], "A valid fault triggers page-in and instruction retry.", "Easy", "os-memory"),
        ("Which condition is NOT one of Coffman's four deadlock conditions?", "Aging", ["Mutual exclusion", "Hold and wait", "Circular wait"], "Aging prevents starvation; it is not a deadlock condition.", "Easy", "os-deadlock"),
        ("What is thrashing in virtual memory systems?", "Excessive paging where the CPU spends more time swapping than executing", ["Disk fragmentation", "Cache coherence traffic", "Interrupt storms"], "Thrashing means the working set exceeds frames, so page faults dominate.", "Medium", "os-memory"),
        # DBMS
        ("Which normal form removes all transitive dependencies on the primary key?", "Third Normal Form (3NF)", ["First Normal Form", "Second Normal Form", "BCNF only"], "3NF requires every non-key attribute to depend directly on the key.", "Medium", "dbms-normalization"),
        ("In a B+ tree index, where is the actual row data stored?", "Only in the leaf nodes, linked in key order", ["In every internal node", "In the root only", "Nowhere; B+ trees store hashes"], "Internal nodes hold separators; leaves hold ordered records.", "Medium", "dbms-indexing"),
        ("Which isolation level guarantees full serializability?", "Serializable", ["Read committed", "Repeatable read", "Read uncommitted"], "Serializable executes as if transactions ran one after another.", "Easy", "dbms-transactions"),
        ("What does a foreign key constraint enforce?", "Referential integrity to a parent table's key", ["Uniqueness within one table", "Non-null storage format", "Index compression"], "Foreign keys require matching parent rows.", "Easy", "dbms-constraints"),
        ("Why does a database use write-ahead logging (WAL)?", "To guarantee durability by persisting intent before applying changes", ["To speed up SELECT parsing", "To compress backups", "To shard tables"], "WAL records changes durably first, so crashes can replay.", "Medium", "dbms-recovery"),
        # CN
        ("Which protocol reliably delivers an ordered byte stream between hosts?", "TCP", ["UDP", "ICMP", "ARP"], "TCP adds sequence numbers, ACKs, and retransmission over IP.", "Easy", "cn-transport"),
        ("What does DNS resolve?", "Hostnames to IP addresses", ["MAC to IP", "Ports to processes", "URLs to checksums"], "DNS maps names like example.com to addresses.", "Easy", "cn-application"),
        ("In CIDR, what does the prefix length /24 leave for hosts?", "8 host bits (254 usable)", ["24 host bits", "16 host bits", "No hosts"], "32 - 24 = 8 host bits; minus network and broadcast = 254.", "Easy", "cn-addressing"),
        ("Which HTTP method is idempotent and safe for retrieval?", "GET", ["POST", "CONNECT", "PATCH"], "GET must not change server state and repeats safely.", "Easy", "cn-application"),
        ("What does a TCP SYN flood attack exhaust?", "The server's half-open connection backlog", ["DNS cache", "BGP routes", "TLS certificates"], "Unanswered SYNs fill the backlog queue.", "Medium", "cn-security"),
        # System design (placement level)
        ("For a read-heavy feed, which cache strategy keeps hot timelines fast?", "Cache-aside with TTL plus write-through on post", ["No cache at all", "Write-behind without TTL", "Client-side only cache"], "Hot reads hit memory; TTL bounds staleness; writes refresh entries.", "Medium", "design-caching"),
        ("How should a URL shortener generate collision-free short keys at scale?", "Counter or Snowflake ID encoded in base62", ["Random 2-char strings", "MD5 of the full URL truncated to 2 chars", "Client timestamp only"], "Monotonic unique IDs in base62 stay short and unique.", "Medium", "design-keys"),
        ("Where should rate limiting live for a public API gateway?", "At the edge/gateway with a token-bucket per key", ["In each browser tab", "Only in batch jobs", "Inside the database trigger"], "Edge enforcement protects all backends uniformly.", "Medium", "design-scaling"),
        ("Which database fits a social graph with deep traversals?", "Graph database (e.g. Neo4j)", ["Key-value cache only", "Flat CSV files", "Time-series DB"], "Graph stores model multi-hop relationships natively.", "Easy", "design-storage"),
        ("What makes an API design RESTful for a resource collection?", "Stateless verbs on nouns with status codes and pagination", ["Stateful sessions with RPC verbs", "Single POST endpoint for everything", "XML-only payloads"], "Resources plus uniform verbs plus statelessness define REST.", "Easy", "design-api"),
    ]

    for prompt, ans, distractors, exp, diff, sub in core_cases:
        questions.append(
            make_question(
                id_str=f"gen-core-{sub}-{q_idx}",
                topic="core-cs",
                subtopic=sub,
                difficulty=diff,  # type: ignore[arg-type]
                prompt=prompt,
                correct_answer=ans,
                distractors=distractors,
                explanation=exp,
                generator_key=f"core_cs.{sub}",
                rng=rng,
            )
        )
        q_idx += 1

    return questions[:count]
