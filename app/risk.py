from . import db
from .models import SensorReading, Alert

# DEMONSTRATION thresholds - must be reviewed by an agriculture expert
HUMIDITY_HIGH = 80      # %
TEMP_MIN, TEMP_MAX = 25, 38  # degrees C
SOIL_DRY = 20           # %
WINDOW = 3              # number of consecutive readings


def _open_alert(farm, kind, message):
    exists = Alert.query.filter_by(farm_id=farm.id, kind=kind, acknowledged=False).first()
    if not exists:
        db.session.add(Alert(farm_id=farm.id, kind=kind, message=message))


def evaluate(farm):
    recent = (SensorReading.query.filter_by(farm_id=farm.id)
              .order_by(SensorReading.created_at.desc()).limit(WINDOW).all())
    if len(recent) < WINDOW:
        return

    if all(r.humidity >= HUMIDITY_HIGH and TEMP_MIN <= r.temperature <= TEMP_MAX for r in recent):
        _open_alert(farm, "pest_risk",
                    "Hot and humid conditions for several readings: higher whitefly / "
                    "leaf curl risk. Please scout your field and upload a leaf photo "
                    "if you see symptoms.")

    latest = recent[0]
    if latest.soil_moisture is not None and latest.soil_moisture < SOIL_DRY:
        _open_alert(farm, "dry_soil", "Soil moisture is low. Please check irrigation.")

    db.session.commit()
