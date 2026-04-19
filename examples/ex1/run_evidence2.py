#!/usr/bin/env python3
"""
Evidence 2: Distributional Drift -- Normal Context Tokens vs ICAE Compression Tokens.

Measures per-layer-transition drift using:
  - Sliced Wasserstein Distance (SWD): distance between representations at
    consecutive layers (higher = more drift)

Usage::
    python -m src.probe.drifting_analysis.run_evidence2 \
        --base_model_path /path/to/Llama-3.2-1B \
        --icae_checkpoint /path/to/icae_checkpoint \
        --num_examples 200 --max_length 512 --batch_size 4

    Experiment
    python -m src.probe.drifting_analysis.run_evidence2 --base_model_path=/users/k21025815/storage/checkpoints/llama-3.2-1b --icae_checkpoint=/users/k21025815/storage/CompressIn/backup/training_outputs/512-128-icae-gpu/checkpoint-763 --num_examples=20
"""

import argparse
import gc
import os
import sys

import numpy as np
import torch
from loguru import logger

from utils import (
    configure_matplotlib_for_env,
    save_figure,
    load_text_examples,
    tokenize_examples,
    collect_hidden_states_frozen_llm,
    collect_hidden_states_icae_compression,
    sliced_wasserstein_distance,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evidence 2: Distributional drift comparison"
    )
    parser.add_argument(
        "--base_model_path",
        type=str,
        required=True,
        help="Path to frozen Llama-3.2-1B base model",
    )
    parser.add_argument(
        "--icae_checkpoint",
        type=str,
        required=True,
        help="Path to trained ICAE checkpoint",
    )
    parser.add_argument("--num_examples", type=int, default=200)
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument(
        "--swd_n_projections",
        type=int,
        default=200,
        help="Number of random projections for SWD",
    )
    parser.add_argument(
        "--max_tokens_per_layer",
        type=int,
        default=5000,
        help="Max tokens to subsample per layer for metrics (memory)",
    )
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--save_dir", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--reuse",
        action="store_true",
        help="Skip model forwards and metric computation; load cached SWD "
             "values from <save_dir>/evidence2_swd_values.npz and re-plot.",
    )
    return parser.parse_args()


def subsample(
    arrays: list[np.ndarray], max_tokens: int, seed: int = 42
) -> list[np.ndarray]:
    """Subsample each array to max_tokens rows if larger."""
    rng = np.random.RandomState(seed)
    result = []
    for arr in arrays:
        if arr.shape[0] > max_tokens:
            idx = rng.choice(arr.shape[0], max_tokens, replace=False)
            result.append(arr[idx])
        else:
            result.append(arr)
    return result


def compute_drift_metrics(
    hidden_states: list[np.ndarray], n_projections: int, seed: int = 42
):
    """
    Compute SWD for each consecutive layer pair.

    Args:
        hidden_states: list of L+1 arrays, each (n_tokens, hidden_dim)
        n_projections: number of projections for SWD

    Returns:
        swd_values: (L,) array -- SWD for transitions 0->1, 1->2, ..., (L-1)->L
    """
    num_transitions = len(hidden_states) - 1
    swd_values = np.zeros(num_transitions)

    for ell in range(num_transitions):
        X = hidden_states[ell]
        Y = hidden_states[ell + 1]
        n = min(X.shape[0], Y.shape[0])
        swd_values[ell] = sliced_wasserstein_distance(
            X[:n], Y[:n], n_projections=n_projections, seed=seed
        )
        logger.info(f"  Transition {ell}->{ell+1}: SWD={swd_values[ell]:.6f}")

    return swd_values


def compute_swd_from_origin(
    hidden_states: list[np.ndarray], n_projections: int, seed: int = 42
) -> np.ndarray:
    """
    Compute SWD(layer_0, layer_ell) for each layer ell = 1, ..., L.

    Returns:
        swd_from_origin: (L,) array -- SWD from layer 0 to each subsequent layer
    """
    num_layers = len(hidden_states)
    swd_from_origin = np.zeros(num_layers - 1)
    X0 = hidden_states[0]

    for ell in range(1, num_layers):
        Y = hidden_states[ell]
        n = min(X0.shape[0], Y.shape[0])
        swd_from_origin[ell - 1] = sliced_wasserstein_distance(
            X0[:n], Y[:n], n_projections=n_projections, seed=seed
        )
        logger.info(
            f"  SWD(layer_0, layer_{ell}): {swd_from_origin[ell - 1]:.6f}"
        )

    return swd_from_origin


