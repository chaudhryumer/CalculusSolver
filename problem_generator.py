import json
import random
from pathlib import Path

def generate_slang_dataset():
    print("⏳ [Dataset Engine] Programmatically synthesizing 100k-row canonical SLaNg dataset...")
    splits_dir = Path("data/splits")
    splits_dir.mkdir(parents=True, exist_ok=True)
    
    dataset = []
    
    def make_frac(terms):
        return {
            "numi": {"terms": terms},
            "deno": 1
        }
        
    for i in range(100000):
        rule = random.randint(0, 4)
        var_name = "x"
        
        if rule == 0: # Power Rule
            coeff = random.randint(1, 20)
            power = random.randint(2, 8)
            src_expr = make_frac([{"coeff": coeff, "var": {var_name: power}}])
            ans_expr = make_frac([{"coeff": coeff * power, "var": {var_name: power - 1}}])
            rule_id = 0
            
        elif rule == 1: # Trig Derivatives
            src_expr = make_frac([{"coeff": 1, "var": {"sin_x": 1}}])
            ans_expr = make_frac([{"coeff": 1, "var": {"cos_x": 1}}])
            rule_id = 1
            
        elif rule == 2: # Exponential Rule
            coeff = random.randint(1, 5)
            src_expr = make_frac([{"coeff": coeff, "var": {"e_x": 1}}])
            ans_expr = make_frac([{"coeff": coeff, "var": {"e_x": 1}}])
            rule_id = 2
            
        elif rule == 3: # Logarithmic Rule
            src_expr = make_frac([{"coeff": 1, "var": {"ln_x": 1}}])
            ans_expr = make_frac([{"coeff": 1, "var": {"x": -1}}])
            rule_id = 3
            
        else: # Sum/Difference
            c1, c2 = random.randint(1, 15), random.randint(1, 15)
            p1, p2 = random.randint(2, 5), random.randint(2, 5)
            src_expr = make_frac([
                {"coeff": c1, "var": {var_name: p1}},
                {"coeff": -c2, "var": {var_name: p2}}
            ])
            ans_expr = make_frac([
                {"coeff": c1 * p1, "var": {var_name: p1 - 1}},
                {"coeff": -c2 * p2, "var": {var_name: p2 - 1}}
            ])
            rule_id = 4

        src_op_node = {
            "op": "diff",
            "var": var_name,
            "expr": src_expr
        }
        
        dataset.append({
            "src_tokens": src_op_node,
            "tgt_input_tokens": ans_expr,
            "tgt_output_tokens": ans_expr,
            "rule_ids": rule_id,
            "verification_state": 1
        })

    random.shuffle(dataset)
    
    with open("data/slang_dataset.jsonl", "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item) + "\n")
            
    for name, split_data in [("train", dataset[:90000]), ("val", dataset[90000:95000]), ("test", dataset[95000:])]:
        with open(splits_dir / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for item in split_data:
                f.write(json.dumps(item) + "\n")
                
    print(f"✅ [Dataset Engine] 100,000 structural canonical rows generated successfully.")

if __name__ == "__main__":
    generate_slang_dataset()