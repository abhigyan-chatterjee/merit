"""Core CS question generator (OS, DBMS, CN, OOP, system design) with exact oracles."""

import random
from collections import deque

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


def _total_wait_fcfs(bursts: list[int]) -> int:
    elapsed = 0
    total = 0
    for burst in bursts:
        total += elapsed
        elapsed += burst
    return total


def _total_wait_sjf(bursts: list[int]) -> int:
    elapsed = 0
    total = 0
    for burst in sorted(bursts):
        total += elapsed
        elapsed += burst
    return total


def _eat(hit: float, tlb: int, mem: int) -> float:
    return hit * (tlb + mem) + (1 - hit) * (tlb + 2 * mem)


def _bankers_finished(available: list[int], needs: list[list[int]], releases: list[list[int]]) -> int:
    available = list(available)
    pending = set(range(len(needs)))
    finished = 0
    while True:
        progressed = False
        for i in sorted(pending):
            if all(need <= have for need, have in zip(needs[i], available)):
                available = [have + unit for have, unit in zip(available, releases[i])]
                pending.discard(i)
                finished += 1
                progressed = True
        if not progressed:
            return finished


def _fifo_faults(reference: list[int], frames: int) -> int:
    memory: list[int] = []
    faults = 0
    for page in reference:
        if page in memory:
            continue
        faults += 1
        if len(memory) == frames:
            memory.pop(0)
        memory.append(page)
    return faults


def _lru_faults(reference: list[int], frames: int) -> int:
    memory: list[int] = []
    faults = 0
    for page in reference:
        if page in memory:
            memory.remove(page)
            memory.append(page)
            continue
        faults += 1
        if len(memory) == frames:
            memory.pop(0)
        memory.append(page)
    return faults


def _rr_total_wait(bursts: list[int], quantum: int) -> int:
    remaining = list(bursts)
    wait = [0] * len(bursts)
    queue = deque(range(len(bursts)))
    while queue:
        i = queue.popleft()
        run = min(quantum, remaining[i])
        remaining[i] -= run
        for j in range(len(bursts)):
            if j != i and remaining[j] > 0:
                wait[j] += run
        if remaining[i] > 0:
            queue.append(i)
    return sum(wait)


