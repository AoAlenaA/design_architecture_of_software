from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from uuid import uuid4, UUID
from datetime import date, datetime

app = FastAPI(title="Analytics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====== Models ======
class TraineeCreate(BaseModel):
    fullName: str = Field(min_length=1, max_length=200)
    email: EmailStr
    department: Optional[str] = Field(default=None, max_length=200)
    hireDate: date


class Trainee(TraineeCreate):
    id: UUID
    status: str = "ACTIVE"
    createdAt: datetime
    updatedAt: datetime


class AssessmentCreate(BaseModel):
    traineeId: UUID
    type: str = Field(pattern="^(TEST|DIALOGUE|FINAL)$")
    moduleId: str = Field(min_length=1, max_length=200)
    score: int = Field(ge=0)
    maxScore: int = Field(gt=0)
    completedAt: datetime
    errors: Optional[List[Dict[str, int]]] = None


class Assessment(AssessmentCreate):
    id: UUID
    passed: bool


# ====== In-memory storage (для лабы) ======
trainees: Dict[UUID, Trainee] = {}
assessments: Dict[UUID, Assessment] = {}


# ====== Utility ======
@app.get("/health")
def health():
    return {"status": "ok"}


# ====== Trainees ======

@app.post("/api/v1/trainees", status_code=201, response_model=Trainee)
def create_trainee(body: TraineeCreate):
    now = datetime.utcnow()
    new_id = uuid4()
    trainee = Trainee(
        id=new_id,
        fullName=body.fullName,
        email=body.email,
        department=body.department,
        hireDate=body.hireDate,
        status="ACTIVE",
        createdAt=now,
        updatedAt=now,
    )
    trainees[new_id] = trainee
    return trainee


@app.get("/api/v1/trainees", response_model=List[Trainee])
def list_trainees(
    department: Optional[str] = None,
    status: Optional[str] = Query(default=None, pattern="^(ACTIVE|INACTIVE)$"),
):
    items = list(trainees.values())
    if department:
        items = [t for t in items if (t.department or "") == department]
    if status:
        items = [t for t in items if t.status == status]
    return items


@app.get("/api/v1/trainees/{trainee_id}", response_model=Trainee)
def get_trainee(trainee_id: UUID):
    trainee = trainees.get(trainee_id)
    if not trainee:
        raise HTTPException(status_code=404, detail="Trainee not found")
    return trainee


@app.put("/api/v1/trainees/{trainee_id}", response_model=Trainee)
def update_trainee(trainee_id: UUID, body: TraineeCreate):
    trainee = trainees.get(trainee_id)
    if not trainee:
        raise HTTPException(status_code=404, detail="Trainee not found")

    now = datetime.utcnow()
    updated = Trainee(
        id=trainee.id,
        fullName=body.fullName,
        email=body.email,
        department=body.department,
        hireDate=body.hireDate,
        status=trainee.status,
        createdAt=trainee.createdAt,
        updatedAt=now,
    )
    trainees[trainee_id] = updated
    return updated


@app.delete("/api/v1/trainees/{trainee_id}", status_code=204)
def delete_trainee(trainee_id: UUID):
    if trainee_id not in trainees:
        raise HTTPException(status_code=404, detail="Trainee not found")
    del trainees[trainee_id]
    return None


# ====== Assessments ======

@app.post("/api/v1/assessments", status_code=201, response_model=Assessment)
def create_assessment(body: AssessmentCreate):
    if body.score > body.maxScore:
        raise HTTPException(status_code=400, detail="score cannot be greater than maxScore")
    if body.traineeId not in trainees:
        raise HTTPException(status_code=404, detail="Trainee not found")

    new_id = uuid4()
    passed = body.score >= int(0.6 * body.maxScore)
    assessment = Assessment(
        id=new_id,
        traineeId=body.traineeId,
        type=body.type,
        moduleId=body.moduleId,
        score=body.score,
        maxScore=body.maxScore,
        completedAt=body.completedAt,
        errors=body.errors,
        passed=passed,
    )
    assessments[new_id] = assessment
    return assessment


@app.get("/api/v1/assessments", response_model=List[Assessment])
def list_assessments(
    traineeId: Optional[UUID] = None,
    type: Optional[str] = Query(default=None, pattern="^(TEST|DIALOGUE|FINAL)$"),
):
    items = list(assessments.values())
    if traineeId:
        items = [a for a in items if a.traineeId == traineeId]
    if type:
        items = [a for a in items if a.type == type]
    return items


@app.get("/api/v1/metrics/trainees/{trainee_id}")
def metrics(trainee_id: UUID):
    if trainee_id not in trainees:
        raise HTTPException(status_code=404, detail="Trainee not found")

    items = [a for a in assessments.values() if a.traineeId == trainee_id]
    if not items:
        return {"traineeId": str(trainee_id), "avgScore": None, "count": 0, "passRate": None}

    avg = sum(a.score / a.maxScore for a in items) / len(items)
    pass_rate = sum(1 for a in items if a.passed) / len(items)

    return {
        "traineeId": str(trainee_id),
        "avgScore": round(avg * 100, 2),
        "count": len(items),
        "passRate": round(pass_rate, 2),
    }