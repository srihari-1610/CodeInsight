"""Built-in sample problems. Each carries a pre-written analysis used by Demo mode (no API key)."""
from __future__ import annotations

from typing import Any


def _norm(code: str) -> str:
    return "\n".join(line.rstrip() for line in code.strip().splitlines())


_TWO_SUM = r'''import sys

def main():
    data = sys.stdin.read().split()
    n, target = int(data[0]), int(data[1])
    a = list(map(int, data[2:2 + n]))
    seen = {}
    for i, x in enumerate(a):
        need = target - x
        if need in seen:
            print(seen[need] + 1, i + 1)
            return
        seen[x] = i
    print(-1)

main()'''

_DIJKSTRA = r'''#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, int>>> adj(n + 1);
    for (int i = 0; i < m; i++) {
        int u, v, w;
        cin >> u >> v >> w;
        adj[u].push_back({v, w});
        adj[v].push_back({u, w});
    }
    vector<ll> dist(n + 1, LLONG_MAX);
    priority_queue<pair<ll, int>, vector<pair<ll, int>>, greater<>> pq;
    dist[1] = 0;
    pq.push({0, 1});
    while (!pq.empty()) {
        auto [d, u] = pq.top();
        pq.pop();
        if (d > dist[u]) continue;
        for (auto [v, w] : adj[u]) {
            if (dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
                pq.push({dist[v], v});
            }
        }
    }
    for (int i = 1; i <= n; i++)
        cout << (dist[i] == LLONG_MAX ? -1 : dist[i]) << " ";
    cout << "\n";
    return 0;
}'''

_LIS = r'''#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    scanf("%d", &n);
    vector<int> a(n), dp(n, 1);
    for (int i = 0; i < n; i++) scanf("%d", &a[i]);
    int best = 0;
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < i; j++) {
            if (a[j] < a[i]) dp[i] = max(dp[i], dp[j] + 1);
        }
        best = max(best, dp[i]);
    }
    printf("%d\n", best);
    return 0;
}'''

_LIS_FAST = r'''#include <bits/stdc++.h>
using namespace std;

int main() {
    int n;
    scanf("%d", &n);
    vector<int> tails;
    for (int i = 0; i < n; i++) {
        int x;
        scanf("%d", &x);
        auto it = lower_bound(tails.begin(), tails.end(), x);
        if (it == tails.end()) tails.push_back(x);
        else *it = x;
    }
    printf("%d\n", (int)tails.size());
    return 0;
}'''


def _block(s: int, e: int, text: str, insight: str = "") -> dict[str, Any]:
    return {"start_line": s, "end_line": e, "explanation": text, "key_insight": insight}


