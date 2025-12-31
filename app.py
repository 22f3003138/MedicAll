from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager
from dotenv import load_dotenv
import os

from models import db, init_db, User
from routes.auth import auth as auth_blueprint
from routes.main import main as main_blueprint
from routes.admin import admin as admin_blueprint
from routes.doctor import doctor as doctor_blueprint
from routes.patient import patient as patient_blueprint
from routes.api import api as api_blueprint

load_dotenv()

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG')


db.init_app(app)

with app.app_context():
    init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith('/api'):
        return jsonify({'error': 'Unauthorized'}), 401
    return redirect(url_for('auth.login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

app.register_blueprint(auth_blueprint)
app.register_blueprint(main_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(doctor_blueprint)
app.register_blueprint(patient_blueprint)
app.register_blueprint(api_blueprint)

if __name__ == '__main__':
    app.run()

