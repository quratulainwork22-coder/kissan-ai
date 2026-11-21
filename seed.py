from app import create_app, db
from app.models import User, Farm, Guidance

app = create_app()

GUIDANCE = [
    ("healthy", "Healthy leaf"),
    ("curl_virus", "Cotton Leaf Curl Virus (CLCuV)"),
    ("bacterial_blight", "Bacterial Blight"),
]

with app.app_context():
    def get_or_create_user(email, name, role, password):
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, name=name, role=role)
            user.set_password(password)
            db.session.add(user)
        return user

    get_or_create_user("adviser@kissan.local", "Demo Adviser", "adviser", "adviser123")
    farmer = get_or_create_user("farmer@kissan.local", "Demo Farmer", "farmer", "farmer123")
    db.session.commit()

    if not Farm.query.filter_by(api_key="demo-key-123").first():
        db.session.add(Farm(user_id=farmer.id, name="Demo Farm", location="Sadiqabad",
                            crop="Cotton", api_key="demo-key-123"))

    for code, title in GUIDANCE:
        if not Guidance.query.filter_by(disease=code).first():
            db.session.add(Guidance(
                disease=code, title=title, approved=False,
                content="DRAFT - write this from official Punjab Agriculture Department "
                        "advisories. It will be visible to farmers only after adviser approval."))
    db.session.commit()
    print("Seed complete. Farmer: farmer@kissan.local / farmer123, "
          "Adviser: adviser@kissan.local / adviser123")
