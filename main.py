"""
main.py — AI Job Assistant API
"""

import io
import logging
from typing import Annotated

import PyPDF2
from bson import ObjectId
from fastapi import FastAPI, File, HTTPException, UploadFile, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from auth import router as auth_router, get_current_user, require_admin
from cover_letter import generate_cover_letter
from db import jobs_collection, users_collection
from email_service import send_status_email
from matcher import match_score
from resume_parser import extract_skills

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Job Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class MatchRequest(BaseModel):
    resume: str
    job: str

class CoverLetterRequest(BaseModel):
    name: str
    role: str
    skills: list[str]

class JobRequest(BaseModel):
    company: str
    role: str
    status: str
    notes: str = ""          # ✅ optional notes field

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"applied", "interview", "offer", "rejected"}
        if v.lower() not in allowed:
            raise ValueError(f"status must be one of: {', '.join(allowed)}")
        return v.lower()

class UpdateJobRequest(BaseModel):
    status: str
    notes: str | None = None  # ✅ optional — only update if provided

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        allowed = {"applied", "interview", "offer", "rejected"}
        if v.lower() not in allowed:
            raise ValueError(f"status must be one of: {', '.join(allowed)}")
        return v.lower()

class MessageResponse(BaseModel):
    msg: str

CurrentUser = Annotated[str, Depends(get_current_user)]
AdminUser   = Annotated[dict, Depends(require_admin)]

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "AI Job Assistant API is running 🚀"}

# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

@app.post("/upload-resume", tags=["Resume"])
async def upload_resume(current_user: CurrentUser, file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    if not filename.endswith((".pdf", ".txt")):
        raise HTTPException(status_code=400, detail="Only PDF or TXT files are supported")

    content = await file.read()
    text = ""
    try:
        if filename.endswith(".pdf"):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted
        else:
            text = content.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=422, detail="Could not parse the uploaded file")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No readable text found in the uploaded file")

    skills = extract_skills(text)
    return {"message": "Resume processed successfully", "skills": skills,
            "preview": text[:300], "full_text": text}

# ---------------------------------------------------------------------------
# Match
# ---------------------------------------------------------------------------

@app.post("/match", tags=["Matching"])
def match(data: MatchRequest, current_user: CurrentUser):
    try:
        score = match_score(data.resume, data.job)
        return {"match_percentage": score}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

# ---------------------------------------------------------------------------
# Cover Letter
# ---------------------------------------------------------------------------

@app.post("/cover-letter", tags=["Cover Letter"])
def cover(data: CoverLetterRequest, current_user: CurrentUser):
    try:
        letter = generate_cover_letter(data.name, data.role, data.skills)
        return {"cover_letter": letter}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

# ---------------------------------------------------------------------------
# Job Tracker — USER routes
# ---------------------------------------------------------------------------

@app.post("/jobs", response_model=MessageResponse, status_code=201, tags=["Jobs"])
async def add_job(data: JobRequest, current_user: CurrentUser):
    jobs_collection.insert_one({
        **data.model_dump(),
        "user_email": current_user,
    })
    # Send email notification
    await send_status_email(current_user, data.company, data.role, data.status)
    return MessageResponse(msg="Job added successfully")


@app.get("/jobs", tags=["Jobs"])
def get_jobs(current_user: CurrentUser):
    jobs = []
    for job in jobs_collection.find({"user_email": current_user}):
        job["_id"] = str(job["_id"])
        jobs.append(job)
    return jobs


@app.put("/jobs/{job_id}", response_model=MessageResponse, tags=["Jobs"])
async def update_job(job_id: str, data: UpdateJobRequest, current_user: CurrentUser):
    # Build update fields
    update_fields: dict = {"status": data.status}
    if data.notes is not None:
        update_fields["notes"] = data.notes

    try:
        job = jobs_collection.find_one(
            {"_id": ObjectId(job_id), "user_email": current_user}
        )
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_fields},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID")

    # Send email notification for status change
    await send_status_email(current_user, job["company"], job["role"], data.status)
    return MessageResponse(msg="Job updated successfully")


@app.delete("/jobs/{job_id}", response_model=MessageResponse, tags=["Jobs"])
def delete_job(job_id: str, current_user: CurrentUser):
    try:
        result = jobs_collection.delete_one(
            {"_id": ObjectId(job_id), "user_email": current_user}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return MessageResponse(msg="Job deleted successfully")

# ---------------------------------------------------------------------------
# ADMIN routes
# ---------------------------------------------------------------------------

@app.get("/admin/users", tags=["Admin"])
def admin_get_all_users(admin: AdminUser):
    users = []
    for user in users_collection.find():
        users.append({
            "_id": str(user["_id"]),
            "email": user["email"],
            "role": user.get("role", "user"),
            "created_at": str(user.get("created_at", "")),
        })
    return users


@app.delete("/admin/users/{email}", response_model=MessageResponse, tags=["Admin"])
def admin_delete_user(email: str, admin: AdminUser):
    result = users_collection.delete_one({"email": email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    jobs_collection.delete_many({"user_email": email})
    return MessageResponse(msg=f"User {email} and all their jobs deleted")


@app.get("/admin/jobs", tags=["Admin"])
def admin_get_all_jobs(admin: AdminUser):
    jobs = []
    for job in jobs_collection.find():
        job["_id"] = str(job["_id"])
        jobs.append(job)
    return jobs


@app.put("/admin/jobs/{job_id}", response_model=MessageResponse, tags=["Admin"])
async def admin_update_job(job_id: str, data: UpdateJobRequest, admin: AdminUser):
    try:
        job = jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        update_fields: dict = {"status": data.status}
        if data.notes is not None:
            update_fields["notes"] = data.notes

        jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": update_fields},
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID")

    # Notify the user whose job was updated
    await send_status_email(job["user_email"], job["company"], job["role"], data.status)
    return MessageResponse(msg="Job updated successfully")


@app.delete("/admin/jobs/{job_id}", response_model=MessageResponse, tags=["Admin"])
def admin_delete_job(job_id: str, admin: AdminUser):
    try:
        result = jobs_collection.delete_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return MessageResponse(msg="Job deleted successfully")


@app.patch("/admin/users/{email}/role", response_model=MessageResponse, tags=["Admin"])
def admin_update_role(email: str, role: str, admin: AdminUser):
    if role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
    result = users_collection.update_one({"email": email}, {"$set": {"role": role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return MessageResponse(msg=f"{email} is now a {role}")
