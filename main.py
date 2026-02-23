"""
Hiring System Dashboard - Flask Application
Connects to Airtable and displays hiring metrics
Includes AI Video Evaluation features
"""

import os
import requests
from flask import Flask, render_template, jsonify, request
from collections import Counter
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Airtable Configuration
AIRTABLE_PAT = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_ID = os.getenv("AIRTABLE_TABLE_ID")

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_PAT}",
    "Content-Type": "application/json"
}

# Hiring API URL for evaluation
HIRING_API_URL = os.getenv("HIRING_API_URL", "https://srv1079050.hstgr.cloud/hiring-api-la")


# ──────────────────────────────────────────────────
# In-memory cache for Airtable records (15-min TTL)
# ──────────────────────────────────────────────────
_cache = {
    "filtered_records": None,
    "timestamp": 0
}
CACHE_TTL = 15 * 60  # 15 minutes


def get_cached_data(force_refresh=False):
    """Get filtered records with caching. Returns (filtered_records, cache_timestamp)."""
    now = time.time()
    if (not force_refresh
            and _cache["filtered_records"] is not None
            and (now - _cache["timestamp"]) < CACHE_TTL):
        return _cache["filtered_records"], _cache["timestamp"]

    records = fetch_all_records()
    filtered = filter_test_entries(records)
    _cache["filtered_records"] = filtered
    _cache["timestamp"] = now
    return filtered, now


def invalidate_cache():
    """Clear the cache so next read fetches fresh data."""
    _cache["filtered_records"] = None
    _cache["timestamp"] = 0


def fetch_all_records():
    """Fetch all records from Airtable with pagination"""
    all_records = []
    offset = None

    while True:
        params = {"pageSize": 100}
        if offset:
            params["offset"] = offset

        response = requests.get(AIRTABLE_URL, headers=HEADERS, params=params)
        data = response.json()

        records = data.get("records", [])
        all_records.extend(records)

        offset = data.get("offset")
        if not offset:
            break

    return all_records


def filter_test_entries(records):
    """Remove entries where email or source contains 'test'"""
    filtered = []
    for record in records:
        fields = record.get("fields", {})
        email = fields.get("Applicant_Email", "").lower()
        source = fields.get("Source", "").lower()

        if "test" not in email and "test" not in source:
            filtered.append(record)

    return filtered


