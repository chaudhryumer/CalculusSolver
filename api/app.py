from fastapi import FastAPI

from api.routes.solve import router as solve_router
from api.routes.validate import router as validate_router
from inference.solve import CalculusSolverInference

app = FastAPI(title="CalculusSolver API")


@app.on_event("startup")
async def startup_event():
    app.state.solver = CalculusSolverInference(
        model_path="checkpoints/final/best.pt",
        vocab_path="tokenizer/vocab.json",
        beam_size=5,
        max_len=256,
    )


@app.on_event("shutdown")
async def shutdown_event():
    solver = getattr(app.state, "solver", None)
    if solver is not None:
        solver.close()


app.include_router(solve_router)
app.include_router(validate_router)
