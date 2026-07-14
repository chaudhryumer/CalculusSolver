# Known Issues and Tracked Gaps

This file records bugs and discrepancies that were discovered, their root cause,
and their resolution. Each entry includes the fix reference so the full history
is preserved even after the issue is closed.

---

## [RESOLVED] STRUCT:OPEN missing from tokenizer/vocab.json

**Discovered:** During unit test implementation (Task 1, PR adding test suite)  
**Fixed:** Fix 3 (vocab.json v1.1)  
**Severity:** High — silent data corruption in neural training and inference  
**Affected path:** Neural solver only (FallbackSolver and GroqSolver unaffected)

### What was wrong

`tokenizer/slang_serializer.py` emits `"STRUCT:OPEN"` as the opening bracket
token for every fraction node and op-node it serializes. This token is defined
as a module-level constant:

```python
OPEN = "STRUCT:OPEN"