def calculate_metrics(records):
    """Calculate all dashboard metrics from records"""
    fields_list = [r.get("fields", {}) for r in records]

    # Total Applications
    total_applications = len(fields_list)

    # Source Breakdown
    sources = [f.get("Source", "Unknown") for f in fields_list]
    source_breakdown = Counter(sources)
    source_breakdown = dict(sorted(source_breakdown.items(), key=lambda x: x[1], reverse=True))

    # Level Breakdown
    levels = [f.get("Filt_Level", "Unknown") for f in fields_list]
    level_breakdown = Counter(levels)
    level_order = {"Level 5": 1, "Level 4": 2, "Level 3": 3, "Unknown": 4}
    level_breakdown = dict(sorted(level_breakdown.items(), key=lambda x: level_order.get(x[0], 5)))

    # Top-Tier MBA
    top_tier_mba = []
    mba_institutions = []
    for f in fields_list:
        if f.get("is_Top-Tier", "").lower() == "yes":
            top_tier_mba.append(f)
            inst = f.get("MBA_Institution_Name", "Unknown")
            if inst and inst not in ["N/A", "Not specified", ""]:
                mba_institutions.append(inst)

    mba_institution_breakdown = Counter(mba_institutions)
    mba_institution_breakdown = dict(sorted(mba_institution_breakdown.items(), key=lambda x: x[1], reverse=True))

    # Top-Tier UG (only for those WITHOUT a Top-Tier MBA)
    top_tier_ug = []
    ug_institutions = []
    for f in fields_list:
        is_top_tier_ug = f.get("UG_School_Top_Tier", "").lower() == "yes"
        is_top_tier_mba = f.get("is_Top-Tier", "").lower() == "yes"

        if is_top_tier_ug and not is_top_tier_mba:
            top_tier_ug.append(f)
            inst = f.get("Undergrad_School_Name", "Unknown")
            if inst and inst not in ["N/A", "Not specified", ""]:
                ug_institutions.append(inst)

    ug_institution_breakdown = Counter(ug_institutions)
    ug_institution_breakdown = dict(sorted(ug_institution_breakdown.items(), key=lambda x: x[1], reverse=True))

    # Section 2: Video Submissions
    video_submissions = []
    for f in fields_list:
        video_link = f.get("Video_Link", "").strip()
        if video_link:
            video_submissions.append(f)

    video_count = len(video_submissions)

    # Video submissions by level
    video_levels = [f.get("Filt_Level", "Unknown") for f in video_submissions]
    video_level_breakdown = Counter(video_levels)
    video_level_breakdown = dict(sorted(video_level_breakdown.items(), key=lambda x: level_order.get(x[0], 5)))

    # Video submissions by MBA status
    video_mba_breakdown = {"Top-Tier MBA": 0, "Other MBA": 0, "No MBA": 0}
    video_mba_institutions = []
    for f in video_submissions:
        has_mba = f.get("Has_MBA", "").lower() == "yes"
        is_top_tier = f.get("is_Top-Tier", "").lower() == "yes"

        if is_top_tier:
            video_mba_breakdown["Top-Tier MBA"] += 1
            inst = f.get("MBA_Institution_Name", "Unknown")
            if inst and inst not in ["N/A", "Not specified", ""]:
                video_mba_institutions.append(inst)
        elif has_mba:
            video_mba_breakdown["Other MBA"] += 1
        else:
            video_mba_breakdown["No MBA"] += 1

    video_mba_institution_breakdown = Counter(video_mba_institutions)
    video_mba_institution_breakdown = dict(sorted(video_mba_institution_breakdown.items(), key=lambda x: x[1], reverse=True))

    # Video submissions by Stage 1 Status
    video_stage_breakdown = {"Selected": 0, "Rejected": 0, "Not Reviewed": 0}
    for f in video_submissions:
        stage = f.get("Stage 1 Status", "").strip()
        if stage == "Selected":
            video_stage_breakdown["Selected"] += 1
        elif stage == "Rejected":
            video_stage_breakdown["Rejected"] += 1
        else:
            video_stage_breakdown["Not Reviewed"] += 1

    # AI Recommendation breakdown
    ai_rec_breakdown = {"Strong Yes": 0, "Yes": 0, "Maybe": 0, "No": 0, "Not Evaluated": 0}
    for f in video_submissions:
        ai_rec = f.get("AI_Rec", "").strip()
        if ai_rec in ai_rec_breakdown:
            ai_rec_breakdown[ai_rec] += 1
        else:
            ai_rec_breakdown["Not Evaluated"] += 1

    # Transcript Processing breakdown (based on AI_Status)
    # Exclude Stage 1 Rejected candidates from the count
    transcript_processed = 0
    transcript_not_processed = 0
    for f in video_submissions:
        stage1_status = f.get("Stage 1 Status", "").strip()
        if stage1_status == "Rejected":
            continue
        ai_status = f.get("AI_Status", "").strip()
        if ai_status == "Completed":
            transcript_processed += 1
        else:
            transcript_not_processed += 1

    return {
        "total_applications": total_applications,
        "source_breakdown": source_breakdown,
        "level_breakdown": level_breakdown,
        "top_tier_mba_count": len(top_tier_mba),
        "mba_institutions": mba_institution_breakdown,
        "top_tier_ug_count": len(top_tier_ug),
        "ug_institutions": ug_institution_breakdown,
        "video_count": video_count,
        "video_level_breakdown": video_level_breakdown,
        "video_mba_breakdown": video_mba_breakdown,
        "video_mba_institutions": video_mba_institution_breakdown,
        "video_stage_breakdown": video_stage_breakdown,
        "ai_rec_breakdown": ai_rec_breakdown,
        "transcript_processed": transcript_processed,
        "transcript_not_processed": transcript_not_processed
    }


@app.route("/")
def dashboard():
    """Main dashboard page"""
    try:
        force = request.args.get('refresh') == '1'
        filtered_records, cached_at = get_cached_data(force_refresh=force)
        metrics = calculate_metrics(filtered_records)
        return render_template("index.html", metrics=metrics, cached_at=cached_at)
    except Exception as e:
        return render_template("index.html", error=str(e), metrics=None)


