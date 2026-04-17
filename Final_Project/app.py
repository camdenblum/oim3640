"""
app.py
Campus Advocacy Toolkit — Flask web application
Run with: python app.py
"""

import json
import os
import uuid
from datetime import date

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from openai import OpenAI

from data import (
    FOUNDATION_CHOICES,
    FOUNDATIONS,
    PIPELINE_STATUSES,
    RESOURCES,
    SCHOOL_TYPES,
)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

PIPELINE_FILE = os.path.join(os.path.dirname(__file__), "pipeline.json")

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Pipeline helpers (JSON file persistence)
# ---------------------------------------------------------------------------

def load_pipeline():
    if not os.path.exists(PIPELINE_FILE):
        return []
    with open(PIPELINE_FILE, "r") as f:
        return json.load(f)


def save_pipeline(data):
    with open(PIPELINE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    pipeline = load_pipeline()
    total_schools = len(pipeline)
    active_partners = sum(1 for s in pipeline if s["status"] == "Active Partner")
    in_progress = sum(1 for s in pipeline if s["status"] in ("Contacted", "Responding"))
    foundations = list(FOUNDATIONS.values())
    return render_template(
        "index.html",
        foundations=foundations,
        total_schools=total_schools,
        active_partners=active_partners,
        in_progress=in_progress,
    )


@app.route("/resources")
def resources():
    selected = request.args.get("foundation", "all")
    if selected != "all" and selected in RESOURCES:
        filtered = {selected: RESOURCES[selected]}
    else:
        filtered = RESOURCES
        selected = "all"
    return render_template(
        "resources.html",
        resources=filtered,
        foundations=FOUNDATIONS,
        selected=selected,
        foundation_choices=FOUNDATION_CHOICES,
    )


@app.route("/letter", methods=["GET", "POST"])
def letter_builder():
    if request.method == "POST":
        school_name = request.form.get("school_name", "").strip()
        school_type = request.form.get("school_type", "").strip()
        admin_name = request.form.get("admin_name", "").strip()
        admin_title = request.form.get("admin_title", "").strip()
        submitter_name = request.form.get("submitter_name", "").strip()
        submitter_role = request.form.get("submitter_role", "").strip()
        campus_context = request.form.get("campus_context", "").strip()
        selected_foundations = request.form.getlist("foundations")

        errors = []
        if not school_name:
            errors.append("School name is required.")
        if not admin_name:
            errors.append("Administrator name is required.")
        if not submitter_name:
            errors.append("Your name is required.")
        if not selected_foundations:
            errors.append("Please select at least one foundation.")

        if errors:
            return render_template(
                "letter_builder.html",
                errors=errors,
                foundation_choices=FOUNDATION_CHOICES,
                school_types=SCHOOL_TYPES,
                form=request.form,
            )

        foundation_names = [
            FOUNDATIONS[fid]["name"]
            for fid in selected_foundations
            if fid in FOUNDATIONS
        ]
        foundation_missions = "\n".join(
            f"- {FOUNDATIONS[fid]['name']}: {FOUNDATIONS[fid]['mission']}"
            for fid in selected_foundations
            if fid in FOUNDATIONS
        )

        prompt = f"""You are a professional nonprofit outreach writer. Write a formal, warm, and compelling outreach letter from a school representative to a school administrator, introducing one or more artist-founded nonprofit foundations and requesting a partnership.

School: {school_name} ({school_type})
Letter recipient: {admin_name}, {admin_title}
Letter sender: {submitter_name}, {submitter_role}
Campus context provided by the sender: {campus_context if campus_context else "None provided"}

Foundations to introduce:
{foundation_missions}

Write a complete, professional letter with:
- A formal salutation
- An engaging opening that references the school's specific context if provided
- A clear explanation of each selected foundation and why it is relevant to this school
- A specific call to action (schedule a meeting, review materials, etc.)
- A professional sign-off from {submitter_name}, {submitter_role} at {school_name}

The letter should be ready to send with no further editing needed. Do not use placeholders. Write it as a real letter."""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                temperature=0.7,
            )
            letter_text = response.choices[0].message.content.strip()
        except Exception as e:
            letter_text = f"[Letter generation failed: {e}]\n\nPlease try again or contact support."

        return render_template(
            "letter_result.html",
            letter_text=letter_text,
            school_name=school_name,
            admin_name=admin_name,
            foundation_names=foundation_names,
        )

    return render_template(
        "letter_builder.html",
        errors=[],
        foundation_choices=FOUNDATION_CHOICES,
        school_types=SCHOOL_TYPES,
        form={},
    )


@app.route("/pipeline")
def pipeline():
    schools = load_pipeline()
    status_filter = request.args.get("status", "all")
    if status_filter != "all":
        schools = [s for s in schools if s["status"] == status_filter]
    return render_template(
        "pipeline.html",
        schools=schools,
        statuses=PIPELINE_STATUSES,
        status_filter=status_filter,
        foundation_choices=FOUNDATION_CHOICES,
        foundations=FOUNDATIONS,
    )


@app.route("/pipeline/add", methods=["POST"])
def pipeline_add():
    schools = load_pipeline()
    foundations_selected = request.form.getlist("foundations")
    new_school = {
        "id": str(uuid.uuid4())[:8],
        "name": request.form.get("name", "").strip(),
        "contact": request.form.get("contact", "").strip(),
        "status": request.form.get("status", "Contacted"),
        "foundations": foundations_selected,
        "notes": request.form.get("notes", "").strip(),
        "date_added": str(date.today()),
    }
    if new_school["name"]:
        schools.append(new_school)
        save_pipeline(schools)
    return redirect(url_for("pipeline"))


@app.route("/pipeline/update/<school_id>", methods=["POST"])
def pipeline_update(school_id):
    schools = load_pipeline()
    for school in schools:
        if school["id"] == school_id:
            school["status"] = request.form.get("status", school["status"])
            school["notes"] = request.form.get("notes", school["notes"])
            break
    save_pipeline(schools)
    return redirect(url_for("pipeline"))


@app.route("/pipeline/delete/<school_id>", methods=["POST"])
def pipeline_delete(school_id):
    schools = load_pipeline()
    schools = [s for s in schools if s["id"] != school_id]
    save_pipeline(schools)
    return redirect(url_for("pipeline"))


if __name__ == "__main__":
    app.run(debug=True)
