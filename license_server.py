from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import jwt
import uuid
import uvicorn

app = FastAPI()

licenses = {}


SECRET_KEY = "secret-key-here"
ALGORITHM = "HS256"


class License(BaseModel):
    id: str
    key: str
    product_id: str
    customer_id: str
    issued_at: datetime
    expires_at: datetime
    hardware_id: Optional[str]
    features: List[str]
    active: bool


class LicenseRequest(BaseModel):
    product_id: str
    customer_id: str
    hardware_id: Optional[str]
    features: List[str]
    duration_days: int


class ValidateRequest(BaseModel):
    license_key: str
    hardware_id: Optional[str]


def generate_license_key():
    return str(uuid.uuid4()).replace("-", "")[:24]


@app.post("/api/licenses")
async def create_license(request: LicenseRequest):
    license_id = str(uuid.uuid4())
    license = License(
        id=license_id,
        key=generate_license_key(),
        product_id=request.product_id,
        customer_id=request.customer_id,
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=request.duration_days),
        hardware_id=request.hardware_id,
        features=request.features,
        active=True,
    )
    licenses[license_id] = license
    return license


@app.post("/api/validate")
async def validate_license(request: ValidateRequest):
    license = next(
        (lic for lic in licenses.values() if lic.key == request.license_key), None
    )

    if not license:
        raise HTTPException(status_code=401, detail="Invalid license key")

    if not license.active:
        raise HTTPException(status_code=401, detail="License is inactive")

    if license.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="License has expired")

    if license.hardware_id and request.hardware_id:
        if license.hardware_id != request.hardware_id:
            raise HTTPException(status_code=401, detail="Invalid hardware ID")

    token_data = {
        "license_id": license.id,
        "exp": datetime.now() + timedelta(hours=24),
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    return {"valid": True, "token": token, "features": license.features}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
