import os
import sys
from pathlib import Path

from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.routes.solve import router as solve_router
from api.routes.validate import router as validate_router
from inference.solve import CalculusSolverInference

app = FastAPI(title="CalculusSolver API")


def _resolve_model_path() -> str:
    candidate_paths = []
    env_path = os.environ.get("MODEL_PATH")
    if env_path:
        configured_path = Path(env_path)
        candidate_paths.append(
            configured_path if configured_path.is_absolute() else ROOT / configured_path
        )
    candidate_paths.extend(
        [
            ROOT / "checkpoints" / "final" / "best.pt",
            ROOT / "checkpoints" / "sft" / "best.pt",
            ROOT / "checkpoints" / "pretrain" / "best.pt",
        ]
    )

    for path in candidate_paths:
        if path.exists():
            return str(path)

    raise FileNotFoundError(
        "No model checkpoint found. Tried: "
        + ", ".join(str(p) for p in candidate_paths)
    )


@app.on_event("startup")
async def startup_event():
    try:
        model_path = _resolve_model_path()
        app.state.solver = CalculusSolverInference(
            model_path=model_path,
            vocab_path=str(ROOT / "tokenizer" / "vocab.json"),
            beam_size=5,
            max_len=256,
        )
        app.state.solver_error = None
    except Exception as exc:
        app.state.solver = None
        app.state.solver_error = str(exc)
        print(f"CalculusSolver API started without solver: {exc}", flush=True)


@app.on_event("shutdown")
async def shutdown_event():
    solver = getattr(app.state, "solver", None)
    if solver is not None:
        solver.close()


app.include_router(solve_router)
app.include_router(validate_router)
