"""
Shared utilities for drifting analysis experiments.

Provides:
- Sliced Wasserstein Distance (SWD) between representation distributions
- Linear CKA similarity between paired representation matrices
- Headless-safe matplotlib configuration
- Data loading from HuggingFace datasets
- Hidden state collection helpers
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
from loguru import logger


# ---------------------------------------------------------------------------
# Matplotlib helpers (headless-safe) — mirrors src/probe/ot/ot_probe_utils.py
# ---------------------------------------------------------------------------


def configure_matplotlib_for_env() -> None:
    import matplotlib

    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        matplotlib.use("Agg")


def save_figure(
    fig,
    *,
    name: str,
    save_dir: Optional[str] = None,
    dpi: int = 300,
    formats: Tuple[str, ...] = ("pdf", "png"),
) -> None:
    import matplotlib.pyplot as plt

    out_dir = Path(save_dir) if save_dir else Path(__file__).resolve().parent / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    for fmt in formats:
        out_path = out_dir / f"{name}.{fmt}"
        fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
        logger.info(f"Saved figure to {out_path}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def sliced_wasserstein_distance(
    X: np.ndarray, Y: np.ndarray, n_projections: int = 200, seed: int = 42
) -> float:
    """
    Compute Sliced Wasserstein Distance between two point clouds.

    Args:
        X: (n, d) array of representations
        Y: (m, d) array of representations
        n_projections: number of random 1D projections
        seed: random seed for reproducibility

    Returns:
        Scalar SWD value
    """
    rng = np.random.RandomState(seed)
    d = X.shape[1]
    n = min(len(X), len(Y))
    distances = []
    for _ in range(n_projections):
        theta = rng.randn(d).astype(np.float64)
        theta /= np.linalg.norm(theta)
        Xp = X.astype(np.float64) @ theta
        Yp = Y.astype(np.float64) @ theta
        # Subsample to equal size
        Xp_sub = np.sort(rng.choice(Xp, n, replace=False))
        Yp_sub = np.sort(rng.choice(Yp, n, replace=False))
        distances.append(np.mean(np.abs(Xp_sub - Yp_sub)))
    return float(np.mean(distances))


def linear_cka(X: np.ndarray, Y: np.ndarray) -> float:
    """
    Compute Linear CKA (Centered Kernel Alignment) between paired representations.

    Args:
        X: (n, d1) array -- representations at layer l
        Y: (n, d2) array -- representations at layer l+1 (same tokens)

    Returns:
        Scalar CKA similarity in [0, 1]. Higher = more similar.
    """
    X = X.astype(np.float64)
    Y = Y.astype(np.float64)
    X = X - X.mean(axis=0)
    Y = Y - Y.mean(axis=0)

    hsic_xy = np.linalg.norm(X.T @ Y, "fro") ** 2
    hsic_xx = np.linalg.norm(X.T @ X, "fro") ** 2
    hsic_yy = np.linalg.norm(Y.T @ Y, "fro") ** 2

    return float(hsic_xy / (np.sqrt(hsic_xx * hsic_yy) + 1e-10))


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_text_examples(
    num_examples: int = 200, max_length: int = 512, seed: int = 42
) -> list[str]:
    """
    Load text examples from WikiText-103 validation set.

    Returns:
        List of text strings, each long enough to tokenize to ~max_length tokens.
    """
    from datasets import load_dataset

    ds = load_dataset("wikitext", "wikitext-103-raw-v1", split="validation")
    # Filter to non-empty, reasonably long paragraphs
    texts = [t for t in ds["text"] if len(t.split()) > max_length // 2]
    rng = np.random.RandomState(seed)
    rng.shuffle(texts)
    return texts[:num_examples]


def tokenize_examples(
    texts: list[str], tokenizer, max_length: int = 512
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Tokenize a list of texts with truncation and padding.

    Returns:
        input_ids: (N, max_length)
        attention_mask: (N, max_length)
    """
    encodings = tokenizer(
        texts,
        max_length=max_length,
        truncation=True,
        padding="max_length",
        return_tensors="pt",
    )
    return encodings["input_ids"], encodings["attention_mask"]


# ---------------------------------------------------------------------------
# Hidden state collection
# ---------------------------------------------------------------------------


