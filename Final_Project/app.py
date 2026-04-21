"""
app.py
Campus Advocacy Toolkit — Flask web application
Run with: python app.py
Requires ANTHROPIC_API_KEY in your .env file.
"""

import json
import os
import uuid
from collections import Counter
from datetime import date

import anthropic
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for

from data import (
    AUDIENCE_TYPES,
    FOUNDATION_CHOICES,
    FOUNDATIONS,
    LETTER_TYPES,
    PIPELINE_STATUSES,
    RESOURCES,
    SCHOOL_TYPES,
    URGENCY_LEVELS,
)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = Flask(__name__)

PIPELINE_FILE = os.path.join(os.path.dirname(__file__), "pipeline.json")
RESOURCE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "resource_cache.json")

claude = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

LETTER_SYSTEM_PROMPT = (
    "You are a professional partnership development writer at the Campus Advocacy Toolkit, "
    "a parent organization that oversees a portfolio of artist-founded nonprofits. "
    "Your job is to write outbound outreach letters to college and university administrators "
    "on behalf of the organization, pitching the nonprofits' programs as campus partnerships. "
    "You write from the perspective of the nonprofit organization reaching out to the school — "
    "never the school reaching out. Your letters are formal, warm, and compelling. "
    "They are always complete and ready to send with no further editing. "
    "You use specific details about the target institution to make each letter feel personal, "
    "not generic. You never use placeholder text or brackets. "
    "You write at a professional level appropriate for deans, provosts, and student affairs administrators."
)


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def load_pipeline():
    if not os.path.exists(PIPELINE_FILE):
        return []
    with open(PIPELINE_FILE, "r") as f:
        return json.load(f)


