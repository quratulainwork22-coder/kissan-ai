from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="farmer")  # farmer / adviser / admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    farms = db.relationship("Farm", backref="owner", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Farm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150))
    crop = db.Column(db.String(50), default="Cotton")
    api_key = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cases = db.relationship("Case", backref="farm", lazy=True)
    readings = db.relationship("SensorReading", backref="farm", lazy=True)
    alerts = db.relationship("Alert", backref="farm", lazy=True)


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farm.id"), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    symptoms = db.Column(db.Text)
    predicted_label = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    status = db.Column(db.String(20), default="Submitted")  # Submitted / Reviewed / Closed
    adviser_label = db.Column(db.String(50))
    adviser_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    followups = db.relationship("FollowUp", backref="case", lazy=True,
                                order_by="FollowUp.created_at")


class FollowUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    note = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Guidance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    disease = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farm.id"), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    soil_moisture = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey("farm.id"), nullable=False)
    kind = db.Column(db.String(30), nullable=False)
    message = db.Column(db.Text, nullable=False)
    acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
