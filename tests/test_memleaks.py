"""
Run continous layout calculations and monitor memory usage.

Layout should include border, padding, margin, and resizing/recalculating layout.
"""

import gc
import random
import tracemalloc

from stretchable import Node, Style

ITERATIONS: int = 1000
ALLOWED_BYTES_PER_ITER: int = 1024


def get_style(k: float = 1) -> Style:
    return Style(size=(100 * k, 100 * k), margin=10 * k, padding=10 * k, border=10 * k)


def setup_layout() -> Node:
    """ """
    root = Node(margin=10, padding=10, border=10)
    for i in range(3):
        root.add(Node(key=f"child{i}", style=get_style()))
    return root


def modify_layout(root: Node):
    """Modify layout in various ways to simulate real-world usage."""
    for i in range(3):
        child = root.find(f"child{i}")
        k = (1 + random.random()) / 2
        child.style = get_style(k)
    k = random.random()
    root.compute_layout()


def test_no_memleak():
    """Run repeated layout modifications and assert no growing memory leak."""

    root = setup_layout()
    memory_samples = []
    sample_interval = ITERATIONS // 10  # Take 10 samples throughout the run

    # warm-up
    for _ in range(5):
        modify_layout(root)

    gc.collect()
    tracemalloc.start()
    _, before_peak = tracemalloc.get_traced_memory()

    for i in range(ITERATIONS):
        modify_layout(root)

        if (i & 0x7F) == 0:
            # occasional GC helps avoid transient spikes being counted as leaks
            gc.collect()

        if i > 0 and i % sample_interval == 0:
            _, current_peak = tracemalloc.get_traced_memory()
            memory_increase = max(0, current_peak - before_peak)
            memory_samples.append((i, memory_increase))

    _, after_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_peak_increase = max(0, after_peak - before_peak)
    avg_per_iter = total_peak_increase / max(1, ITERATIONS)

    # Print memory growth pattern
    print("\nMemory growth pattern:")
    for iter_num, mem_increase in memory_samples:
        percentage = (iter_num / ITERATIONS) * 100
        kb_increase = mem_increase / 1024
        print(
            f"@ {percentage:3.0f}% ({iter_num:6d} iterations): {kb_increase:8.2f}KB ({kb_increase/iter_num if iter_num else 0:.2f} KB/iter)"
        )

    assert avg_per_iter <= ALLOWED_BYTES_PER_ITER, (
        f"Possible memory leak: peak increased by {total_peak_increase} bytes ({total_peak_increase/1024/1024:.2f} MB) "
        f"over {ITERATIONS} iterations (~{avg_per_iter:.1f} B/iter). "
        "Increase above threshold."
    )
