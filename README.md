# ALGOVISTA — Interactive Data Structures & Algorithms Visual Learning Platform

ALGOVISTA is a 100% client-side interactive Data Structures & Algorithms visual learning platform built with **Vite + React 19 + TypeScript + Tailwind CSS + Framer Motion + Recharts**. All user state (progress tracking, quiz scores, GitHub-style daily streak heatmap, problem notes, bookmarks, and theme preferences) persists natively in `localStorage`.

---

## ✨ Features & Architecture

1. **12 Interactive 60FPS Visualizers (`/visualizers/:id`)**:
   - **Sorting Algorithms**: Bubble, Selection, Insertion, Merge, and Quick Sort with real-time Comparison & Swap counters, Array Size slider (`N = 5..50`), Speed slider (`0.25x..2.0x`), and step-by-step playback.
   - **Graph BFS/DFS Explorer**: Click-to-add vertices and edges on an interactive SVG stage, step through Breadth-First Queue or Depth-First Stack traversals with active pseudocode line highlighting.
   - **Binary Tree / BST / Heap**: Node insertion with animated Inorder, Preorder, and Postorder traversals.
   - **Linear & Hashing Structures**: Static/Dynamic Arrays, Singly Linked List, LIFO Stack, FIFO Queue, Separate Chaining HashMap, Binary Search, and Recursion Call Stack Tree.

2. **30 Browser-Runnable Coding Problems (`/problems/:topic/:slug`)**:
   - 5 curated Easy/Medium problems across each of 6 core topics (`Arrays`, `Strings`, `Linked Lists`, `Trees`, `Graphs`, `Dynamic Programming`).
   - **Sandboxed Browser CodeRunner**: Evaluates JavaScript solutions in-browser via `new Function()` against 3 test cases with instant Pass/Fail assertions and execution time.
   - **Progressive Hints & Reference Solutions**: 3 collapsible hints per problem plus Brute Force vs Optimal Big-O solution tabs.
   - **Personal Notes**: Markdown-ready revision notes saved per problem slug directly to `localStorage`.

3. **Mastery Quizzes (`/quiz/:topic`)**:
   - 10-question timed MCQ quizzes per topic (Arrays, Trees, Graphs, DP) plus a cross-topic **Mixed Mastery** quiz (`/quiz/mixed`).
   - Instant algorithmic explanation on submit and a **Retry Wrong-Only** mode.

4. **Guided Learning Paths (`/learn`, `/learn/:id`)**:
   - Four structured paths (Foundations, Pointers & Strings, Data Structures, Graphs & DP) that mix workbenches, problems and quizzes in a recommended order with a lock-step progress rail and a "next step" shortcut.

---

## 🗂 Folder Structure

```
src/
├── App.tsx                       # Root application container
├── main.tsx                      # Entry point
├── routes.tsx                    # All 7 client-side routes
├── store/
│   └── ProgressContext.tsx       # Global localStorage state & actions
├── hooks/
│   ├── useLocalStorage.ts        # Type-safe storage sync hook
│   └── useStreak.ts              # Consecutive daily streak calculator
├── components/
│   ├── Navbar.tsx                # Top nav + ⌘K instant search + mobile tab bar
│   ├── ThemeToggle.tsx           # Dark/Light mode switcher
│   ├── ProgressRing.tsx          # Circular SVG progress gauge
│   ├── StreakHeatmap.tsx         # GitHub-style 16-week contribution grid
│   ├── VisualizerCanvas.tsx      # Interactive SVG stage wrapper
│   ├── ControlBar.tsx            # Play/Pause/Step/Reset/Randomize bar
│   ├── SpeedControl.tsx          # 0.25x - 2.0x speed slider
│   ├── PseudoCodePanel.tsx       # Line-highlighted pseudocode + operation log
│   ├── ComplexityBadge.tsx       # Time/Space Big-O pill
│   ├── ProblemTable.tsx          # Instant search, filter, and sort table
│   ├── CodeRunner.tsx            # Browser sandboxed JS test runner
│   ├── QuizEngine.tsx            # 10-question MCQ quiz with timer
│   ├── EmptyState.tsx            # Empty filter state
│   └── Footer.tsx                # Footer navigation
├── visualizers/
│   ├── SortingVisualizer.tsx     # Bubble/Selection/Insertion/Merge/Quick
│   ├── GraphVisualizer.tsx       # Click-to-edit BFS/DFS graph canvas
│   ├── TreeVisualizer.tsx        # Binary Tree / BST / Heap traversals
│   └── LinearVisualizer.tsx      # Array/LinkedList/Stack/Queue/HashMap
    ├── pages/
    │   ├── LandingPage.tsx           # Hero with live sorting mini-demo
    │   ├── DashboardPage.tsx         # Streak heatmap, progress ring, Recharts
    │   ├── VisualizersListPage.tsx   # 12 visualizer cards grid
    │   ├── VisualizerDetailPage.tsx  # Universal workbench host
    │   ├── GuidedPathsPage.tsx       # Learning paths browser
    │   ├── GuidedPathDetailPage.tsx  # Lock-step path with next-step CTA
    │   ├── ProblemListPage.tsx       # Topic problem table
    │   ├── ProblemDetailPage.tsx     # Problem detail + CodeRunner + Notes
    │   └── QuizPage.tsx              # Topic + mixed quiz host
    └── data/
        ├── curriculum.ts             # Topics & 12 visualizers metadata
        ├── problems.ts               # 30 problems with test cases & solutions
        ├── quizzes.ts                # 10 Qs per topic + mixed MCQ quizzes
        ├── learningPaths.ts          # 4 guided learning paths
        └── pseudocode.ts             # Algorithm pseudocode lines
```

---

## 💾 LocalStorage Schema (`algovista_store_v1`)

```json
{
  "progress": {
    "two-sum": "Done",
    "maximum-subarray": "Doing"
  },
  "quizzes": {
    "arrays": 90,
    "trees": 80,
    "graphs": 60,
    "dp": 50
  },
  "streak": ["2026-03-20", "2026-03-21", "2026-03-22"],
  "notes": {
    "two-sum": "Store seen[nums[i]] = i in Map for O(1) complement lookup."
  },
  "bookmarks": ["sorting", "two-sum"],
  "dailyGoalDone": {
    "2026-03-22": true
  },
  "lastVisited": {
    "type": "visualizer",
    "title": "Sorting Algorithms",
    "path": "/visualizers/sorting",
    "subtitle": "Interactive Big-O & Step Debugger"
  }
}
```

---

## 🚀 Deployment & SPA Fallback (D12)

Because Algovista uses HTML5 client-side routing (`BrowserRouter`), static hosts must rewrite non-asset requests to `/index.html`:

### Vercel
Configured in `apps/web/vercel.json`:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

### Netlify / Cloudflare Pages
Configured in `apps/web/public/_redirects`:
```
/*    /index.html   200
```

### Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/algovista/apps/web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

