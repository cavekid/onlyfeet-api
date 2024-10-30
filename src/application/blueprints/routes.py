import json
import sys, os
import logging
import logging.config
from application.database import User, Image, db, migrate_db
from application.util import admin_only, generate
from subprocess import PIPE, run
from flask import Blueprint, jsonify, redirect, render_template, request, current_app, send_file
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

web = Blueprint('web', __name__)
api = Blueprint('api', __name__)

def response(message):
    return jsonify({'message': message})

@web.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@api.route('/register', methods=['POST'])
def user_registration():

    current_app.logger.debug("Entering register")

    if not request.is_json:
        return response('Missing required parameters!'), 401

    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return response('Missing required parameters!'), 401

    user = User.query.filter_by(username=username).first()

    if user:
        return response('User already exists!'), 401

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return response('User registered successfully!')

@api.route('/login', methods=['POST'])
def user_login():

    current_app.logger.debug("Entering login")

    if not request.is_json:
        return response('Missing required parameters!'), 401

    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return response('Missing required parameters!'), 401

    user = User.query.filter_by(username=username).first()

    if not user or not user.password == password:
        return response('Invalid username or password!'), 403

    login_user(user)

    return response('User authenticated successfully!')

# TODO implement
"""
@web.route('/logout')
@login_required
def logout():
    pass
"""

@api.route('/gallery', methods=['GET'])
@login_required
def gallery():

    current_app.logger.debug("Entering gallery") 

    query = Image.query.filter_by(username=current_user.username).all()

    locations = []

    for image in query:
        locations.append(image.location)

    return response(locations)

@api.route('/download_image', methods=['GET'])
@login_required
def download_image():

    current_app.logger.debug("Entering download image")

    if 'file' not in request.args:
        return response('Missing required parameters!'), 401

    query = Image.query.filter_by(location=request.args["file"]).first()

    if query.location:
        return send_file(f"{current_app.config['UPLOAD_FOLDER']}/images/{query.location}")
    else:
        return response("File not found!")

@api.route('/upload', methods=['POST'])
@login_required
def upload_image():

    if 'file' not in request.files or 'label' not in request.form:
        return response('Missing required parameters!'), 401

    file = request.files['file']
    label=request.form["label"]

    if label not in ["sfw", "nsfw"]:
        return response(f"Unsupported label '{label}'. Allowed labels are: sfw, nsfw"), 400

    if file.filename == '':
       return response('Missing required parameters!'), 401

    rand_dir = generate(15)
    upload_dir = f"{current_app.config['UPLOAD_FOLDER']}/images/{rand_dir}/"
    os.makedirs(upload_dir, exist_ok=True)

    filename = secure_filename(str(label + "_" + generate(10)))
    file.save(upload_dir + filename)

    new_file = Image(username=current_user.username, location=f"{rand_dir}/{filename}")
    db.session.add(new_file)
    db.session.commit()

    return response("File successfully uploaded")

# OBSOLETE used for remote debugging.
@api.route('/log_config', methods=['POST'])
@login_required
def log_config():

    if not request.is_json:
        return response('Missing required parameters!'), 401

    data = request.get_json()
    file_name = data.get('filename', '') 

    logging.config.fileConfig(f"{current_app.config['UPLOAD_FOLDER']}/conf/{file_name}")

    return response(data)

# OBSOLETE used for more privileged remote debugging.
@api.route('/run_command', methods=['POST'])
@login_required
@admin_only
def remote_exec():

    if not request.is_json:
            return response('Missing required parameters!')

    data = request.get_json()
    command = data.get('command','')
    result = run(command, stdout=PIPE, stderr=PIPE, shell=True)

    return response(result.stdout.decode())
