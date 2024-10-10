import os
from app import app, db, bcrypt
from app.models import User

@app.cli.command('seeds')
def seeds():
    with app.app_context():
        username = os.getenv('APP_ADMIN_USERNAME')
        password = os.getenv('APP_ADMIN_PASSWORD')

        db.create_all()
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin_user = User(username=username, password=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print(f'Admin user {username} created successfully.')
