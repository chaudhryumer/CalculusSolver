# Hosting Decision — Neural Model vs Vercel Serverless

## Constraint
Vercel Python serverless functions cap deployment size at 250MB unzipped.
torch + numpy + model.pkl exceed this by 2-3x. Confirmed not feasible to
run the neural path (`inference/solve.py`) inside a Vercel function.

## Decision
- Production (Vercel): FallbackSolver only, optionally Groq if
  GROQ_API_KEY is set. No torch/numpy in requirements.txt.
- Neural mode (`model/`, `train.py`, checkpoints) is local-dev /
  research only, gated behind `requirements-neural.txt`.
- Revisit self-hosting the neural model as a separate service only if
  product requirements demand it.

## Why this doesn't limit functionality today
`FallbackSolver` already covers diff, partial, integrate, gradient,
tangent_line for polynomial expressions — the full scope described in
README.md's "Key Features". Neural mode is an accuracy upgrade for
non-polynomial rules (trig, exp, log), not a hard requirement for launch.