SAMPLES: list[dict[str, Any]] = [
    {
        "title": "Two Sum (hash map) - Python",
        "language": "Python",
        "problem": "Given n integers and a target, print the 1-based indices of two elements that sum to the target, or -1.",
        "n_max": 200_000, "m_max": 1, "k_max": 1, "time_limit": 1.0,
        "code": _TWO_SUM,
        "demo": {
            "algorithm": "One-pass hash map (Two Sum)",
            "category": "Hashing",
            "tags": ["hash map", "arrays", "two sum"],
            "summary": "Scans the array once. For each value x it checks whether target - x was already seen; if so the "
                       "pair is found, otherwise x is stored with its index. Checking before inserting also makes "
                       "duplicate values (e.g. 3 + 3 = 6) work.",
            "line_blocks": [
                _block(1, 1, "Imports sys so the whole input can be read in one call, much faster than repeated input()."),
                _block(3, 6, "main() reads all tokens, parses n and target, then slices the next n tokens into the list a.",
                       "Slicing data[2:2+n] copies up to n tokens once - O(n)."),
                _block(7, 7, "seen maps a value to the index where it last appeared."),
                _block(8, 13, "For each element compute need = target - x. If need is already in seen, print both 1-based "
                              "indices and stop; otherwise remember x.",
                       "Lookup happens before insertion, so an element can never pair with itself."),
                _block(14, 14, "If the loop ends without a match, print -1."),
                _block(16, 16, "Entry point: runs main()."),
            ],
            "complexity": {
                "time": "O(n) expected", "space": "O(n)", "ops_expression": "n",
                "variables": {"n": "number of elements", "m": "-", "k": "-"},
                "derivation": "The loop runs at most n times. Each iteration does one dictionary lookup and one insertion, "
                              "both O(1) on average, so time is O(n). The dictionary holds at most n entries, so space is O(n).",
                "best_case": "O(1) - the first two elements already form the pair.",
                "worst_case": "O(n) expected; adversarial hash collisions could degrade dict operations in theory.",
            },
            "optimizations": [{
                "title": "Avoid the intermediate list copy",
                "bottleneck": "data[2:2+n] and list(map(...)) allocate two lists of size n.",
                "suggestion": "Iterate lazily over data[2:2+n], converting with int(tok) inside the loop.",
                "tradeoff": "Saves memory only; runtime stays O(n). Slightly less readable.",
                "impact": "low", "optimized_code": "",
            }],
            "pitfalls": [
                {"kind": "edge_case", "description": "If the input has fewer than n numbers the slice silently returns a shorter list instead of failing.", "line": 6},
                {"kind": "edge_case", "description": "Output uses 1-based indices; confirm the problem statement expects that.", "line": 11},
            ],
            "quality": {
                "clarity_score": 8,
                "naming_feedback": "seen and need describe their role well; a is terse but conventional.",
                "structure_feedback": "Wrapping logic in main() is good practice and the early return keeps the loop flat.",
                "tips": ["Add a short comment explaining why the lookup precedes the insertion."],
            },
        },
    },
    {
        "title": "Dijkstra shortest paths - C++",
        "language": "C++",
        "problem": "Undirected weighted graph with n nodes and m edges. Print the shortest distance from node 1 to every node (-1 if unreachable).",
        "n_max": 100_000, "m_max": 200_000, "k_max": 1, "time_limit": 2.0,
        "code": _DIJKSTRA,
        "demo": {
            "algorithm": "Dijkstra with a binary heap",
            "category": "Graphs",
            "tags": ["shortest path", "priority queue", "graphs"],
            "summary": "Classic single-source shortest paths on non-negative weights. A min-heap always yields the closest "
                       "unsettled node; its edges are relaxed and improved distances are pushed. Stale heap entries are skipped.",
            "line_blocks": [
                _block(1, 3, "Standard headers, namespace and a 64-bit alias so distances cannot overflow int."),
                _block(5, 7, "Fast I/O: unsynchronise C and C++ streams and untie cin from cout.",
                       "Essential when reading ~2*10^5 edges with cin."),
                _block(8, 16, "Read n, m and build an undirected adjacency list of (neighbour, weight) pairs."),
                _block(17, 20, "dist starts at LLONG_MAX as infinity. The priority queue is a min-heap of (distance, node); "
                               "the source (node 1) is pushed with distance 0."),
                _block(21, 31, "Main loop: pop the closest node, skip it if the entry is stale (line 24), otherwise relax "
                               "each outgoing edge and push any improved distance.",
                       "The d > dist[u] check makes lazy deletion work, so each node is expanded once."),
                _block(32, 36, "Print every distance, using -1 for unreachable nodes, then return."),
            ],
            "complexity": {
                "time": "O((n + m) log m)", "space": "O(n + m)", "ops_expression": "(n + m) * log2(m + 2)",
                "variables": {"n": "number of nodes", "m": "number of edges", "k": "-"},
                "derivation": "Each undirected edge becomes two directed edges, and each can trigger at most one push, so the heap "
                              "sees at most 2m pushes and pops, each O(log m). Scanning adjacency lists costs O(n + m) overall. "
                              "Memory is the adjacency list O(n + m) plus the heap O(m).",
                "best_case": "O(n + m) if few relaxations succeed.",
                "worst_case": "O((n + m) log m).",
            },
            "optimizations": [
                {"title": "Stop early for single-target queries",
                 "bottleneck": "The loop keeps expanding nodes after the answer for a given target is final.",
                 "suggestion": "If only dist[t] is needed, break as soon as t is popped from the heap.",
                 "tradeoff": "No cost, but only valid when you do not need all distances.", "impact": "low", "optimized_code": ""},
                {"title": "Array-based Dijkstra for dense graphs",
                 "bottleneck": "When m is close to n^2 the heap's log factor adds overhead.",
                 "suggestion": "Use the O(n^2) version that scans an array for the minimum unsettled node.",
                 "tradeoff": "Worse on sparse graphs, so it only pays off when m is about n^2.", "impact": "low", "optimized_code": ""},
            ],
            "pitfalls": [
                {"kind": "edge_case", "description": "Negative edge weights break Dijkstra; this code assumes all weights are non-negative.", "line": 26},
                {"kind": "overflow", "description": "dist[u] + w is safe because nodes with infinite distance are never expanded.", "line": 26},
                {"kind": "edge_case", "description": "Node ids are assumed to be in 1..n; out-of-range ids would write out of bounds.", "line": 14},
            ],
            "quality": {
                "clarity_score": 9,
                "naming_feedback": "adj, dist and pq are conventional and clear.",
                "structure_feedback": "Compact and idiomatic; structured bindings keep the relaxation loop readable.",
                "tips": ["A named constant such as INF = LLONG_MAX would make the checks self-explanatory."],
            },
        },
    },
    {
        "title": "Longest Increasing Subsequence O(n^2) - C++",
        "language": "C++",
        "problem": "Given an array of n integers, print the length of its longest strictly increasing subsequence.",
        "n_max": 100_000, "m_max": 1, "k_max": 1, "time_limit": 1.0,
        "code": _LIS,
        "demo": {
            "algorithm": "Longest Increasing Subsequence - quadratic DP",
            "category": "Dynamic Programming",
            "tags": ["dp", "lis", "subsequence"],
            "summary": "dp[i] is the length of the longest strictly increasing subsequence ending at index i. For every i the "
                       "code tries each earlier j with a[j] < a[i] and extends dp[j]. The answer is the maximum dp[i].",
            "line_blocks": [
                _block(1, 2, "Standard headers and namespace."),
                _block(4, 8, "Read n and the array. dp is initialised to 1 because every element alone is a subsequence."),
                _block(9, 9, "best tracks the maximum dp value seen."),
                _block(10, 15, "For each i, scan every j < i; when a[j] < a[i] the subsequence ending at j can be extended. "
                               "Then update best with dp[i].",
                       "The strict < gives strictly increasing; use <= for non-decreasing."),
                _block(16, 17, "Print the answer and return."),
            ],
            "complexity": {
                "time": "O(n^2)", "space": "O(n)", "ops_expression": "n * n / 2",
                "variables": {"n": "array length", "m": "-", "k": "-"},
                "derivation": "For index i the inner loop runs i times, so the total is 0 + 1 + ... + (n - 1) = n(n - 1) / 2, "
                              "which is O(n^2). Only the arrays a and dp are stored, so space is O(n).",
                "best_case": "O(n^2) - the loops do not depend on the data.",
                "worst_case": "O(n^2).",
            },
            "optimizations": [{
                "title": "Patience sorting with binary search",
                "bottleneck": "Lines 11-13: the inner loop compares every earlier element for every i, about 5*10^9 steps at n = 10^5.",
                "suggestion": "Keep a 'tails' array where tails[len-1] is the smallest possible tail of an increasing subsequence "
                              "of that length. Each element replaces the first tail >= x via lower_bound, or appends.",
                "tradeoff": "Drops the dp array, so reconstructing the actual subsequence needs extra parent bookkeeping.",
                "impact": "high", "optimized_code": _LIS_FAST,
            }],
            "pitfalls": [
                {"kind": "tle", "description": "At n = 10^5 the inner loop runs about 5*10^9 times, far beyond a 1-second limit.", "line": 11},
                {"kind": "edge_case", "description": "n = 0 prints 0, which is correct; make sure the problem guarantees n >= 1 if required.", "line": 6},
            ],
            "quality": {
                "clarity_score": 7,
                "naming_feedback": "dp and best are clear; a is conventional.",
                "structure_feedback": "Straightforward and correct, but the quadratic scan limits it to small n.",
                "tips": ["Comment what dp[i] means so the recurrence is obvious."],
            },
        },
    },
]


def find_sample(code: str, language: str) -> dict[str, Any] | None:
    target = _norm(code)
    for sample in SAMPLES:
        if sample["language"] == language and _norm(sample["code"]) == target:
            return sample
    return None
