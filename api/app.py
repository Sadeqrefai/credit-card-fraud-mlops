# ============================================
#  PHASE 7
# ============================================

from fastapi import FastAPI, Request
from pydantic import BaseModel
import joblib
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --------------------------------------------
# 1. Load model
# --------------------------------------------
model_path = os.getenv("MODEL_PATH")
model = joblib.load(model_path)

# --------------------------------------------
# 2. Define input schema
# --------------------------------------------
class Transaction(BaseModel):
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    scaled_amount: float
    scaled_time: float

# --------------------------------------------
# 3. Create FastAPI app
# --------------------------------------------
app = FastAPI(title="Credit Card Fraud Detection API")

# --------------------------------------------
# 3.1 Prometheus Instrumentation (MUST be here)
# --------------------------------------------
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)

# --------------------------------------------
# 3.2 Database initialization
# --------------------------------------------
from api.database import init_db

@app.on_event("startup")
def startup_event():
    init_db()

# --------------------------------------------
# Logging Middleware
# --------------------------------------------
import json
from datetime import datetime
from starlette.responses import Response

LOG_FILE = "logs/predictions.jsonl"

@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.url.path == "/predict":
        try:
            body_bytes = await request.body()
            payload = json.loads(body_bytes.decode()) if body_bytes else {}
        except:
            payload = {}

        response = await call_next(request)

        try:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            result = json.loads(response_body.decode())
        except:
            result = {}

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request": payload,
            "response": result
        }

        os.makedirs("logs", exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        return Response(
            content=response_body,
            status_code=response.status_code,
            media_type=response.media_type
        )

    return await call_next(request)

# --------------------------------------------
# 3.3 Health endpoint
# --------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# --------------------------------------------
# 4. Prediction endpoint
# --------------------------------------------
from api.database import SessionLocal, FraudLog

@app.post("/predict")
def predict(transaction: Transaction):
    data = np.array([[
        transaction.V1, transaction.V2, transaction.V3, transaction.V4,
        transaction.V5, transaction.V6, transaction.V7, transaction.V8,
        transaction.V9, transaction.V10, transaction.V11, transaction.V12,
        transaction.V13, transaction.V14, transaction.V15, transaction.V16,
        transaction.V17, transaction.V18, transaction.V19, transaction.V20,
        transaction.V21, transaction.V22, transaction.V23, transaction.V24,
        transaction.V25, transaction.V26, transaction.V27, transaction.V28,
        transaction.scaled_amount, transaction.scaled_time
    ]])

    prediction = model.predict(data)[0]
    probability = model.predict_proba(data)[0][1]

    db = SessionLocal()
    log_entry = FraudLog(
        request_data=transaction.dict(),
        prediction=int(prediction),
        probability=float(probability)
    )
    db.add(log_entry)
    db.commit()
    db.close()

    return {
        "fraud_prediction": int(prediction),
        "fraud_probability": float(probability)
    }

# --------------------------------------------
# 5. Retrieve logs from PostgreSQL
# --------------------------------------------
@app.get("/logs")
def get_logs():
    db = SessionLocal()
    logs = db.query(FraudLog).all()
    db.close()
    return logs