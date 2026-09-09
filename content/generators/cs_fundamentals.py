"""Placement-grade CS Fundamentals generator (OS, DBMS, Computer Networks) with exact technical oracles."""

import random
from content.generators.base import GeneratedQuestion, make_question


def lru_page_faults_oracle(pages: list[int], frames_cnt: int) -> int:
    frames: list[int] = []
    faults = 0
    for p in pages:
        if p in frames:
            frames.remove(p)
            frames.append(p)
        else:
            faults += 1
            if len(frames) == frames_cnt:
                frames.pop(0)
            frames.append(p)
    return faults


def fifo_page_faults_oracle(pages: list[int], frames_cnt: int) -> int:
    frames: list[int] = []
    faults = 0
    for p in pages:
        if p not in frames:
            faults += 1
            if len(frames) == frames_cnt:
                frames.pop(0)
            frames.append(p)
    return faults


def generate_cs_fundamentals_questions(count: int = 140, seed: int = 48) -> list[GeneratedQuestion]:
    rng = random.Random(seed)
    questions: list[GeneratedQuestion] = []
    q_idx = 1

    # 1. OS: Page Replacement Simulation (LRU vs FIFO)
    page_reference_strings = [
        ([7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2], 3),
        ([1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5], 3),
        ([2, 3, 2, 1, 5, 2, 4, 5, 3, 2, 5, 2], 3),
        ([1, 2, 3, 4, 2, 1, 5, 6, 2, 1, 2, 3, 7, 6, 3, 2, 1, 2, 3, 6], 4),
        ([0, 2, 1, 6, 4, 0, 1, 0, 3, 1, 2, 1], 3),
    ]

    for pages, frames in page_reference_strings:
        lru_faults = lru_page_faults_oracle(pages, frames)
        prompt = (
            f"In an Operating System virtual memory system with `{frames}` physical page frames initially empty, "
            f"the page reference stream is:\n`{pages}`\n\n"
            f"Using the Least Recently Used (LRU) page replacement algorithm, how many total page faults occur?"
        )
        ans = str(lru_faults)
        cand_lru = [lru_faults + 1, lru_faults + 2, lru_faults + 3]
        if lru_faults > 1:
            cand_lru.append(lru_faults - 1)
        distractors = [str(d) for d in cand_lru if d != lru_faults]
        q = make_question(
            id_str=f"gen-cs-os-lru-{q_idx}",
            topic="data-structures",
            subtopic="virtual-memory",
            difficulty="Medium",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"Tracking page presence in {frames} frames with LRU eviction on misses results in exactly {lru_faults} page faults.",
            generator_key="cs_fundamentals.lru_faults",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

        fifo_faults = fifo_page_faults_oracle(pages, frames)
        prompt_fifo = (
            f"In an Operating System virtual memory system with `{frames}` physical page frames initially empty, "
            f"the page reference stream is:\n`{pages}`\n\n"
            f"Using the First-In First-Out (FIFO) page replacement algorithm, how many total page faults occur?"
        )
        ans_f = str(fifo_faults)
        cand_fifo = [fifo_faults + 1, fifo_faults + 2, fifo_faults + 3]
        if fifo_faults > 1:
            cand_fifo.append(fifo_faults - 1)
        distractors_f = [str(d) for d in cand_fifo if d != fifo_faults]
        q_f = make_question(
            id_str=f"gen-cs-os-fifo-{q_idx}",
            topic="data-structures",
            subtopic="virtual-memory",
            difficulty="Medium",
            prompt=prompt_fifo,
            correct_answer=ans_f,
            distractors=distractors_f,
            explanation=f"Tracking FIFO queue eviction on misses results in {fifo_faults} page faults.",
            generator_key="cs_fundamentals.fifo_faults",
            rng=rng,
        )
        questions.append(q_f)
        q_idx += 1

    # 2. Placement CS Theory (OS, DBMS, Networks)
    core_concepts = [
        # OS
        ("What four Coffman conditions are simultaneously necessary and sufficient for a system deadlock to occur?", "Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait", ["Mutual Exclusion, Starvation, Priority Inversion, Aging", "Race Condition, Deadlock, Livelock, Starvation", "Virtual Memory, Thrashing, Belady's Anomaly, Semaphore"], "Coffman proved that deadlock can occur if and only if all 4 conditions hold simultaneously: Mutual exclusion, Hold and wait, No preemption, and Circular wait.", "Medium"),
        ("What anomaly describes the phenomenon where increasing the number of page frames results in an increased number of page faults under FIFO page replacement?", "Belady's Anomaly", ["Amdahl's Law", "Cache Thrashing", "Convoy Effect"], "Belady's Anomaly occurs in FIFO replacement because FIFO is not a stack-based algorithm (unlike LRU or Optimal), so increasing allocated frames can increase page fault count.", "Easy"),
        ("What is the primary difference between a process and a thread in modern operating systems?", "Processes have independent virtual address spaces; threads within a process share the same memory space", ["Threads have their own heap and global variables; processes share memory", "Processes run on the GPU; threads run on the CPU", "Threads cannot be scheduled concurrently by the kernel"], "A process is an execution unit with its own private virtual memory space. Threads belonging to the same process share code, data, and heap segments, maintaining only private stack and registers.", "Easy"),
        # DBMS
        ("In relational database normalization, what distinguishes Boyce-Codd Normal Form (BCNF) from Third Normal Form (3NF)?", "In BCNF, for every non-trivial functional dependency X -> Y, X MUST be a superkey", ["BCNF allows transitive dependencies", "3NF forbids composite primary keys", "BCNF applies only to unindexed tables"], "3NF allows X -> Y if X is a superkey OR Y is a prime attribute. BCNF is stricter: X must always be a superkey without exception.", "Medium"),
        ("Which ACID transaction property guarantees that committed transaction changes survive system crashes or power failures?", "Durability", ["Atomicity", "Consistency", "Isolation"], "Durability guarantees that once a transaction has committed, its updates are recorded in non-volatile storage (WAL/disk) and will not be lost even during a crash.", "Easy"),
        ("Why are B+ trees preferred over standard Binary Search Trees or Hash Indexes for relational database table indexing?", "B+ trees keep data in sorted leaf nodes linked sequentially, enabling efficient range scans and high-fanout shallow disk I/O", ["B+ trees require O(1) time for all operations", "B+ trees use less memory than hash tables for point lookups", "B+ trees eliminate the need for write-ahead logging"], "Disk I/O is costly; B+ trees have high branching factor (fanout > 100), meaning tree depth is typically 3-4. All records are stored at leaf level in linked order, making range queries (`BETWEEN a AND b`) efficient.", "Medium"),
        ("Which SQL transaction isolation level prevents Dirty Reads and Non-Repeatable Reads, but may still permit Phantom Reads?", "Repeatable Read", ["Read Uncommitted", "Read Committed", "Serializable"], "Repeatable Read guarantees rows read cannot be modified by concurrent transactions, preventing non-repeatable reads. However, new rows inserted matching a query predicate (phantom rows) can still appear unless Serializable is used.", "Hard"),
        # Networks
        ("What packet sequence constitutes the standard TCP 3-Way Handshake connection establishment?", "SYN -> SYN-ACK -> ACK", ["ACK -> SYN -> SYN-ACK", "SYN -> ACK -> DATA", "FIN -> FIN-ACK -> ACK"], "Client sends SYN; Server responds with SYN-ACK; Client sends ACK acknowledging the server's sequence number, establishing the TCP connection.", "Easy"),
        ("How many usable host IP addresses are available in an IPv4 subnet with CIDR prefix /26?", "62", ["64", "30", "126"], "A /26 subnet leaves 32 - 26 = 6 host bits. 2^6 = 64 total addresses. Subtracting 2 (network address and broadcast address) yields 62 usable host addresses.", "Easy"),
        ("At which layer of the OSI model do routers primarily operate to forward packets based on IP addresses?", "Network Layer (Layer 3)", ["Data Link Layer (Layer 2)", "Transport Layer (Layer 4)", "Session Layer (Layer 5)"], "Routers operate at Layer 3 (Network layer), inspecting IP headers to make packet routing and forwarding decisions.", "Easy"),
    ]

    for prompt, ans, distractors, exp, diff in core_concepts:
        q = make_question(
            id_str=f"gen-cs-concept-{q_idx}",
            topic="data-structures",
            subtopic="core-concepts",
            difficulty=diff,
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=exp,
            generator_key="cs_fundamentals.concepts",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    # 3. Subnetting & CIDR Host Calculation Loop
    for prefix in [20, 22, 23, 24, 25, 26, 27, 28, 29, 30]:
        host_bits = 32 - prefix
        usable_hosts = (2 ** host_bits) - 2
        total_hosts = 2 ** host_bits
        prompt = (
            f"In an IPv4 network, how many **usable host** IP addresses can be assigned to client devices "
            f"within a subnet configured with CIDR prefix `/{prefix}`?"
        )
        ans = str(usable_hosts)
        cand_sub = [
            total_hosts,
            total_hosts - 1,
            total_hosts + 2,
            usable_hosts + 4,
            max(2, usable_hosts - 4),
            (total_hosts * 2) - 2,
        ]
        distractors = [str(d) for d in dict.fromkeys(cand_sub) if str(d) != ans]
        q = make_question(
            id_str=f"gen-cs-cidr-{q_idx}",
            topic="data-structures",
            subtopic="subnetting",
            difficulty="Easy",
            prompt=prompt,
            correct_answer=ans,
            distractors=distractors,
            explanation=f"A /{prefix} subnet has 32 - {prefix} = {host_bits} host bits, yielding 2^{host_bits} = {total_hosts} total addresses. Subtracting 2 (network and broadcast) yields {usable_hosts} usable host IPs.",
            generator_key="cs_fundamentals.cidr",
            rng=rng,
        )
        questions.append(q)
        q_idx += 1

    return questions[:count]