def save_pipeline(data):
    with open(PIPELINE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_resource_cache():
    if not os.path.exists(RESOURCE_CACHE_FILE):
        return {}
    with open(RESOURCE_CACHE_FILE, "r") as f:
        return json.load(f)


def save_resource_cache(cache):
    with open(RESOURCE_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


# ---------------------------------------------------------------------------
# Routes — Overview
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


# ---------------------------------------------------------------------------
# Routes — Foundation detail
# ---------------------------------------------------------------------------

@app.route("/foundation/<fid>")
def foundation_detail(fid):
    if fid not in FOUNDATIONS:
        return redirect(url_for("index"))
    foundation = FOUNDATIONS[fid]
    resources = RESOURCES.get(fid, [])
    return render_template(
        "foundation.html",
        f=foundation,
        resources=resources,
        fid=fid,
    )


# ---------------------------------------------------------------------------
# Routes — Resources
# ---------------------------------------------------------------------------

@app.route("/resources")
def resources():
    selected_foundation = request.args.get("foundation", "all")
    selected_audience = request.args.get("audience", "all")

    if selected_foundation != "all" and selected_foundation in RESOURCES:
        filtered = {selected_foundation: RESOURCES[selected_foundation]}
    else:
        filtered = RESOURCES
        selected_foundation = "all"

    if selected_audience != "all":
        filtered = {
            fid: [r for r in rlist if r["audience"] == selected_audience]
            for fid, rlist in filtered.items()
            if any(r["audience"] == selected_audience for r in rlist)
        }

    return render_template(
        "resources.html",
        resources=filtered,
        foundations=FOUNDATIONS,
        selected=selected_foundation,
        selected_audience=selected_audience,
        foundation_choices=FOUNDATION_CHOICES,
        audience_types=AUDIENCE_TYPES,
    )


@app.route("/resource/<fid>/<int:idx>")
def resource_view(fid, idx):
    if fid not in RESOURCES or idx >= len(RESOURCES[fid]):
        return redirect(url_for("resources"))
    resource = RESOURCES[fid][idx]
    foundation = FOUNDATIONS[fid]

    cache = load_resource_cache()
    cache_key = f"{fid}_{idx}"
    generated_content = cache.get(cache_key)

    return render_template(
        "resource_view.html",
        resource=resource,
        foundation=foundation,
        fid=fid,
        idx=idx,
        generated_content=generated_content,
    )


@app.route("/resource/<fid>/<int:idx>/generate", methods=["POST"])
def resource_generate(fid, idx):
    if fid not in RESOURCES or idx >= len(RESOURCES[fid]):
        return redirect(url_for("resources"))
    resource = RESOURCES[fid][idx]
    foundation = FOUNDATIONS[fid]

    cache = load_resource_cache()
    cache_key = f"{fid}_{idx}"

    if cache_key not in cache:
        prompt = (
            f"Write the full content for a school resource called \"{resource['title']}\" "
            f"published by {foundation['name']} (founded by {foundation['founder']}).\n\n"
            f"Resource type: {resource['type']}\n"
            f"Intended audience: {resource['audience']}\n"
            f"Description: {resource['description']}\n"
            f"Content preview hint: {resource['content_preview']}\n\n"
            f"Write the complete, usable resource content. Format it clearly with sections, "
            f"numbered steps where appropriate, and any templates or scripts described. "
            f"It should be immediately usable by someone at a school with no prior training. "
            f"Write approximately 600-900 words of substantive, actionable content."
        )
        try:
            response = claude.messages.create(
                model="claude-opus-4-7",
                max_tokens=1400,
                system=[{
                    "type": "text",
                    "text": (
                        "You are an expert nonprofit curriculum writer creating practical, "
                        "school-ready resources for The Campus Advocacy Toolkit. Your resources "
                        "are clear, professional, and immediately actionable. You write for "
                        "educators and school administrators who are motivated but time-constrained."
                    ),
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": prompt}],
            )
            generated = response.content[0].text.strip()
        except Exception as e:
            generated = f"Content generation encountered an error: {e}\n\nPlease try again."

        cache[cache_key] = generated
        save_resource_cache(cache)

    return redirect(url_for("resource_view", fid=fid, idx=idx))


# ---------------------------------------------------------------------------
# Routes — Letter Builder
# ---------------------------------------------------------------------------

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
        letter_type = request.form.get("letter_type", "admin").strip()
        urgency = request.form.get("urgency", "exploratory").strip()
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
                letter_types=LETTER_TYPES,
                urgency_levels=URGENCY_LEVELS,
                form=request.form,
            )

        foundation_names = [
            FOUNDATIONS[fid]["name"]
            for fid in selected_foundations
            if fid in FOUNDATIONS
        ]
        foundation_details = "\n".join(
            f"- {FOUNDATIONS[fid]['name']} (founded by {FOUNDATIONS[fid]['founder']}): "
            f"{FOUNDATIONS[fid]['mission']} Focus area: {FOUNDATIONS[fid]['focus']}."
            for fid in selected_foundations
            if fid in FOUNDATIONS
        )

        letter_type_label = dict(LETTER_TYPES).get(letter_type, "To School Administrator")
        urgency_label = dict(URGENCY_LEVELS).get(urgency, "Exploratory")

        today = date.today().strftime("%B %d, %Y")
        prompt = (
            f"Write a complete, properly formatted outreach letter with the following specifications.\n\n"
            f"CONTEXT: You are writing on behalf of the Campus Advocacy Toolkit (the sender), "
            f"a nonprofit partnership organization, reaching out TO a college or university to pitch a campus partnership.\n\n"
            f"LETTER TYPE: {letter_type_label}\n"
            f"TARGET INSTITUTION: {school_name} ({school_type or 'institution type not specified'})\n"
            f"RECIPIENT (at the college): {admin_name}, {admin_title or 'Administrator'}\n"
            f"SENDER (our organization representative): {submitter_name}, {submitter_role or 'Partnership Development, Campus Advocacy Toolkit'}\n"
            f"TIMELINE/URGENCY: {urgency_label}\n"
            f"WHAT WE KNOW ABOUT THIS INSTITUTION: {campus_context if campus_context else 'No specific context provided — write a compelling general pitch tailored to higher education.'}\n\n"
            f"PROGRAMS WE ARE PITCHING:\n{foundation_details}\n\n"
            f"FORMAT REQUIREMENTS — follow this exact letter structure:\n"
            f"1. Date line: {today}\n"
            f"2. Blank line\n"
            f"3. Recipient block: {admin_name}\\n{admin_title or 'Administrator'}\\n{school_name}\n"
            f"4. Blank line\n"
            f"5. Subject line: Re: [brief descriptive partnership subject]\n"
            f"6. Blank line\n"
            f"7. Salutation: Dear {admin_name},\n"
            f"8. Body paragraphs (3-4 paragraphs) — see content requirements below\n"
            f"9. Closing: Sincerely,\n"
            f"10. Blank line\n"
            f"11. Signature block: {submitter_name}\\n{submitter_role or 'Partnership Development'}\\nCampus Advocacy Toolkit\n\n"
            f"CONTENT REQUIREMENTS:\n"
            f"- Write from the nonprofit's perspective — WE are reaching out to THEM\n"
            f"- Open by referencing why this specific institution is a strong fit for our programs\n"
            f"- Introduce each foundation's programs as opportunities we are offering the campus\n"
            f"- Frame the call to action as an invitation to partner with us, not a request for their help\n"
            f"- Match the urgency level in the call to action\n"
            f"- Close with a specific next step that moves toward a formal partnership\n"
            f"- The letter must be ready to send with zero editing needed\n"
            f"- Do not use placeholder brackets or generic language\n"
            f"- Use plain text only — no markdown, no asterisks, no bullet symbols"
        )

        try:
            response = claude.messages.create(
                model="claude-opus-4-7",
                max_tokens=1500,
                system=[{
                    "type": "text",
                    "text": LETTER_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }],
                messages=[{"role": "user", "content": prompt}],
            )
            letter_text = response.content[0].text.strip()
        except Exception as e:
            letter_text = (
                f"Letter generation failed: {e}\n\n"
                "Please check your ANTHROPIC_API_KEY and try again."
            )

        return render_template(
            "letter_result.html",
            letter_text=letter_text,
            school_name=school_name,
            admin_name=admin_name,
            foundation_names=foundation_names,
            letter_type_label=letter_type_label,
        )

    return render_template(
        "letter_builder.html",
        errors=[],
        foundation_choices=FOUNDATION_CHOICES,
        school_types=SCHOOL_TYPES,
        letter_types=LETTER_TYPES,
        urgency_levels=URGENCY_LEVELS,
        form={},
    )


# ---------------------------------------------------------------------------
# Routes — Pipeline
# ---------------------------------------------------------------------------

@app.route("/pipeline")
def pipeline():
    schools = load_pipeline()
    status_filter = request.args.get("status", "all")

    status_counts = Counter(s["status"] for s in schools)
    total = len(schools)

    if status_filter != "all":
        filtered_schools = [s for s in schools if s["status"] == status_filter]
    else:
        filtered_schools = schools

    return render_template(
        "pipeline.html",
        schools=filtered_schools,
        all_schools=schools,
        statuses=PIPELINE_STATUSES,
        status_filter=status_filter,
        status_counts=status_counts,
        total=total,
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
        "last_updated": str(date.today()),
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
            school["notes"] = request.form.get("notes", school.get("notes", ""))
            school["last_updated"] = str(date.today())
            break
    save_pipeline(schools)
    return redirect(url_for("pipeline"))


@app.route("/pipeline/delete/confirm/<school_id>")
def pipeline_delete_confirm(school_id):
    schools = load_pipeline()
    school = next((s for s in schools if s["id"] == school_id), None)
    if not school:
        return redirect(url_for("pipeline"))
    return render_template("pipeline_delete_confirm.html", school=school)


@app.route("/pipeline/delete/<school_id>", methods=["POST"])
def pipeline_delete(school_id):
    schools = load_pipeline()
    schools = [s for s in schools if s["id"] != school_id]
    save_pipeline(schools)
    return redirect(url_for("pipeline"))


# ---------------------------------------------------------------------------
# Routes — Impact
# ---------------------------------------------------------------------------

@app.route("/impact")
def impact():
    schools = load_pipeline()
    total = len(schools)
    status_counts = Counter(s["status"] for s in schools)

    foundation_counts = Counter()
    for school in schools:
        for fid in school.get("foundations", []):
            foundation_counts[fid] += 1

    active_foundations = {
        fid: count
        for fid, count in foundation_counts.items()
        if fid in FOUNDATIONS
    }

    combined_impact = [
        stat
        for f in FOUNDATIONS.values()
        for stat in f["impact_stats"]
    ]

    return render_template(
        "impact.html",
        schools=schools,
        total=total,
        status_counts=status_counts,
        active_foundations=active_foundations,
        foundations=FOUNDATIONS,
        combined_impact=combined_impact,
        statuses=PIPELINE_STATUSES,
        foundation_choices=FOUNDATION_CHOICES,
    )


if __name__ == "__main__":
    app.run(debug=True)
