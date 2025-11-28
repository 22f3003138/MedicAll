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

@login_manager.unauthorized_handler
def unauthorized():
    from flask import request, jsonify, redirect, url_for
    if request.path.startswith('/api'):
        return jsonify({'error': 'Unauthorized'}), 401
    return redirect(url_for('auth.login'))

@app.errorhandler(404)
def page_not_found(e):
    from flask import render_template
    return render_template('404.html'), 404

from routes.auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

from routes.main import main as main_blueprint
app.register_blueprint(main_blueprint)

from routes.admin import admin as admin_blueprint
app.register_blueprint(admin_blueprint)

from routes.doctor import doctor as doctor_blueprint
app.register_blueprint(doctor_blueprint)

from routes.patient import patient as patient_blueprint
app.register_blueprint(patient_blueprint)

from routes.api import api as api_blueprint
app.register_blueprint(api_blueprint)

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])

