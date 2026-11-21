import os
import secrets
import uuid
from functools import wraps

from flask import (Blueprint, render_template, request, redirect, url_for, flash,
                   abort, jsonify, current_app)
from flask_login import login_user, logout_user, login_required, current_user

from . import db
from .models import User, Farm, Case, FollowUp, Guidance, SensorReading, Alert
from .ml import predict
from .risk import evaluate

bp = Blueprint("main", __name__)

ALLOWED_EXT = {"jpg", "jpeg", "png"}
LABELS = {
    "healthy": "Healthy",
    "curl_virus": "Cotton Leaf Curl Virus",
    "bacterial_blight": "Bacterial Blight",
    "uncertain": "Uncertain - needs adviser review",
    "model_not_ready": "Model not trained yet",
}
REVIEW_LABELS = ["healthy", "curl_virus", "bacterial_blight", "uncertain"]


@bp.app_template_filter("label")
def label_filter(code):
    return LABELS.get(code, code or "-")


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


def is_staff():
    return current_user.role in ("adviser", "admin")


def can_view_farm(farm):
    return is_staff() or farm.user_id == current_user.id


def save_image(file):
    if "." not in file.filename:
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXT:
        return None
    name = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
    return name


# ---------- Auth ----------
@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.adviser" if is_staff() else "main.dashboard"))
    return redirect(url_for("main.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Please fill all fields (password at least 6 characters).", "error")
        elif User.query.filter_by(email=email).first():
            flash("This email is already registered.", "error")
        else:
            user = User(name=name, email=email, role="farmer")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Please log in.", "success")
            return redirect(url_for("main.login"))
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email", "").strip().lower()).first()
        if user and user.check_password(request.form.get("password", "")):
            login_user(user)
            return redirect(url_for("main.index"))
        flash("Wrong email or password.", "error")
    return render_template("login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))


# ---------- Farmer ----------
@bp.route("/dashboard")
@role_required("farmer")
def dashboard():
    farms = Farm.query.filter_by(user_id=current_user.id).all()
    ids = [f.id for f in farms]
    cases, alerts = [], []
    if ids:
        cases = (Case.query.filter(Case.farm_id.in_(ids))
                 .order_by(Case.created_at.desc()).limit(10).all())
        alerts = (Alert.query.filter(Alert.farm_id.in_(ids), Alert.acknowledged.is_(False))
                  .order_by(Alert.created_at.desc()).all())
    return render_template("dashboard.html", farms=farms, cases=cases, alerts=alerts)


@bp.route("/farms/new", methods=["POST"])
@role_required("farmer")
def new_farm():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Farm name is required.", "error")
        return redirect(url_for("main.dashboard"))
    farm = Farm(user_id=current_user.id, name=name,
                location=request.form.get("location", "").strip(),
                crop=request.form.get("crop", "Cotton").strip() or "Cotton",
                api_key=secrets.token_hex(16))
    db.session.add(farm)
    db.session.commit()
    flash("Farm added.", "success")
    return redirect(url_for("main.farm_detail", farm_id=farm.id))


@bp.route("/farms/<int:farm_id>")
@login_required
def farm_detail(farm_id):
    farm = db.get_or_404(Farm, farm_id)
    if not can_view_farm(farm):
        abort(403)
    latest = (SensorReading.query.filter_by(farm_id=farm.id)
              .order_by(SensorReading.created_at.desc()).first())
    alerts = (Alert.query.filter_by(farm_id=farm.id)
              .order_by(Alert.created_at.desc()).limit(10).all())
    return render_template("farm.html", farm=farm, latest=latest, alerts=alerts)


@bp.route("/alerts/<int:alert_id>/ack", methods=["POST"])
@login_required
def ack_alert(alert_id):
    alert = db.get_or_404(Alert, alert_id)
    if not can_view_farm(alert.farm):
        abort(403)
    alert.acknowledged = True
    db.session.commit()
    return redirect(request.referrer or url_for("main.index"))


@bp.route("/cases/new", methods=["GET", "POST"])
@role_required("farmer")
def new_case():
    farms = Farm.query.filter_by(user_id=current_user.id).all()
    if not farms:
        flash("Please add a farm first.", "error")
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        farm = db.session.get(Farm, request.form.get("farm_id", type=int))
        if not farm or farm.user_id != current_user.id:
            abort(403)
        file = request.files.get("image")
        if not file or not file.filename:
            flash("Please choose a leaf photo.", "error")
            return redirect(request.url)
        filename = save_image(file)
        if not filename:
            flash("Only JPG or PNG images are allowed.", "error")
            return redirect(request.url)
        label, confidence = predict(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
        case = Case(farm_id=farm.id, image_path=filename,
                    symptoms=request.form.get("symptoms", "").strip(),
                    predicted_label=label, confidence=confidence)
        db.session.add(case)
        db.session.commit()
        return redirect(url_for("main.case_detail", case_id=case.id))
    return render_template("new_case.html", farms=farms)


@bp.route("/cases/<int:case_id>")
@login_required
def case_detail(case_id):
    case = db.get_or_404(Case, case_id)
    if not can_view_farm(case.farm):
        abort(403)
    final_label = case.adviser_label or case.predicted_label
    guidance = Guidance.query.filter_by(disease=final_label, approved=True).first()
    return render_template("case.html", case=case, guidance=guidance,
                           review_labels=REVIEW_LABELS)


@bp.route("/cases/<int:case_id>/followup", methods=["POST"])
@role_required("farmer")
def add_followup(case_id):
    case = db.get_or_404(Case, case_id)
    if case.farm.user_id != current_user.id:
        abort(403)
    note = request.form.get("note", "").strip()
    if not note:
        flash("Please write what action you took.", "error")
        return redirect(url_for("main.case_detail", case_id=case.id))
    image_name = None
    file = request.files.get("image")
    if file and file.filename:
        image_name = save_image(file)
    db.session.add(FollowUp(case_id=case.id, note=note, image_path=image_name))
    db.session.commit()
    flash("Follow-up saved.", "success")
    return redirect(url_for("main.case_detail", case_id=case.id))


# ---------- Adviser ----------
@bp.route("/adviser")
@role_required("adviser", "admin")
def adviser():
    open_cases = (Case.query.filter(Case.status != "Closed")
                  .order_by(Case.created_at.desc()).all())
    guidance = Guidance.query.order_by(Guidance.disease).all()
    return render_template("adviser.html", cases=open_cases, guidance=guidance)


@bp.route("/adviser/cases/<int:case_id>/review", methods=["POST"])
@role_required("adviser", "admin")
def review_case(case_id):
    case = db.get_or_404(Case, case_id)
    label = request.form.get("adviser_label")
    status = request.form.get("status")
    if label not in REVIEW_LABELS or status not in ("Reviewed", "Closed"):
        abort(400)
    case.adviser_label = label
    case.adviser_note = request.form.get("adviser_note", "").strip()
    case.status = status
    db.session.commit()
    flash("Case review saved.", "success")
    return redirect(url_for("main.case_detail", case_id=case.id))


@bp.route("/adviser/guidance/<int:guidance_id>", methods=["GET", "POST"])
@role_required("adviser", "admin")
def edit_guidance(guidance_id):
    g = db.get_or_404(Guidance, guidance_id)
    if request.method == "POST":
        g.title = request.form.get("title", g.title).strip()
        g.content = request.form.get("content", g.content).strip()
        g.approved = request.form.get("approved") == "on"
        g.approved_by = current_user.id if g.approved else None
        db.session.commit()
        flash("Guidance saved.", "success")
        return redirect(url_for("main.adviser"))
    return render_template("guidance_edit.html", g=g)


# ---------- IoT API ----------
@bp.route("/api/readings", methods=["POST"])
def api_readings():
    key = request.headers.get("X-API-Key", "")
    farm = Farm.query.filter_by(api_key=key).first() if key else None
    if not farm:
        return jsonify(error="invalid api key"), 401
    data = request.get_json(silent=True) or {}
    try:
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        soil = data.get("soil_moisture")
        soil = float(soil) if soil is not None else None
    except (KeyError, TypeError, ValueError):
        return jsonify(error="temperature and humidity are required numbers"), 400
    if not (-20 <= temperature <= 70 and 0 <= humidity <= 100):
        return jsonify(error="reading out of range"), 400
    reading = SensorReading(farm_id=farm.id, temperature=temperature,
                            humidity=humidity, soil_moisture=soil)
    db.session.add(reading)
    db.session.commit()
    evaluate(farm)
    return jsonify(status="ok", id=reading.id), 201


@bp.route("/api/farms/<int:farm_id>/readings")
@login_required
def api_farm_readings(farm_id):
    farm = db.get_or_404(Farm, farm_id)
    if not can_view_farm(farm):
        abort(403)
    rows = (SensorReading.query.filter_by(farm_id=farm.id)
            .order_by(SensorReading.created_at.desc()).limit(50).all())[::-1]
    return jsonify([{
        "time": r.created_at.strftime("%H:%M:%S"),
        "temperature": r.temperature,
        "humidity": r.humidity,
        "soil_moisture": r.soil_moisture,
    } for r in rows])
