from app import create_app
from app.models import db
from app.seeder import seed_admin
from app.models import MembershipPlan, Membership, MembershipRenewal, User

app = create_app()

with app.app_context():
    # Drop existing table
    # User.__table__.drop(db.engine)
    # MembershipRenewal.__table__.drop(db.engine)
    db.create_all()
    seed_admin()

@app.route('/')
def home():
    return "Hello World!"

if __name__ == "__main__":
    app.run(debug=True)