import json
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Extra

router = APIRouter()


class ValidateRequest(BaseModel):
    expression: Any = None

    class Config:
        extra = Extra.allow


@router.post("/validate")
def validate_expression(body: ValidateRequest) -> Dict[str, Any]:
    import subprocess
    from pathlib import Path

    script_path = Path(__file__).resolve().parents[1] / "validate_slang.js"
    payload = body.dict()
    expression = payload.get("expression", payload)
    proc = subprocess.run(
        ["node", "--input-type=module", str(script_path)],
        input=json.dumps({"expression": expression}),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 and not proc.stdout:
        raise HTTPException(
            status_code=500, detail=proc.stderr.strip() or "Validation failed"
        )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500, detail=f"Validator response parse error: {exc}"
        )

    return payload