@app.route("/api/metrics")
def api_metrics():
    """API endpoint for metrics"""
    try:
        force = request.args.get('refresh') == '1'
        filtered_records, cached_at = get_cached_data(force_refresh=force)
        metrics = calculate_metrics(filtered_records)
        metrics["cached_at"] = cached_at
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/video-submitters")
def api_video_submitters():
    """API endpoint for video submitters list with full details including AI evaluation"""
    try:
        force = request.args.get('refresh') == '1'
        filtered_records, _ = get_cached_data(force_refresh=force)

        video_submitters = []
        for record in filtered_records:
            fields = record.get("fields", {})
            video_link = fields.get("Video_Link", "").strip()

            if video_link:
                # Skip candidates rejected after video evaluation
                ai_rec = fields.get("AI_Rec", "").strip()
                if ai_rec == "No":
                    continue

                resume_pdf = fields.get("Resume_pdf", [])
                pdf_url = resume_pdf[0].get("url", "") if resume_pdf else ""

                # Get name and append (S) for student applications
                applicant_name = fields.get("Applicant_Name", "")
                source = fields.get("Source", "")
                if source == "student_application":
                    applicant_name = f"{applicant_name} (S)"

                submitter = {
                    "id": record.get("id"),
                    "email": fields.get("Applicant_Email", ""),
                    "name": applicant_name,
                    "phone": fields.get("Applicant_Phone", ""),
                    "mba_college": fields.get("MBA_Institution_Name", "N/A"),
                    "has_mba": fields.get("Has_MBA", "No"),
                    "is_top_tier_mba": fields.get("is_Top-Tier", "No"),
                    "total_exp": fields.get("Total_Exp", ""),
                    "relevant_exp": fields.get("Relevant_Exp", ""),
                    "level": fields.get("Filt_Level", ""),
                    "video_link": video_link,
                    "pdf_url": pdf_url,
                    "stage_1_status": fields.get("Stage 1 Status", ""),
                    "source": source,
                    "ug_school": fields.get("Undergrad_School_Name", "N/A"),
                    "ug_top_tier": fields.get("UG_School_Top_Tier", "No"),
                    "has_relevant_exp": fields.get("Has_Relevant_Exp", ""),
                    "technical_analytical": fields.get("Technical_Analytical", ""),
                    "qualification_status": fields.get("Qualification_Status", ""),
                    "comments": fields.get("Comments", ""),
                    "referrer": fields.get("Referrer", ""),
                    "analysis": fields.get("Analysis_explanation", ""),
                    "reviewer_comments": fields.get("Reviewer Comments", ""),
                    # AI Evaluation fields
                    "ai_eval": fields.get("AI_Eval"),
                    "ai_mindset": fields.get("AI_Mindset"),
                    "ai_rec": fields.get("AI_Rec", ""),
                    "ai_report_url": fields.get("AI_Report_URL", ""),
                    "ai_status": fields.get("AI_Status", ""),
                    "has_transcript": bool(fields.get("Video_link_transcript", "").strip()),
                    "all_fields": fields
                }
                video_submitters.append(submitter)

        # Sort by level (Level 5 first, then 4, then 3)
        level_order = {"Level 5": 1, "Level 4": 2, "Level 3": 3}
        video_submitters.sort(key=lambda x: level_order.get(x.get("level", ""), 99))

        return jsonify(video_submitters)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/update-status", methods=["POST"])
def update_status():
    """Update Stage 1 Status in Airtable"""
    try:
        data = request.get_json()
        record_id = data.get("record_id")
        new_status = data.get("status")

        if not record_id:
            return jsonify({"error": "record_id is required"}), 400

        update_url = f"{AIRTABLE_URL}/{record_id}"
        payload = {
            "fields": {
                "Stage 1 Status": new_status if new_status else None
            }
        }

        response = requests.patch(update_url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            invalidate_cache()
            return jsonify({"success": True, "record": response.json()})
        else:
            return jsonify({"error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/update-comments", methods=["POST"])
def update_comments():
    """Update Reviewer Comments in Airtable"""
    try:
        data = request.get_json()
        record_id = data.get("record_id")
        comments = data.get("comments", "")

        if not record_id:
            return jsonify({"error": "record_id is required"}), 400

        update_url = f"{AIRTABLE_URL}/{record_id}"
        payload = {
            "fields": {
                "Reviewer Comments": comments
            }
        }

        response = requests.patch(update_url, headers=HEADERS, json=payload)

        if response.status_code == 200:
            invalidate_cache()
            return jsonify({"success": True, "record": response.json()})
        else:
            return jsonify({"error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/trigger-evaluation", methods=["POST"])
def trigger_evaluation():
    """Trigger AI evaluation for a candidate via Hiring API"""
    try:
        data = request.get_json()
        record_id = data.get("record_id")
        force_rerun = data.get("force_rerun", False)

        if not record_id:
            return jsonify({"error": "record_id is required"}), 400

        # If force_rerun, clear existing AI fields first
        if force_rerun:
            update_url = f"{AIRTABLE_URL}/{record_id}"
            clear_payload = {
                "fields": {
                    "AI_Eval": None,
                    "AI_Mindset": None,
                    "AI_Rec": None,
                    "AI_Report_URL": None,
                    "AI_Status": None
                }
            }
            requests.patch(update_url, headers=HEADERS, json=clear_payload)

        # Call the Hiring API evaluation endpoint
        eval_url = f"{HIRING_API_URL}/api/v1/evaluations/evaluate"
        response = requests.post(
            eval_url,
            json={"record_id": record_id},
            timeout=180  # 3 minute timeout for evaluation with thinking
        )

        if response.status_code == 200:
            invalidate_cache()
            return jsonify(response.json())
        else:
            return jsonify({"error": response.text}), response.status_code

    except requests.Timeout:
        return jsonify({"error": "Evaluation timed out. Please try again."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5012)