def _plot_pareto_swd(normal_step, icae_step, normal_line, icae_line,
                     x_labels, title, line_ylabel, filename,
                     bar_suffix="per-transition", line_suffix="cumulative",
                     save_dir=None):
    """
    Pareto-style plot: grouped bars for per-transition SWD (left y-axis, log),
    lines for a second SWD measure (right y-axis).
    """
    configure_matplotlib_for_env()
    import matplotlib.pyplot as plt

    n = len(normal_step)
    x = np.arange(n)
    bar_width = 0.35

    fig, ax1 = plt.subplots(figsize=(11, 5.5))

    # --- Bars: per-transition SWD (left axis, log scale) ---
    ax1.bar(
        x - bar_width / 2, normal_step, bar_width,
        color="#2a9d8f", alpha=0.55, label=f"Normal ({bar_suffix})",
    )
    ax1.bar(
        x + bar_width / 2, icae_step, bar_width,
        color="#e76f51", alpha=0.55, label=f"ICAE ({bar_suffix})",
    )
    ax1.set_yscale("log")
    ax1.set_xlabel("Layer Transition", fontsize=14)
    ax1.set_ylabel("Per-Transition SWD (log)", fontsize=13)
    ax1.set_xticks(x)
    ax1.set_xticklabels(x_labels, fontsize=10, rotation=45)
    ax1.tick_params(axis="y", labelsize=11)

    # --- Lines: second SWD measure (right axis) ---
    ax2 = ax1.twinx()
    ax2.plot(
        x, normal_line, color="#264653", linewidth=2.5,
        marker="o", markersize=7, label=f"Normal ({line_suffix})",
    )
    ax2.plot(
        x, icae_line, color="#c1440e", linewidth=2.5,
        marker="s", markersize=7, label=f"ICAE ({line_suffix})",
    )
    ax2.set_ylabel(line_ylabel, fontsize=13)
    ax2.tick_params(axis="y", labelsize=11)

    # --- Combined legend ---
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=11, loc="upper left")

    ax1.set_title(title, fontsize=14)
    ax1.grid(True, linestyle="--", alpha=0.25, which="both")
    fig.tight_layout()

    save_figure(fig, name=filename, save_dir=save_dir)


def plot_swd_cumsum(normal_swd, icae_swd, save_dir=None):
    """Plot A: per-transition bars + running-sum cumulative line."""
    n = len(normal_swd)
    x_labels = [f"{i}\u2192{i+1}" for i in range(n)]
    normal_cumul = np.cumsum(normal_swd)
    icae_cumul = np.cumsum(icae_swd)

    _plot_pareto_swd(
        normal_swd, icae_swd, normal_cumul, icae_cumul,
        x_labels=x_labels,
        title="Distributional Drift",
        line_ylabel="Cumulative SWD",
        filename="evidence2_swd_cumsum",
        bar_suffix="per-transition",
        line_suffix="cumulative",
        save_dir=save_dir,
    )


def plot_swd_from_origin(normal_swd_step, icae_swd_step,
                         normal_swd_origin, icae_swd_origin, save_dir=None):
    """Plot B: per-transition bars + SWD(layer_0, layer_ell) line."""
    n = len(normal_swd_step)
    x_labels = [f"{i}\u2192{i+1}" for i in range(n)]

    _plot_pareto_swd(
        normal_swd_step, icae_swd_step,
        normal_swd_origin, icae_swd_origin,
        x_labels=x_labels,
        title="Distributional Drift",
        line_ylabel="SWD (embedding, layer \u2113)",
        filename="evidence2_swd_from_origin",
        bar_suffix="per-transition",
        line_suffix="from-embedding",
        save_dir=save_dir,
    )


def _cache_path(save_dir):
    from pathlib import Path
    out_dir = Path(save_dir) if save_dir else Path(__file__).resolve().parent / "plots"
    return out_dir / "evidence2_swd_values.npz"


def save_swd_cache(save_dir, normal_swd, icae_swd,
                   normal_swd_origin, icae_swd_origin):
    path = _cache_path(save_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        normal_swd=normal_swd,
        icae_swd=icae_swd,
        normal_swd_origin=normal_swd_origin,
        icae_swd_origin=icae_swd_origin,
    )
    logger.info(f"Saved SWD cache to {path}")


def load_swd_cache(save_dir):
    path = _cache_path(save_dir)
    if not path.exists():
        raise FileNotFoundError(
            f"--reuse was set but cache file not found at {path}. "
            f"Run once without --reuse to populate the cache."
        )
    data = np.load(path)
    logger.info(f"Loaded SWD cache from {path}")
    return (
        data["normal_swd"],
        data["icae_swd"],
        data["normal_swd_origin"],
        data["icae_swd_origin"],
    )