def collect_hidden_states_frozen_llm(
    model,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    batch_size: int = 4,
    device: str = "cuda:0",
) -> list[np.ndarray]:
    """
    Run frozen LLM and collect hidden states at all layers.

    Args:
        model: AutoModelForCausalLM (frozen, eval mode)
        input_ids: (N, seq_len)
        attention_mask: (N, seq_len)
        batch_size: inference batch size
        device: device string

    Returns:
        List of L+1 arrays, each (total_non_padding_tokens, hidden_dim).
        Index 0 = embedding layer, index L = last transformer layer.
    """
    model.eval()
    num_examples = input_ids.shape[0]
    all_hidden = None  # will be list of lists

    for start in range(0, num_examples, batch_size):
        end = min(start + batch_size, num_examples)
        ids = input_ids[start:end].to(device)
        mask = attention_mask[start:end].to(device)

        with torch.no_grad():
            outputs = model(
                input_ids=ids, attention_mask=mask, output_hidden_states=True
            )

        # outputs.hidden_states: tuple of (batch, seq_len, hidden_dim)
        if all_hidden is None:
            all_hidden = [[] for _ in range(len(outputs.hidden_states))]

        for layer_idx, hs in enumerate(outputs.hidden_states):
            # Extract only non-padding tokens
            hs_cpu = hs.float().cpu().numpy()
            mask_cpu = mask.cpu().numpy().astype(bool)
            for b in range(hs_cpu.shape[0]):
                all_hidden[layer_idx].append(hs_cpu[b, mask_cpu[b], :])

    # Concatenate across examples
    assert all_hidden is not None, "No examples were processed"
    return [np.concatenate(layer_list, axis=0) for layer_list in all_hidden]


def collect_hidden_states_icae_compression(
    model,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    batch_size: int = 4,
    device: str = "cuda:0",
) -> list[np.ndarray]:
    """
    Run ICAE compressor and collect hidden states of compression (memory) tokens
    at all layers.

    The ICAE model appends ``num_memory_tokens`` learnable tokens after the input.
    At each layer, the compression token representations are the last
    ``num_memory_tokens`` positions.

    Args:
        model: ICAE model instance (eval mode)
        input_ids: (N, seq_len) -- context token IDs
        attention_mask: (N, seq_len)
        batch_size: inference batch size
        device: device string

    Returns:
        List of L+1 arrays, each (total_compression_tokens, hidden_dim).
    """
    model.eval()
    num_memory_tokens = model.num_memory_tokens
    num_examples = input_ids.shape[0]
    all_hidden = None

    for start in range(0, num_examples, batch_size):
        end = min(start + batch_size, num_examples)
        ids = input_ids[start:end].to(device)
        mask = attention_mask[start:end].to(device)

        # Prepare inputs exactly as ICAE.compress does
        inputs_embeds = model.compressor.get_input_embeddings()(ids)
        bs = inputs_embeds.shape[0]
        memory_embeds = model.memory_embeddings.repeat(bs, 1, 1).to(
            device=inputs_embeds.device, dtype=inputs_embeds.dtype
        )
        encoder_inputs = torch.cat([inputs_embeds, memory_embeds], dim=1)
        mem_mask = torch.ones(
            bs, num_memory_tokens, device=mask.device, dtype=mask.dtype
        )
        encoder_mask = torch.cat([mask, mem_mask], dim=1)

        with torch.no_grad():
            outputs = model.compressor(
                inputs_embeds=encoder_inputs,
                attention_mask=encoder_mask,
                output_hidden_states=True,
            )

        if all_hidden is None:
            all_hidden = [[] for _ in range(len(outputs.hidden_states))]

        for layer_idx, hs in enumerate(outputs.hidden_states):
            # Memory tokens are the last num_memory_tokens positions
            mem_hs = hs[:, -num_memory_tokens:, :].detach().float().cpu().numpy()
            # Flatten batch: (batch, num_mem, hidden) -> (batch*num_mem, hidden)
            all_hidden[layer_idx].append(mem_hs.reshape(-1, mem_hs.shape[-1]))

    assert all_hidden is not None, "No examples were processed"
    return [np.concatenate(layer_list, axis=0) for layer_list in all_hidden]
