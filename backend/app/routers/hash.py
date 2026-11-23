import hashlib

from fastapi import APIRouter

from backend.app.schemas import HashRequest, HashResponse

router = APIRouter(prefix="/hash", tags=["hash"])


@router.post("/blake2b", response_model=HashResponse)
def hash_blake2b(request: HashRequest):
    digest = hashlib.blake2b(request.text.encode("utf-8"), digest_size=32).hexdigest()
    return HashResponse(
        algorithm="blake2b",
        digest=digest,
        input_length=len(request.text),
        note="Uso recomendado para integridad o fingerprints; no para contraseñas.",
    )
