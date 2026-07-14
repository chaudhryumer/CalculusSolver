import json
import random
from pathlib import Path

# ── Vocab-safe ranges ────────────────────────────────────────────────────────
SAFE_COEFFS = list(range(-10, 11)) + [12]
SAFE_POS_COEFFS = [c for c in SAFE_COEFFS if c > 0]
SAFE_NONZERO_COEFFS = [c for c in SAFE_COEFFS if c != 0]
SAFE_EXPONENTS = list(range(-3, 6))
SAFE_POS_EXPONENTS = [e for e in SAFE_EXPONENTS if e >= 1]
VARIABLES = ["x", "y", "z"]


def _output_in_vocab(coeff, power):
    """Check that the derivative output (coeff*power, power-1) stays in vocab range."""
    out_coeff = coeff * power
    out_exp = power - 1
    return out_coeff in SAFE_COEFFS and out_exp in SAFE_EXPONENTS


def generate_single_term_diff(var="x"):
    """Generate a single-term power-rule differentiation problem."""
    for _ in range(100):
        coeff = random.choice(SAFE_NONZERO_COEFFS)
        power = random.choice(SAFE_POS_EXPONENTS)
        if _output_in_vocab(coeff, power):
            src = {"numi": {"terms": [{"coeff": coeff, "var": {var: power}}]}, "deno": 1}
            ans = {"numi": {"terms": [{"coeff": coeff * power, "var": {var: power - 1}}]}, "deno": 1}
            if ans["numi"]["terms"][0]["var"][var] == 0:
                ans = {"coeff": coeff * power}
            return src, ans, 0  # power_rule
    return {"numi": {"terms": [{"coeff": 2, "var": {var: 2}}]}, "deno": 1}, {"numi": {"terms": [{"coeff": 4, "var": {var: 1}}]}, "deno": 1}, 0


def generate_constant_term(var="x"):
    """Generate a constant differentiation problem (derivative = 0)."""
    coeff = random.choice(SAFE_NONZERO_COEFFS)
    src = {"numi": {"terms": [{"coeff": coeff}]}, "deno": 1}
    ans = {"numi": {"terms": [{"coeff": 0}]}, "deno": 1}
    return src, ans, 5  # constant_rule


def generate_multi_term_diff(var="x", num_terms=None):
    """Generate a multi-term polynomial differentiation problem (sum rule)."""
    if num_terms is None:
        num_terms = random.randint(2, 3)

    src_terms = []
    ans_terms = []

    for i in range(num_terms):
        if i == num_terms - 1 and random.random() < 0.3:
            c_src, c_ans, _ = generate_constant_term(var)
            src_terms.append(c_src)
        else:
            t_src, t_ans, _ = generate_single_term_diff(var)
            src_exps = {list(t["numi"]["terms"][0].get("var", {}).values())[0] for t in src_terms if t["numi"]["terms"][0].get("var")}
            t_exp = list(t_src["numi"]["terms"][0].get("var", {}).values())[0] if t_src["numi"]["terms"][0].get("var") else None
            if t_exp in src_exps:
                t_src, t_ans, _ = generate_single_term_diff(var)
            src_terms.append(t_src)
            ans_terms.append(t_ans)

    if not ans_terms:
        ans_terms = [{"numi": {"terms": [{"coeff": 0}]}, "deno": 1}]

    return src_terms, ans_terms, 4  # sum_rule


def generate_negative_exp_diff(var="x"):
    """Generate a differentiation problem with negative exponents."""
    neg_exps = [e for e in SAFE_EXPONENTS if e < 0]
    for _ in range(100):
        coeff = random.choice(SAFE_NONZERO_COEFFS)
        power = random.choice(neg_exps)
        if _output_in_vocab(coeff, power):
            src = {"numi": {"terms": [{"coeff": coeff, "var": {var: power}}]}, "deno": 1}
            new_exp = power - 1
            ans = {"numi": {"terms": [{"coeff": coeff * power, "var": {var: new_exp}}]}, "deno": 1}
            return src, ans, 0
    return {"numi": {"terms": [{"coeff": 1, "var": {var: -1}}]}, "deno": 1}, {"numi": {"terms": [{"coeff": -1, "var": {var: -2}}]}, "deno": 1}, 0


def generate_multivar_diff():
    """Generate a multi-variable partial differentiation problem."""
    var = random.choice(VARIABLES)
    other_vars = [v for v in VARIABLES if v != var]

    src_terms = []
    ans_terms = []

    t_src, t_ans, _ = generate_single_term_diff(var)
    src_terms.append(t_src)
    ans_terms.append(t_ans)

    if other_vars:
        ov = random.choice(other_vars)
        c = random.choice(SAFE_NONZERO_COEFFS)
        p = random.choice(SAFE_POS_EXPONENTS)
        src_terms.append({"numi": {"terms": [{"coeff": c, "var": {ov: p}}]}, "deno": 1})

    if not ans_terms:
        ans_terms = [{"numi": {"terms": [{"coeff": 0}]}, "deno": 1}]

    return src_terms, ans_terms, var, 7


# ── Phase 2: Trig, Exp, and Log with multipliers and full coverage ──────────

