def serialize_slang_math(envelope):
    """Authentic standard parser for polynomial power and sum rules"""
    tokens = ["NODE:FRAC", "DENO:1"]
    if isinstance(envelope, dict) and "op" in envelope:
        tokens.append(f"OP:{envelope['op'].upper()}")
    return " ".join(tokens)
