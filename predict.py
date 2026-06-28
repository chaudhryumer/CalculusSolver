import sys
import json
import torch
from solver_model import CalculusSolverModel
from tokenizer.slang_serializer import serialize_slang_math

with open("config.json", "r") as cfg_file:
    config = json.load(cfg_file)

with open("vocab.json", "r", encoding="utf-8") as f:
    vocab_mapping = json.load(f)
REAL_VOCAB_SIZE = len(vocab_mapping)

def evaluate_cli_input():
    if len(sys.argv) < 2:
        print("💡 Usage: python predict.py '{\"op\": \"diff\", \"var\": \"x\", \"expr\": {\"type\": \"pow\", \"base\": \"x\", \"exp\": 3}}'")
        return
        
    try:
        # Expect input as a valid JSON envelope string from CLI
        user_envelope = json.loads(sys.argv[1])
    except Exception:
        print("❌ Error: Input must be a valid JSON envelope dictionary string.")
        return
        
    print(f"📥 Envelope Received: {user_envelope}")
    
    token_strings = serialize_slang_math(user_envelope)
    if isinstance(token_strings, str):
        token_list = token_strings.split()
    else:
        token_list = token_strings
        
    encoded_src = [vocab_mapping.get(t, vocab_mapping.get("<unk>", 3)) for t in token_list]

    if len(encoded_src) < 20:
        encoded_src += [0] * (20 - len(encoded_src))
    src_tensor = torch.tensor([encoded_src[:20]], dtype=torch.long)
    dummy_tgt = torch.zeros((1, 20), dtype=torch.long)
    
    rules_inverse = {0: "power rule", 1: "trig derivative", 2: "exponential rule", 3: "logarithmic rule"}
    model = CalculusSolverModel(vocab_size=REAL_VOCAB_SIZE, hidden_dim=config["hidden_dim"])
    
    try:
        model.load_state_dict(torch.load("checkpoints/checkpoint_epoch_1.pt"))
    except Exception:
        pass
        
    model.eval()
    with torch.no_grad():
        _, rule_logits, verifier_logits = model(src_tensor, dummy_tgt)
        pred_rule = torch.argmax(rule_logits, dim=-1).item()
        confidence = torch.sigmoid(verifier_logits).item()
        
    print("\n🎯 --- Prediction Results Summary ---")
    print(f"🧩 Identified Rule Head: {rules_inverse.get(pred_rule, 'power rule')}")
    print(f"🛡️ Verifier Assessment : {'VERIFIED' if confidence >= 0.5 else 'CORRUPTED'} (Confidence: {confidence*100:.2f}%)")

if __name__ == "__main__":
    evaluate_cli_input()