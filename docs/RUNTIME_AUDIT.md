# CalculusSolver Runtime Documentation

This file documents the `calculussolver/` subproject runtime and audit notes. It does not replace the existing `ARCHITECTURE.md` or `GUIDE.md`; it complements them with practical project-structure and run-readiness notes.

## Purpose

CalculusSolver is the ML and symbolic-calculus subsystem. It contains:

- A solver API with `/health`, `/solve`, and `/validate`.
- A fallback deterministic solver for polynomial operations.
- Neural inference code for checkpoint-backed solving.
- PyTorch model architecture and training scripts.
- JavaScript SLaNg serialization, validation, and verification bridges.
- Data-generation and evaluation scripts.
- Streamlit and website frontends for solver demos/docs.

## Main Folders

| Path | Purpose |
| --- | --- |
| `api/` | Starlette solver API |
| `inference/` | Neural inference, fallback solver, beam search, verifier |
| `model/` | PyTorch architecture |
| `training/` | Pretraining, fine-tuning, verifier loop, configs |
| `data_pipeline/` | Synthetic data generation and verification scripts |
| `tokenizer/` | SLaNg tokenizer and vocabulary |
| `data/` | Dataset files |
| `eval/` | Evaluation scripts |
| `website/` | React/Vite explanatory site |
| `slang/` | Bundled SLaNg JavaScript math library |
| `slang/website/` | Svelte/Vite SLaNg site |

## Local Commands

Solver API:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.app:app --reload --port 8001
```

Streamlit UI:

```bash
streamlit run streamlit_app.py
```

Solver website:

```bash
cd website
npm install
npm run dev
```

SLaNg website:

```bash
cd slang/website
npm install
npm run dev
```

## Runtime Modes

The solver API starts in one of two modes:

- `neural`: a checkpoint is found and loaded.
- `fallback`: no checkpoint is found, so the deterministic fallback solver is used.

Fallback mode supports a smaller feature set:

- `diff`
- `partial`
- `integrate`
- `gradient`
- `tangent_line`

Full neural behavior requires a trained checkpoint under `checkpoints/` or a valid `MODEL_PATH`.

## Important Runtime Contracts

`POST /solve` expects:

```json
{
  "input": {
    "op": "diff",
    "var": "x",
    "expr": {
      "numi": { "terms": [{ "coeff": 3, "var": { "x": 2 } }] },
      "deno": 1
    }
  }
}
```

Fallback response shape:

```json
{
  "status": "solved",
  "expr": {},
  "steps": [],
  "latex": "...",
  "confidence": 1.0,
  "verified": true,
  "warning": "Fallback mode — no neural checkpoint loaded.",
  "rule": "power_rule",
  "mode": "fallback"
}
```

## Current Technical Debt

- Some SLaNg package exports point to root files that are not present in `calculussolver/slang/`.
- Some solver/data-pipeline imports expect SLaNg files at paths that do not match the current folder layout.
- Node subprocess bridges should have timeouts and clearer failure handling.
- Requirements should be split into runtime/API/training/dev dependency groups.
- Runtime code currently zeroes some tree-position structures that the architecture docs describe as meaningful inputs.

## Recommended Next Docs

- `docs/API_CONTRACT.md`: exact solver API payload examples.
- `docs/CHECKPOINTS.md`: where checkpoints live and how `MODEL_PATH` is resolved.
- `docs/SLANG_INTEGRATION.md`: expected package exports and import paths.
- `docs/TESTING.md`: fallback, verifier, tokenizer, and package-export smoke tests.
