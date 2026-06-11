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
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


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

    # Propagate contextvars into worker threads (threads don't inherit
    # them), so per-call state like the MCP log-capture token survives.
    _caller_ctx = contextvars.copy_context()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batches
        future_to_idx = {
            executor.submit(_caller_ctx.copy().run, worker_fn, batch): idx
            for idx, batch in enumerate(batches)
        }

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
