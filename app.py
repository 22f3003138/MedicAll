from flask import Flask
from models import db, init_db
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
database_uri = os.getenv('DATABASE_URI', f'sqlite:///{os.path.join(basedir, "hospital.db")}')

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'


db.init_app(app)

with app.app_context():
    init_db()

from flask_login import LoginManager
from models import User

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

from routes.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from routes.main import main as main_blueprint
app.register_blueprint(main_blueprint)

from routes.admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint)

from routes.doctor import doctor as doctor_blueprint
app.register_blueprint(doctor_blueprint)

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])

