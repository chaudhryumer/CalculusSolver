# Dataset Engine Evaluation Report

This report summarizes the structure, distribution, and validation metrics of the SLaNg dataset synthesized for training and evaluating the neural calculus solver.

---

## Dataset Distribution Overview

Following the version 1.2 updates to address the lack of out-of-domain evaluation capability, the dataset generation pipeline was scaled to **125,000 total unique mathematical samples** distributed across 10 distinct mathematical rules.

### Distribution by Rule

| Rule / Concept | Associated Generator | Sample Count | Percentage |
| :--- | :--- | :--- | :--- |
| **Power Rule** | `generate_single_term_diff` | 35,000 | 28.0% |
| **Sum/Difference Rule** | `generate_multi_term_diff` | 25,000 | 20.0% |
| **Multivariable (Partial)** | `generate_multivar_diff` | 20,000 | 16.0% |
| **Constant Rule** | `generate_constant_term` | 10,000 | 8.0% |
| **Negative Exponents** | `generate_negative_exp_diff` | 10,000 | 8.0% |
| **Trigonometric: Sine** | `generate_sin_diff` | 5,000 | 4.0% |
| **Trigonometric: Cosine** | `generate_cos_diff` | 5,000 | 4.0% |
| **Trigonometric: Tangent** | `generate_tan_diff` | 5,000 | 4.0% |
| **Exponential** | `generate_exp_diff` | 5,000 | 4.0% |
| **Natural Logarithm** | `generate_ln_diff` | 5,000 | 4.0% |
| **Total Split Metrics** | — | **125,000** | **100%** |

---

## Split Strategy

The synthesized dataset is split deterministically using a fixed seed (`42`) into three main directory partitions located inside `data/splits/`:

*   **Training Set (90%):** 112,500 samples
*   **Validation Set (5%):** 6,250 samples
*   **Test Set (5%):** 6,250 samples

---

## Validation & Integrity

*   **Vocab-Bounded Verification:** Every generated sample undergoes automated verification to ensure that both input coefficient/exponent parameters and output derivatives stay safely within the range defined in `tokenizer/vocab.json`.
*   **No Naive Shortcuts:** Trigonometric generators incorporate dynamic inner multiplier coefficients ($a \cdot x$) to prevent neural paths from shortcut-memorizing simple string identity rules.
*   **Token-Level Roundtripping:** Verification asserts that $100\%$ of generated symbols map back to assigned structural IDs instead of silently dropping to padding tokens.