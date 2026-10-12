import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.env_loader import load_app_env, cors_origins, cors_allow_all, cors_origin_regex

load_app_env()

from typing import List, Optional
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.mailer import send_email
import pandas as pd
from io import StringIO, BytesIO  # Correct imports for StringIO and BytesIO
from mangum import Mangum  # Add Mangum to handle the Lambda integration
from app.database import init_db, log_campaign, get_analytics_summary
from app.cloudinary_storage import upload_banner, upload_recipient_list
from app.email_filter import filter_emails

app = FastAPI()

# Initialize analytics database on startup
@app.on_event("startup")
def startup_event():
    missing = [
        name
        for name in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
        if not os.getenv(name)
    ]
    if missing:
        print(
            "WARNING: Cloudinary env vars not set: "
            + ", ".join(missing)
            + ". Add them to app/.env locally or to your host environment (production)."
        )
    try:
        init_db()
    except Exception as e:
        print(f"WARNING: Analytics DB init failed (emails may still send): {e}")
    print(
        f"CORS: allow_all={cors_allow_all()}, origins={len(_origins)}, "
        f"regex={_origin_regex!r}"
    )

# CORS (credentials must stay false if allow_origins is "*")
_origins = ["*"] if cors_allow_all() else cors_origins()
_origin_regex = None if cors_allow_all() else cors_origin_regex()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Email Automation API", "docs": "POST /send-emails, GET /api/analytics"}

def _banner_kind(filename: str) -> Optional[str]:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext == ".pdf":
        return "pdf"
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"):
        return "image"
    return None


@app.post("/send-emails")
async def send_emails(
    subject: str = Form(...),
    content: str = Form(...),
    banners: List[UploadFile] = File(...),
    csv_file: UploadFile = File(...),
    filter_similar: str = Form("true"),
):
    if not banners:
        return JSONResponse(
            status_code=400,
            content={"error": "Please upload at least one banner image or PDF."},
        )

    banner_items = []

    try:
        for uf in banners:
            raw = await uf.read()
            if not raw:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Empty file: {uf.filename or 'unknown'}"},
                )

            orig_name = uf.filename or "file"
            safe_base = os.path.basename(orig_name).replace("\\", "_").replace("/", "_")
            kind = _banner_kind(safe_base)

            if kind is None:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": f"Unsupported banner type: {safe_base}. Use images (JPG, PNG, GIF, WebP, SVG, BMP) or PDF."
                    },
                )

            banner_url = upload_banner(raw, safe_base, kind)
            item = {"url": banner_url, "kind": kind, "filename": safe_base}
            if kind == "pdf":
                item["data"] = raw
            banner_items.append(item)

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"Failed to upload banners to Cloudinary: {str(e)}"}
        )

    # Step 3: Read the CSV/Excel file
    contents = await csv_file.read()
    if not contents:
        return JSONResponse(status_code=400, content={"error": "Recipient file is empty."})

    recipient_cloudinary_id = upload_recipient_list(
        contents, csv_file.filename or "recipients.csv"
    )

    # Step 4: Use pandas to handle CSV/Excel dynamically (CSV or Excel)
    fname = (csv_file.filename or "").lower()
    try:
        if fname.endswith(".csv"):
            # For CSV files, try different encodings
            try:
                content_str = contents.decode("utf-8")
                data = pd.read_csv(StringIO(content_str))
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                content_str = contents.decode("latin-1")
                data = pd.read_csv(StringIO(content_str))
        elif fname.endswith((".xls", ".xlsx")):
            # For Excel files, use BytesIO instead of StringIO
            from io import BytesIO
            data = pd.read_excel(BytesIO(contents))
        else:
            raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Failed to read file: {str(e)}"})

    # Step 5: Find the email column dynamically (case-insensitive)
    email_column = None
    for col in data.columns:
        if col.strip().lower() in ["email", "email address"]:
            email_column = col
            break

    if not email_column:
        return JSONResponse(status_code=400, content={"error": "Email column not found in the file."})

    emails = data[email_column].dropna().astype(str).tolist()

    # Step 5b: Filter invalid, duplicate, and similar (prefix/suffix) emails
    do_filter = str(filter_similar).strip().lower() in ("1", "true", "yes", "on")
    filtered = filter_emails(emails, filter_similar=do_filter)
    emails = filtered.valid

    if not emails:
        return JSONResponse(
            status_code=400,
            content={
                "error": "No valid emails left after filtering.",
                "skipped_invalid": filtered.skipped_invalid[:50],
                "skipped_duplicate": filtered.skipped_duplicate[:50],
                "skipped_similar": filtered.skipped_similar[:50],
                "skipped_suspicious": filtered.skipped_suspicious[:50],
            },
        )

    # Step 6: Send emails
    successful_count = 0
    failed_count = 0

    for email in emails:
        try:
            send_email(email, subject, content, banner_items)
            successful_count += 1
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")
            failed_count += 1

    # Log to analytics database
    try:
        log_campaign(subject, len(emails), successful_count, failed_count)
    except Exception as e:
        print(f"Failed to log campaign analytics: {e}")

    out = {
        "message": (
            f"Emails sent! Successful: {successful_count}, Failed: {failed_count}"
            + (f", Filtered out: {filtered.skipped_count}" if filtered.skipped_count else "")
        ),
        "successful": successful_count,
        "failed": failed_count,
        "filtered_out": filtered.skipped_count,
        "skipped_invalid": filtered.skipped_invalid[:50],
        "skipped_duplicate": filtered.skipped_duplicate[:50],
        "skipped_similar": filtered.skipped_similar[:50],
        "skipped_suspicious": filtered.skipped_suspicious[:50],
    }
    if recipient_cloudinary_id:
        out["recipient_file_cloudinary_public_id"] = recipient_cloudinary_id
    return out

@app.get("/api/analytics")
async def get_analytics():
    try:
        summary = get_analytics_summary()
        return summary
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to fetch analytics: {str(e)}"})

# Lambda handler for AWS Lambda
handler = Mangum(app)