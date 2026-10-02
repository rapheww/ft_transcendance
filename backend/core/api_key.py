import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

load_dotenv()

PUBLIC_API_KEY = os.getenv("PUBLIC_API_KEY")
if PUBLIC_API_KEY is None or not PUBLIC_API_KEY.strip():
    raise RuntimeError("PUBLIC_API_KEY must be set and non-blank")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Depends(api_key_header)) -> None:
    if api_key is None or api_key != PUBLIC_API_KEY:
        raise HTTPException(status_code=401,
                            detail="Invalid or missing API key")