def generate_sin_diff(var="x"):
    """d/dvar [sin(a*var)] = a * cos(a*var)"""
    a = random.choice([c for c in SAFE_NONZERO_COEFFS if c != 0])
    inner = {"numi": {"terms": [{"coeff": a, "var": {var: 1}}]}, "deno": 1}
    src = {"op": "sin", "expr": inner}
    ans = {
        "numi": {
            "terms": [{
                "coeff": a,
                "var": {}
            }]
        },
        "deno": 1,
        "op_term": {"op": "cos", "expr": inner}
    }
    return src, ans, 1


def generate_cos_diff(var="x"):
    """d/dvar [cos(a*var)] = -a * sin(a*var)"""
    a = random.choice([c for c in SAFE_NONZERO_COEFFS if c != 0])
    out_coeff = -a
    if out_coeff not in SAFE_COEFFS:
        out_coeff = -1 if a > 0 else 1
        a = -out_coeff

    inner = {"numi": {"terms": [{"coeff": a, "var": {var: 1}}]}, "deno": 1}
    src = {"op": "cos", "expr": inner}
    ans = {
        "numi": {
            "terms": [{
                "coeff": out_coeff,
                "var": {}
            }]
        },
        "deno": 1,
        "op_term": {"op": "sin", "expr": inner}
    }
    return src, ans, 1


def generate_tan_diff(var="x"):
    """d/dvar [tan(a*var)] = a * sec^2(a*var) -> represented as fraction: a / cos^2(a*var)"""
    a = random.choice([c for c in SAFE_NONZERO_COEFFS if c != 0])
    inner = {"numi": {"terms": [{"coeff": a, "var": {var: 1}}]}, "deno": 1}
    src = {"op": "tan", "expr": inner}
    ans = {
        "numi": {"terms": [{"coeff": a}]},
        "deno": {
            "terms": [{
                "coeff": 1,
                "var": {}
            }],
            "op_term": {"op": "cos", "expr": {"numi": {"terms": [{"coeff": a, "var": {var: 2}}]}, "deno": 1}}
        }
    }
    return src, ans, 1


def generate_exp_diff(var="x"):
    """d/dvar [exp(a*var)] = a * exp(a*var)"""
    a = random.choice([c for c in SAFE_NONZERO_COEFFS if c != 0])
    inner = {"numi": {"terms": [{"coeff": a, "var": {var: 1}}]}, "deno": 1}
    src = {"op": "exp", "expr": inner}
    ans = {
        "numi": {
            "terms": [{
                "coeff": a,
                "var": {}
            }]
        },
        "deno": 1,
        "op_term": {"op": "exp", "expr": inner}
    }
    return src, ans, 1


def generate_ln_diff(var="x"):
    """d/dvar [ln(a*var)] = 1/var."""
    a = random.choice(SAFE_POS_COEFFS)
    inner = {"numi": {"terms": [{"coeff": a, "var": {var: 1}}]}, "deno": 1}
    src = {"op": "ln", "expr": inner}
    ans = {"numi": {"terms": [{"coeff": 1}]}, "deno": {"terms": [{"coeff": 1, "var": {var: 1}}]}}
    return src, ans, 1


def generate_slang_dataset():
    print("[Dataset Engine] Programmatically synthesizing expanded SLaNg dataset...")
    splits_dir = Path("data/splits")
    splits_dir.mkdir(parents=True, exist_ok=True)

    dataset = []
    random.seed(42)

    # Total: 125,000 distributed records
    generators = [
        (generate_single_term_diff, 35000),
        (generate_multi_term_diff, 25000),
        (generate_constant_term, 10000),
        (generate_negative_exp_diff, 10000),
        (generate_multivar_diff, 20000),
        (generate_sin_diff, 5000),
        (generate_cos_diff, 5000),
        (generate_tan_diff, 5000),
        (generate_exp_diff, 5000),
        (generate_ln_diff, 5000)
    ]

    for gen_func, count in generators:
        for _ in range(count):
            var = random.choice(VARIABLES[:1])
            if gen_func == generate_multivar_diff:
                src_terms, ans_terms, active_var, rule_id = gen_func()
                src_op = {"op": "diff", "var": active_var, "expr": src_terms[0]}
                ans = ans_terms[0] if ans_terms else {"numi": {"terms": [{"coeff": 0}]}, "deno": 1}
            elif gen_func == generate_multi_term_diff:
                src_terms, ans_terms, rule_id = gen_func(var)
                src_op = {"op": "diff", "var": var, "expr": src_terms[0]}
                ans = ans_terms[0] if ans_terms else {"numi": {"terms": [{"coeff": 0}]}, "deno": 1}
            else:
                src, ans, rule_id = gen_func(var)
                src_op = {"op": "diff", "var": var, "expr": src}

            dataset.append({
                "src_tokens": src_op,
                "tgt_input_tokens": ans,
                "tgt_output_tokens": ans,
                "rule_ids": rule_id,
                "verification_state": 1,
            })

    random.shuffle(dataset)

    with open("data/slang_dataset.jsonl", "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")

    total = len(dataset)
    train_end = int(total * 0.90)
    val_end = int(total * 0.95)
    for name, split_data in [("train", dataset[:train_end]), ("val", dataset[train_end:val_end]), ("test", dataset[val_end:])]:
        with open(splits_dir / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for item in split_data:
                f.write(json.dumps(item) + "\n")

    print(f"[Dataset Engine] {total} expanded lines generated successfully.")


if __name__ == "__main__":
    generate_slang_dataset()