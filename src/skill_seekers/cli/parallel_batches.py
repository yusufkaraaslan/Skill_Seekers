#!/usr/bin/env python3
"""
Shared ThreadPoolExecutor batching for AI enhancers.

Extracted from three near-identical copies (Phase 3.1 of
docs/UNIFICATION_PLAN.md, safe slice):
- ai_enhancer.PatternEnhancer._enhance_patterns_parallel
- ai_enhancer.TestExampleEnhancer._enhance_examples_parallel
- unified_enhancer.UnifiedEnhancer._enhance_parallel

Deliberately a standalone module (not part of ai_enhancer.py) so
unified_enhancer.py can use it without coupling the two enhancer
hierarchies — their full merge is deferred.
"""

import contextvars
import logging
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


def context_propagating_submit(executor: ThreadPoolExecutor) -> Callable[..., Future]:
    """Return a ``submit(fn, *args, **kwargs)`` wrapper for ``executor`` that
    runs each task in a copy of the context captured at THIS call.

    Worker threads don't inherit contextvars (unlike asyncio tasks), so
    per-call state — e.g. the MCP server's log-capture token — would be lost
    in worker-thread logging without this. Each task gets its own copy of the
    captured context because a Context can only be entered by one thread at a
    time.
    """
    caller_ctx = contextvars.copy_context()

    def submit(fn: Callable, /, *args, **kwargs) -> Future:
        return executor.submit(caller_ctx.copy().run, fn, *args, **kwargs)

    return submit


def run_batches_parallel(
    batches: list[list[dict]],
    worker_fn: Callable[[list[dict]], list[dict]],
    max_workers: int,
    *,
    log: Callable[[str], None] = logger.info,
    warn: Callable[[str], None] = logger.warning,
) -> list[list[dict]]:
    """ThreadPoolExecutor over batches with contextvars propagation, ordered
    results, progress logging, and per-batch fallback-to-unenhanced.

    Args:
        batches: List of item batches; each batch is passed to worker_fn.
        worker_fn: Callable enhancing one batch and returning the result list.
        max_workers: ThreadPoolExecutor worker count.
        log: Progress logger (default: this module's logger.info). Pass the
            caller's logger.info to keep log records under the caller's name.
        warn: Failure logger (default: this module's logger.warning).

    Returns:
        Per-batch results in input order. A batch whose worker raised is
        returned unenhanced (the original batch).
    """
    results: list[list[dict] | None] = [None] * len(batches)  # Preserve order

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batches (with contextvars propagated into the workers)
        submit = context_propagating_submit(executor)
        future_to_idx = {submit(worker_fn, batch): idx for idx, batch in enumerate(batches)}

        # Collect results as they complete
        completed = 0
        total = len(batches)
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
                completed += 1
                # Show progress: always for small jobs (<10), every 5 for larger jobs
                if total < 10 or completed % 5 == 0 or completed == total:
                    log(f"   Progress: {completed}/{total} batches completed")
            except Exception as e:
                warn(f"⚠️  Batch {idx} failed: {e}")
                results[idx] = batches[idx]  # Return unenhanced on failure

    return results  # type: ignore[return-value]  # every index is filled above


def flatten_batch_results(results: list[list[dict]]) -> list[dict]:
    """Flatten per-batch results, skipping empty/None batches (shared tail of
    all three original copies)."""
    enhanced: list[dict] = []
    for batch_result in results:
        if batch_result:
            enhanced.extend(batch_result)
    return enhanced