def generate_core_questions(count: int = 104, seed: int = 202) -> list[GeneratedQuestion]:
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
                id_str=f"gen-core-{idx:03d}",
                topic="core-cs",
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

    # 1. CPU scheduling (exact waiting-time oracles)
    for algorithm, bursts, wait in [
        ("FCFS", [5, 3, 8, 4], _total_wait_fcfs([5, 3, 8, 4])),
        ("SJF", [5, 3, 8, 4], _total_wait_sjf([5, 3, 8, 4])),
        ("FCFS", [6, 2, 9, 3], _total_wait_fcfs([6, 2, 9, 3])),
        ("SJF", [6, 2, 9, 3], _total_wait_sjf([6, 2, 9, 3])),
    ]:
        add(
            "core_cs.cpu_scheduling", "os-scheduling", "Hard",
            f"Four processes arrive together with burst times {bursts}. Using {algorithm} "
            "scheduling, what is the total waiting time? Give only the number.",
            str(wait), _nums(wait), f"Under {algorithm} the total waiting time is {wait}.",
        )

    # 2. Paging / TLB effective access time
    for hit, tlb, mem in [(0.8, 10, 100), (0.9, 10, 50), (0.75, 20, 200), (0.6, 5, 100)]:
        eat = _eat(hit, tlb, mem)
        ans = f"{eat:g}"
        add(
            "core_cs.paging_tlb", "os-memory", "Hard",
            f"A TLB hit ratio of {hit} costs {tlb} ns to search and {mem} ns to access memory; "
            "a miss also needs a second memory access. What is the effective access time in ns?",
            ans, [f"{eat + 10:g}", f"{eat + 20:g}", f"{eat + 30:g}", f"{eat + 50:g}"],
            f"EAT = {hit}*({tlb}+{mem}) + (1-{hit})*({tlb}+2*{mem}) = {eat} ns.",
        )

    # 3. Banker's algorithm
    scenarios = [
        ([3, 3, 2], [[1, 2, 2], [3, 1, 2], [2, 2, 1], [1, 1, 1]], [[1, 1, 1]] * 4),
        ([1, 1, 0], [[2, 2, 1], [3, 1, 1], [1, 1, 0], [4, 4, 4]], [[1, 1, 0]] * 4),
        ([2, 2, 2], [[1, 1, 1], [2, 2, 2], [3, 3, 3], [6, 6, 6]], [[1, 1, 1]] * 4),
        ([1, 1, 1], [[1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]], [[1, 1, 0]] * 4),
    ]
    for available, needs, releases in scenarios:
        finished = _bankers_finished(available, needs, releases)
        add(
            "core_cs.bankers_algorithm", "os-deadlock", "Hard",
            f"With available resources {available}, needs {needs} and releases {releases}, "
            "how many processes can finish in a safe state?",
            str(finished), _nums(finished),
            f"The safety algorithm allows {finished} processes to finish.",
        )

    # 4. Coffman deadlock conditions
    for prompt, ans, dis, exp in [
        ("Which of these is NOT one of Coffman's four necessary deadlock conditions?",
         "Aging", ["Mutual exclusion", "Hold and wait", "Circular wait"],
         "Aging prevents starvation; it is not a deadlock condition."),
        ("Which condition allows a process to keep resources while waiting for more?",
         "Hold and wait", ["No preemption", "Mutual exclusion", "Circular wait"],
         "Hold and wait describes retaining held resources while requesting more."),
        ("Which condition means a resource can be used by only one process at a time?",
         "Mutual exclusion", ["Hold and wait", "No preemption", "Circular wait"],
         "Mutual exclusion grants exclusive use of a resource."),
        ("Which condition requires a closed chain of processes each awaiting a resource held "
         "by the next?", "Circular wait", ["No preemption", "Mutual exclusion", "Hold and wait"],
         "A circular wait is a cycle in the resource allocation graph."),
    ]:
        add("core_cs.deadlock_conditions", "os-deadlock", "Medium", prompt, ans, dis, exp)

    # 5. Semaphores & mutexes
    for prompt, ans, dis, exp in [
        ("Which synchronization primitive is ownership-aware and supports priority inheritance?",
         "Mutex", ["Binary semaphore", "Counting semaphore", "Spinlock"],
         "A mutex has ownership and can implement priority inheritance."),
        ("What happens when wait() is called on a binary semaphore whose value is 0?",
         "The calling thread blocks", ["The semaphore value becomes negative always",
                                       "The thread is terminated", "The value is reset to 1"],
         "A zero semaphore causes the caller to block until signal."),
        ("What does a counting semaphore initialized to 5 directly control?",
         "Up to 5 concurrent accesses", ["Exactly one thread total", "Deadlock freedom",
                                         "CPU affinity"],
         "The count tracks five identical resource units."),
        ("Which semaphore operation increments the value and may wake a blocked thread?",
         "signal (V)", ["wait (P)", "acquire", "block"],
         "The V operation increments and releases a waiter."),
    ]:
        add("core_cs.semaphores_mutex", "os-sync", "Medium", prompt, ans, dis, exp)

    # 6. Page replacement faults
    ref = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    for policy, frames, seq, faults in [
        ("FIFO", 3, ref, _fifo_faults(ref, 3)),
        ("LRU", 3, ref, _lru_faults(ref, 3)),
        ("FIFO", 2, [1, 2, 1, 3, 1, 2], _fifo_faults([1, 2, 1, 3, 1, 2], 2)),
        ("LRU", 4, [1, 2, 3, 4, 5, 1, 2, 3, 4, 5], _lru_faults([1, 2, 3, 4, 5, 1, 2, 3, 4, 5], 4)),
    ]:
        add(
            "core_cs.page_replacement", "os-memory", "Hard",
            f"Using {policy} replacement with {frames} frames and reference string {seq}, "
            "how many page faults occur? Give only the number.",
            str(faults), _nums(faults), f"{policy} with {frames} frames incurs {faults} page faults.",
        )

    # 7. Thrashing
    for prompt, ans, dis, exp in [
        ("What is thrashing in a virtual memory system?",
         "Excessive paging with little useful work", ["Disk fragmentation", "Cache coherence traffic",
                                                       "Interrupt storms"],
         "Thrashing means the CPU spends most of its time servicing page faults."),
        ("What is the usual cause of thrashing?",
         "Working set larger than available frames", ["Too few processes in memory",
                                                       "A small page size", "Fast disks"],
         "When the working set exceeds frames, page faults dominate."),
        ("Which model estimates a process's active pages to prevent thrashing?",
         "Working-set model", ["Banker's model", "Round-robin model", "Producer-consumer model"],
         "The working-set model tracks recently referenced pages."),
        ("What happens to CPU utilization during thrashing?",
         "It drops sharply", ["It doubles", "It stays at 100%", "It becomes zero permanently"],
         "Most CPU time is spent paging rather than executing."),
    ]:
        add("core_cs.thrashing", "os-memory", "Medium", prompt, ans, dis, exp)

    # 8. Normalization
    for prompt, ans, dis, exp in [
        ("Which normal form eliminates repeating groups and enforces atomic values?",
         "First Normal Form (1NF)", ["Second Normal Form (2NF)", "Third Normal Form (3NF)",
                                     "Boyce-Codd Normal Form (BCNF)"],
         "1NF requires atomic, single-valued columns."),
        ("Which normal form removes partial dependencies on a composite primary key?",
         "Second Normal Form (2NF)", ["First Normal Form (1NF)", "Third Normal Form (3NF)",
                                      "Fourth Normal Form (4NF)"],
         "2NF builds on 1NF and removes partial dependencies."),
        ("Which normal form removes transitive dependencies on the primary key?",
         "Third Normal Form (3NF)", ["First Normal Form (1NF)", "Second Normal Form (2NF)",
                                     "Boyce-Codd Normal Form (BCNF)"],
         "3NF requires non-key attributes to depend directly on the key."),
        ("Which normal form requires every determinant to be a candidate key?",
         "Boyce-Codd Normal Form (BCNF)", ["Third Normal Form (3NF)", "Second Normal Form (2NF)",
                                           "First Normal Form (1NF)"],
         "BCNF is a stricter form of 3NF."),
    ]:
        add("core_cs.normalization", "dbms-normalization", "Medium", prompt, ans, dis, exp)

    # 9. ACID & isolation anomalies
    for prompt, ans, dis, exp in [
        ("Which ACID property makes concurrent transactions appear to run one after another?",
         "Isolation", ["Atomicity", "Consistency", "Durability"],
         "Isolation controls interleaving of transactions."),
        ("Which anomaly occurs when a transaction reads data written by an uncommitted transaction?",
         "Dirty read", ["Phantom read", "Non-repeatable read", "Lost update"],
         "A dirty read sees uncommitted data."),
        ("Which anomaly occurs when re-reading the same row returns a different committed value?",
         "Non-repeatable read", ["Dirty read", "Phantom read", "Lost update"],
         "A non-repeatable read changes a row between reads."),
        ("Which anomaly involves new rows appearing in a repeated range query?",
         "Phantom read", ["Dirty read", "Non-repeatable read", "Lost update"],
         "A phantom read adds new rows to a result set."),
    ]:
        add("core_cs.acid_isolation", "dbms-transactions", "Medium", prompt, ans, dis, exp)

    # 10. B+ tree indexing (exact node capacity oracle)
    for order in [4, 6, 8, 10]:
        keys = order - 1
        add(
            "core_cs.bplus_tree", "dbms-indexing", "Medium",
            f"In a B+ tree of order {order} (maximum {order} children per internal node), what is "
            "the maximum number of search keys in a node? Give only the number.",
            str(keys), _nums(keys), f"Maximum keys = order - 1 = {order} - 1 = {keys}.",
        )

    # 11. WAL & recovery
    for prompt, ans, dis, exp in [
        ("Why does a database use write-ahead logging?",
         "To persist intent before data changes for durability",
         ["To speed up SELECT parsing", "To compress backups", "To shard tables"],
         "WAL records changes durably before applying them."),
        ("In ARIES recovery, what does the redo phase do?",
         "Repeats committed changes", ["Discards all log records", "Deletes the checkpoint",
                                       "Rolls back every transaction"],
         "Redo re-applies committed updates."),
        ("Which log information enables undoing an uncommitted transaction?",
         "Before-image in the undo log", ["The query plan", "The page checksum", "The index root"],
         "The before-image restores the prior value."),
        ("What is the purpose of a checkpoint in recovery?",
         "To shorten recovery time", ["To increase log size", "To lock the database forever",
                                       "To rebuild indexes"],
         "Checkpoints bound how much log must be replayed."),
    ]:
        add("core_cs.wal_recovery", "dbms-recovery", "Medium", prompt, ans, dis, exp)

    # 12. Schedules & locks
    for prompt, ans, dis, exp in [
        ("Which lock allows several readers but blocks writers?",
         "Shared lock", ["Exclusive lock", "Intent lock", "Schema lock"],
         "Shared locks are compatible with other shared locks."),
        ("Which schedule is equivalent to some serial execution?",
         "Conflict-serializable schedule", ["Any interleaved schedule", "A schedule with cycles",
                                             "A non-recoverable schedule"],
         "Conflict serializability preserves precedence order."),
        ("What does two-phase locking guarantee?",
         "Conflict serializability", ["Deadlock freedom", "Fault tolerance", "Referential integrity"],
         "2PL produces conflict-serializable schedules."),
        ("How is a deadlock detected in a lock manager?",
         "A cycle in the wait-for graph", ["A full log buffer", "A missing index", "A low cache hit ratio"],
         "A cycle in the wait-for graph indicates deadlock."),
    ]:
        add("core_cs.schedules_locks", "dbms-transactions", "Hard", prompt, ans, dis, exp)

    # 13. TCP & UDP
    for prompt, ans, dis, exp in [
        ("Which protocol provides a reliable, ordered byte stream between hosts?",
         "TCP", ["UDP", "ICMP", "ARP"],
         "TCP adds sequence numbers, ACKs and retransmission."),
        ("Which protocol is connectionless and does not guarantee delivery?",
         "UDP", ["TCP", "SCTP", "TLS"], "UDP sends datagrams without handshakes or guarantees."),
        ("Which TCP header field advertises the receiver's available buffer space?",
         "Window size", ["Checksum", "Urgent pointer", "Sequence number"],
         "The window field drives flow control."),
        ("Which TCP state does a client enter immediately after sending SYN?",
         "SYN-SENT", ["ESTABLISHED", "SYN-RECEIVED", "TIME-WAIT"],
         "The client waits for SYN-ACK in SYN-SENT."),
    ]:
        add("core_cs.tcp_udp", "cn-transport", "Easy", prompt, ans, dis, exp)

    # 14. Congestion control
    for prompt, ans, dis, exp in [
        ("What does TCP Reno do on receiving three duplicate ACKs?",
         "Fast retransmit and fast recovery", ["Slow start only", "Close the connection",
                                               "Double the receive window"],
         "Three duplicate ACKs trigger fast retransmit."),
        ("In which phase does the congestion window grow linearly?",
         "Congestion avoidance", ["Slow start", "Fast recovery", "Handshake"],
         "Congestion avoidance adds one MSS per RTT."),
        ("Which algorithm starts the congestion window at one MSS and doubles it each RTT?",
         "Slow start", ["Congestion avoidance", "Fast retransmit", "Nagle's algorithm"],
         "Slow start grows the window exponentially."),
        ("What event triggers window reduction in TCP Tahoe?",
         "Packet loss detected", ["A DNS lookup", "A successful handshake", "A cache miss"],
         "Loss is the signal of congestion."),
    ]:
        add("core_cs.congestion_control", "cn-transport", "Hard", prompt, ans, dis, exp)

    # 15. CIDR subnetting (exact address math)
    for prompt, ans, dis, exp in [
        ("How many usable host addresses does a /24 network provide?",
         str(2 ** (32 - 24) - 2), _nums(2 ** (32 - 24) - 2),
         "A /24 leaves 8 host bits, giving 2^8 - 2 = 254 usable addresses."),
        ("How many /26 subnets fit inside a /24 network?",
         str(2 ** (26 - 24)), _nums(2 ** (26 - 24)),
         "Borrowing 2 bits yields 2^2 = 4 subnets."),
        ("What is the broadcast address of 192.168.1.0/24?",
         "192.168.1.255", ["192.168.1.254", "192.168.0.255", "192.168.2.0"],
         "All eight host bits set gives 192.168.1.255."),
        ("How many usable host addresses does a /27 network provide?",
         str(2 ** (32 - 27) - 2), _nums(2 ** (32 - 27) - 2),
         "A /27 leaves 5 host bits, giving 2^5 - 2 = 30 usable addresses."),
    ]:
        add("core_cs.cidr_subnetting", "cn-addressing", "Medium", prompt, ans, dis, exp)

    # 16. HTTP / TLS / DNS
    for prompt, ans, dis, exp in [
        ("Which HTTP status code means a resource has moved permanently?",
         "301", ["200", "404", "500"], "301 indicates a permanent redirect."),
        ("Which DNS record maps a hostname to an IPv4 address?",
         "A record", ["MX record", "CNAME record", "TXT record"],
         "The A record stores an IPv4 address."),
        ("Which TLS handshake message carries the server's certificate?",
         "Certificate", ["ClientHello", "Finished", "ChangeCipherSpec"],
         "The server sends its Certificate message during the handshake."),
        ("Which HTTP method is both safe and idempotent for retrieval?",
         "GET", ["POST", "PATCH", "CONNECT"], "GET does not modify server state."),
    ]:
        add("core_cs.http_tls_dns", "cn-application", "Easy", prompt, ans, dis, exp)

    # 17. OSI, switching & routing
    for prompt, ans, dis, exp in [
        ("At which OSI layer does a router operate?",
         "Network layer", ["Data link layer", "Physical layer", "Transport layer"],
         "Routers make forwarding decisions at the network layer."),
        ("Which routing protocol uses hop count as its metric?",
         "RIP", ["OSPF", "BGP", "EIGRP"], "RIP uses hop count with a maximum of 15."),
        ("Which switching technique establishes a dedicated path before data transfer?",
         "Circuit switching", ["Packet switching", "Message switching", "Datagram switching"],
         "Circuit switching reserves a path in advance."),
        ("Which protocol do routers use to advertise IP prefixes across autonomous systems?",
         "BGP", ["ARP", "ICMP", "DHCP"], "BGP is the internet's path-vector routing protocol."),
    ]:
        add("core_cs.osi_routing", "cn-addressing", "Easy", prompt, ans, dis, exp)

    # 18. Java polymorphism
    for prompt, ans, dis, exp in [
        ("A reference of type Animal points to a Dog object and calling speak() invokes Dog's "
         "method. What is this behaviour called?",
         "Dynamic dispatch", ["Overloading", "Hiding", "Shadowing"],
         "Runtime dispatch selects the overriding method."),
        ("In Java, methods with the same name but different parameter lists demonstrate?",
         "Overloading", ["Overriding", "Hiding", "Shadowing"],
         "Overloading is resolved at compile time."),
        ("Which Java keyword prevents a method from being overridden?",
         "final", ["abstract", "static", "transient"], "A final method cannot be redefined."),
        ("What does an abstract method in Java lack?",
         "A body", ["A return type", "A name", "An access modifier"],
         "Abstract methods declare a signature without implementation."),
    ]:
        add("core_cs.java_polymorphism", "oop-java", "Medium", prompt, ans, dis, exp)

    # 19. C++ virtual dispatch
    for prompt, ans, dis, exp in [
        ("Which C++ keyword enables runtime polymorphic dispatch through a base pointer?",
         "virtual", ["const", "static", "inline"], "Declaring a method virtual enables dynamic binding."),
        ("What is the consequence of deleting a derived object through a base pointer when the "
         "base destructor is not virtual?", "Undefined behavior",
         ["A compile error", "Automatic memory reclamation", "A thrown exception"],
         "A non-virtual base destructor leads to undefined behavior."),
        ("A class containing at least one pure virtual function is called?",
         "Abstract", ["Final", "Sealed", "Concrete"],
         "Pure virtual functions make a class abstract."),
        ("Which C++ cast performs a runtime type check for polymorphic types?",
         "dynamic_cast", ["static_cast", "reinterpret_cast", "const_cast"],
         "dynamic_cast checks at runtime and returns null on failure."),
    ]:
        add("core_cs.cpp_virtual_dispatch", "oop-cpp", "Hard", prompt, ans, dis, exp)

    # 20. Python semantics & code output
    for prompt, ans, dis, exp in [
        ("A list passed to a Python function can be mutated so the caller sees the change because "
         "Python uses?", "Pass by object reference",
         ["Pass by value only", "Pass by reference only", "Call by name"],
         "The reference itself is passed by value."),
        ("In 'def f(x, *args)', what does args collect?",
         "A tuple of extra positional arguments", ["A list of keywords", "A dictionary of keywords",
                                                    "A single integer"],
         "The star collects extra positional arguments into a tuple."),
        ("What is the value of len({1, 2, 2, 3}) in Python?",
         "3", ["4", "2", "5"], "A set removes duplicates, leaving three elements."),
        ("Which decorator caches a function's results by its arguments?",
         "functools.lru_cache", ["functools.reduce", "functools.partial", "functools.wraps"],
         "lru_cache memoizes results keyed by arguments."),
    ]:
        add("core_cs.python_semantics", "oop-python", "Medium", prompt, ans, dis, exp)

    # 21. Recursion & complexity
    for prompt, ans, dis, exp in [
        ("For T(n) = T(n-1) + n with T(0) = 0, what is T(4)?",
         "10", ["15", "9", "11"], "T(4) = 1 + 2 + 3 + 4 = 10."),
        ("What is the worst-case time complexity of binary search in an array?",
         "O(log n)", ["O(n)", "O(n log n)", "O(1)"],
         "Each comparison halves the search space."),
        ("How many calls are made in total by naive fib(5) with fib(0)=0 and fib(1)=1?",
         "15", ["10", "12", "9"], "The recurrence of the call count gives 15 calls."),
        ("Solve the recurrence T(n) = 2T(n/2) + n using the master theorem.",
         "O(n log n)", ["O(n^2)", "O(log n)", "O(n)"],
         "The equal case of the master theorem gives n log n."),
    ]:
        add("core_cs.recursion_complexity", "code-output", "Hard", prompt, ans, dis, exp)

    # 22. Caching
    for prompt, ans, dis, exp in [
        ("Which cache strategy loads data from the database only on a read miss?",
         "Cache-aside", ["Write-through", "Write-behind", "Read-through"],
         "Cache-aside populates on a miss."),
        ("Which eviction policy removes the least recently used entry?",
         "LRU", ["FIFO", "Random", "LFU"], "LRU evicts the oldest accessed item."),
        ("What bounds how long stale data may remain in a cache?",
         "TTL", ["A mutex", "A shard key", "A semaphore"],
         "A time-to-live expires cached entries."),
        ("Which pattern writes to cache and database in the same operation?",
         "Write-through", ["Cache-aside", "Write-behind", "Read-through"],
         "Write-through updates both stores synchronously."),
    ]:
        add("core_cs.caching", "design-caching", "Medium", prompt, ans, dis, exp)

    # 23. Sharding
    for prompt, ans, dis, exp in [
        ("What does sharding a database by user_id mainly improve?",
         "Write throughput", ["Index selectivity", "Cache hit ratio", "Query readability"],
         "Distributing writes across shards increases capacity."),
        ("What problem can naive range sharding cause?",
         "Hot spots", ["Lost updates", "phantom reads", "Cache stampedes"],
         "Adjacent keys can concentrate load on one shard."),
        ("Which technique maps keys evenly to shards and minimizes remapping?",
         "Consistent hashing", ["Modulo hashing", "Range partitioning", "List partitioning"],
         "Consistent hashing limits key movement when shards change."),
        ("What is a shard key?",
         "The column used to route each row", ["The replication factor", "The index fill factor",
                                                "The backup schedule"],
         "The shard key decides which shard owns a row."),
    ]:
        add("core_cs.sharding", "design-scaling", "Medium", prompt, ans, dis, exp)

    # 24. Queues
    for prompt, ans, dis, exp in [
        ("Which messaging pattern delivers each task to exactly one worker?",
         "Work queue", ["Fan-out topics", "Pub-sub", "Request-response"],
         "A work queue distributes tasks among consumers."),
        ("What does at-least-once delivery imply?",
         "Consumers may see duplicates", ["Every message is delivered once",
                                           "No acknowledgements are used", "Messages are never retried"],
         "Retries can redeliver the same message."),
        ("Which pattern decouples producers from consumers in time?",
         "Message queue", ["Shared memory", "Remote procedure call", "Polling a database"],
         "A queue buffers messages between producers and consumers."),
        ("What is a dead-letter queue used for?",
         "Messages that repeatedly fail processing", ["Successful messages only", "Schema migrations",
                                                       "Cache invalidation"],
         "Failed messages are moved aside for inspection."),
    ]:
        add("core_cs.queues", "design-messaging", "Medium", prompt, ans, dis, exp)

    # 25. Rate limiting
    for prompt, ans, dis, exp in [
        ("Which algorithm permits short bursts up to a fixed capacity while refilling over time?",
         "Token bucket", ["Fixed counter", "Leaky bucket only", "Round robin"],
         "Token bucket accumulates tokens up to a capacity."),
        ("Which limiter smooths traffic with a sliding time window?",
         "Sliding window log", ["Fixed window only", "Token bucket", "Least connections"],
         "A sliding window log tracks recent request timestamps."),
        ("Which HTTP status code signals that a client has exceeded its rate limit?",
         "429", ["200", "401", "503"], "429 means Too Many Requests."),
        ("Where should a public API enforce rate limits first?",
         "At the edge gateway", ["Inside each browser tab", "In database triggers", "In batch jobs"],
         "Edge enforcement protects all backend services."),
    ]:
        add("core_cs.rate_limiting", "design-scaling", "Hard", prompt, ans, dis, exp)

    # 26. Load balancing
    for prompt, ans, dis, exp in [
        ("Which algorithm routes each request to the backend with the fewest active connections?",
         "Least connections", ["Round robin", "IP hash", "Random"],
         "Least connections adapts to uneven load."),
        ("How does round-robin balancing distribute requests?",
         "Equally in rotation", ["By hash of the URL", "To the fastest server only", "Randomly"],
         "Round robin cycles through the backend list."),
        ("What does a health check accomplish for a load balancer?",
         "Removes unhealthy backends", ["Increases capacity", "Rewrites URLs", "Compresses responses"],
         "Failing backends are taken out of rotation."),
        ("At which layer can a balancer route based on URL paths?",
         "Layer 7", ["Layer 2", "Layer 3", "Layer 4"],
         "Layer 7 balances using application data such as paths."),
    ]:
        add("core_cs.load_balancing", "design-scaling", "Medium", prompt, ans, dis, exp)

    return out[:count]