def main():
    args = parse_args()

    if args.reuse:
        logger.info("--reuse set: skipping model forwards, loading cached SWD values.")
        (normal_swd, icae_swd,
         normal_swd_origin, icae_swd_origin) = load_swd_cache(args.save_dir)

        plot_swd_cumsum(normal_swd, icae_swd, save_dir=args.save_dir)
        plot_swd_from_origin(normal_swd, icae_swd,
                             normal_swd_origin, icae_swd_origin,
                             save_dir=args.save_dir)
        logger.info("Done. Plots re-rendered from cache.")
        return

    if args.device is None:
        from src.device_utils import get_device_module

        _, device_type = get_device_module()
        args.device = f"{device_type}:0" if device_type != "cpu" else "cpu"

    logger.info(f"Device: {args.device}")

    # --- Load data ---
    from transformers import AutoModelForCausalLM, AutoTokenizer

    logger.info(f"Loading {args.num_examples} text examples")
    texts = load_text_examples(
        num_examples=args.num_examples, max_length=args.max_length, seed=args.seed
    )

    # --- Phase 1: Normal context tokens ---
    logger.info(f"Loading frozen LLM from {args.base_model_path}")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model_path)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model_path,
        torch_dtype=torch.bfloat16,
        attn_implementation="eager",
    ).to(args.device)
    model.eval()

    input_ids, attention_mask = tokenize_examples(
        texts, tokenizer, max_length=args.max_length
    )

    logger.info("Collecting hidden states for normal context tokens...")
    normal_hidden = collect_hidden_states_frozen_llm(
        model, input_ids, attention_mask, args.batch_size, args.device
    )
    logger.info(
        f"Collected {len(normal_hidden)} layers, "
        f"{normal_hidden[0].shape[0]} total tokens"
    )

    # Free frozen LLM memory
    del model
    gc.collect()
    if "cuda" in args.device:
        torch.cuda.empty_cache()

    # --- Phase 2: ICAE compression tokens ---
    logger.info(f"Loading ICAE model from {args.icae_checkpoint}")
    from src.evaluation.utils_eval import get_model_and_tokenizer

    icae_model, icae_tokenizer = get_model_and_tokenizer(
        model_folder=args.icae_checkpoint,
        device=args.device,
        attn_implementation="eager",
    )

    # Re-tokenize with ICAE's tokenizer (should be same but be safe)
    icae_input_ids, icae_attention_mask = tokenize_examples(
        texts, icae_tokenizer, max_length=args.max_length
    )

    logger.info("Collecting hidden states for ICAE compression tokens...")
    icae_hidden = collect_hidden_states_icae_compression(
        icae_model, icae_input_ids, icae_attention_mask, args.batch_size, args.device
    )
    logger.info(
        f"Collected {len(icae_hidden)} layers, "
        f"{icae_hidden[0].shape[0]} total compression tokens"
    )

    del icae_model
    gc.collect()
    if "cuda" in args.device:
        torch.cuda.empty_cache()

    # --- Subsample for memory efficiency ---
    normal_hidden = subsample(normal_hidden, args.max_tokens_per_layer, args.seed)
    icae_hidden = subsample(icae_hidden, args.max_tokens_per_layer, args.seed)

    # --- Compute per-transition metrics ---
    logger.info("Computing per-transition SWD for normal context tokens...")
    normal_swd = compute_drift_metrics(
        normal_hidden, args.swd_n_projections, args.seed
    )

    logger.info("Computing per-transition SWD for ICAE compression tokens...")
    icae_swd = compute_drift_metrics(
        icae_hidden, args.swd_n_projections, args.seed
    )

    # --- Compute from-origin SWD ---
    logger.info("Computing SWD from layer 0 for normal context tokens...")
    normal_swd_origin = compute_swd_from_origin(
        normal_hidden, args.swd_n_projections, args.seed
    )

    logger.info("Computing SWD from layer 0 for ICAE compression tokens...")
    icae_swd_origin = compute_swd_from_origin(
        icae_hidden, args.swd_n_projections, args.seed
    )

    # --- Cache values so --reuse can skip all the above next time ---
    save_swd_cache(args.save_dir, normal_swd, icae_swd,
                   normal_swd_origin, icae_swd_origin)

    # --- Plot ---
    plot_swd_cumsum(normal_swd, icae_swd, save_dir=args.save_dir)
    plot_swd_from_origin(normal_swd, icae_swd,
                         normal_swd_origin, icae_swd_origin,
                         save_dir=args.save_dir)
    logger.info("Done. Plots saved.")


if __name__ == "__main__":
    main()
