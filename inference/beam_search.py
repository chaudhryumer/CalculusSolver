import json
import os
import subprocess
import threading
from typing import Any, Dict, List, Optional

import torch

from model.architecture import CalculusModel


class NodeValidityWorker:
    def __init__(self, script_path: str):
        self.process = subprocess.Popen(
            [
                "node",
                "--input-type=module",
                script_path,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("Failed to open Node validity worker streams.")
        self.lock = threading.Lock()

    def ask(self, request: Dict[str, Any]) -> Dict[str, Any]:
        payload = json.dumps(request)
        with self.lock:
            self.process.stdin.write(payload + "\n")
            self.process.stdin.flush()
            response_line = self.process.stdout.readline()
        if not response_line:
            stderr = self.process.stderr.read().strip()
            raise RuntimeError(
                f"Node validity worker exited unexpectedly. stderr={stderr}"
            )
        return json.loads(response_line)

    def close(self) -> None:
        try:
            if self.process.stdin:
                self.process.stdin.close()
            self.process.terminate()
        except Exception:
            pass


class NodeValidityPool:
    def __init__(self, script_path: str, num_workers: int = 4):
        self.workers = [NodeValidityWorker(script_path) for _ in range(num_workers)]
        self.next_index = 0

    def mask(self, tokens: List[str], candidate_tokens: List[str]) -> List[bool]:
        worker = self.workers[self.next_index % len(self.workers)]
        self.next_index += 1
        response = worker.ask(
            {
                "tokens": tokens,
                "candidate_tokens": candidate_tokens,
            }
        )
        return response.get("mask", [])

    def close(self) -> None:
        for worker in self.workers:
            worker.close()


def flatten_vocab(vocab: Dict[str, Any]) -> Dict[str, int]:
    token_to_id = {}
    for key, value in vocab.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            token_to_id.update(value)
    return token_to_id


def load_vocab(vocab_path: str) -> Dict[str, Any]:
    with open(vocab_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    flat = flatten_vocab(raw)
    id_to_token = {idx: token for token, idx in flat.items()}
    return {
        "token_to_id": flat,
        "id_to_token": id_to_token,
        "special": raw.get("special_tokens", {}),
    }


def beam_search(
    model: CalculusModel,
    src_tokens: torch.Tensor,
    src_positions: torch.Tensor,
    parent_child_pairs: torch.Tensor,
    vocab_map: Dict[str, Any],
    beam_size: int = 5,
    max_len: int = 128,
    node_pool: Optional[NodeValidityPool] = None,
) -> Dict[str, Any]:
    device = src_tokens.device
    vocab = vocab_map["token_to_id"]
    id_to_token = vocab_map["id_to_token"]
    bos_id = vocab["[BOS]"]
    eos_id = vocab["[EOS]"]

    if node_pool is None:
        script_path = os.path.join(os.path.dirname(__file__), "validity_worker.js")
        node_pool = NodeValidityPool(script_path, num_workers=max(2, beam_size))

    root_mask = torch.zeros(
        src_tokens.size(0), src_tokens.size(1), dtype=torch.bool, device=device
    )
    root_mask[:, 0] = True

    encoder_output = model.encoder(
        src_tokens,
        src_positions,
        parent_child_pairs,
        padding_mask=None,
    )
    rule_logits = model.rule_head(encoder_output, root_mask=root_mask)
    root_rule_ids = torch.argmax(rule_logits, dim=-1)
    root_rule_id = int(root_rule_ids[0].item())
    rule_embeddings = model.rule_head.embed_rules(root_rule_ids)

    all_candidate_tokens = [id_to_token[idx] for idx in range(len(id_to_token))]
    beams = [
        {
            "tokens": [bos_id],
            "score": 0.0,
            "finished": False,
        }
    ]
    completed = []

    for _ in range(max_len):
        candidates = []
        for beam in beams:
            if beam["finished"]:
                candidates.append(beam)
                continue

            current_tokens = beam["tokens"]
            token_strings = [id_to_token[token_id] for token_id in current_tokens]
            tgt = torch.tensor([current_tokens], device=device)
            decoder_logits, _ = model.decoder(
                tgt,
                encoder_output,
                rule_embeddings=rule_embeddings,
                validity_mask=None,
                tgt_padding_mask=None,
                memory_key_padding_mask=None,
            )
            next_logits = decoder_logits[0, -1, :]
            mask = node_pool.mask(token_strings, all_candidate_tokens)
            invalid_mask = torch.tensor([not valid for valid in mask], device=device)
            safe_logits = next_logits.masked_fill(invalid_mask, float("-inf"))

            if torch.isinf(safe_logits).all():
                continue

            log_probs = torch.log_softmax(safe_logits, dim=-1)
            topk = torch.topk(log_probs, min(beam_size, safe_logits.size(0)))
            for score, token_id in zip(topk.values.tolist(), topk.indices.tolist()):
                new_tokens = current_tokens + [int(token_id)]
                finished = token_id == eos_id
                candidates.append(
                    {
                        "tokens": new_tokens,
                        "score": beam["score"] + float(score),
                        "finished": finished,
                    }
                )

        if not candidates:
            break

        beams = sorted(candidates, key=lambda x: x["score"], reverse=True)[:beam_size]
        if all(beam["finished"] for beam in beams):
            completed.extend(beams)
            break

    best = None
    if completed:
        best = sorted(completed, key=lambda x: x["score"], reverse=True)[0]
    else:
        best = (
            beams[0] if beams else {"tokens": [bos_id], "score": 0.0, "finished": False}
        )

    status = "solved"
    root_rule_label = None
    rule_labels = getattr(model.rule_head, "labels", lambda: [])()
    if root_rule_id < len(rule_labels):
        root_rule_label = rule_labels[root_rule_id]
        if root_rule_label == "undefined":
            status = "unsolvable"

    if not best["finished"]:
        status = "partial"

    return {
        "tokens": best["tokens"],
        "score": best["score"],
        "status": status,
        "root_rule_id": root_rule_id,
        "root_rule_label": root_rule_label,
    }
