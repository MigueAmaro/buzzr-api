"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""



from ctypes.wintypes import HLOCAL
from email import message
from email.policy import default
from hashlib import new
from logging import root
import os
import re
from socket import socket


from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import Channels, db, User, Messages, PrivateMessages
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_socketio import SocketIO, send
import datetime

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = os.environ.get('FLASK_APP_KEY')
socketIo = SocketIO(app, cors_allowed_origins="*", logger=True)
MIGRATE = Migrate(app, db)
jwt = JWTManager(app)
db.init_app(app)
CORS(app)
setup_admin(app)


# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


# Sign_up route
@app.route('/signup', methods = ['POST'])
def sign_up():
    body = request.json
    email = body.get("email", None)
    password = body.get("password", None)
    name = body.get("name", None)
    last_name = body.get("last_name", None)
    username = body.get("username", None)

    if email or password or name or last_name or username is not None:
        correo = User.query.filter_by(email = email).first()
        if correo is not None:
            return jsonify({
                "msg":"Email already exist"
            }), 500
        else:
            usertag = User.query.filter_by(username = username).first()
            if usertag is not None:
                return jsonify({
                    "msg":"username already in use"
                }), 500
            else:
                try:
                    new_user = User(
                        email = email,
                        password = password,
                        first_name = name,
                        last_name = last_name,
                        username = username
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    return jsonify({
                        "msg": "Usuario creado"
                    }), 201
                except Exception as error:
                    db.session.rollback()
                    return jsonify(error.args), 500
    else:
        return jsonify({
            "msg":"Something Happened"
        }), 400


#Log_in route
@app.route('/login', methods=['POST'])
def handle_login():
    
    email = request.json.get("email", None)
    password = request.json.get("password", None)

    if email is not None and password is not None:
        user = User.query.filter_by(email=email, password=password).one_or_none()

        if user is not None:
            create_token = create_access_token(identity = user.id)
            return jsonify({
                "email": user.email,
                "token": create_token,
                'username':user.username,
                "user_id": user.id
            }), 200
        else:
            return jsonify({
                "msg": "User not found"
            }), 404
    else:
        return jsonify({
            "msg": "Something is wrong, try again"
        }), 400


# Users profile
@app.route('/user', methods=['GET'])
@jwt_required()
def handle_all_users():

    users = User.query.all()
    if users is not None:
        users = list(map(
            lambda user : user.serialize(),
            users
        ))
        return jsonify(users), 200
    else:
        return jsonify({
            "msg": "Users not found"
        }), 404



@app.route('/user/<int:user_id>', methods=['GET', 'PUT'])
@jwt_required()
def handle_user(user_id = None):

    user_id = get_jwt_identity()

    if request.method == 'GET':

        if user_id is None:
            return jsonify({
                "msg": "User not found"
            }), 404
        else:
            user = User.query.filter_by(id = user_id).first()
            if user is not None:
                return jsonify(user.serialize()), 200
            else:
                return jsonify({
                "msg": "User not found"
            }), 404

    if request.method == 'PUT':

        body = request.json

        user_update = User.query.filter_by(id = user_id).first()

        if user_update is None:
            return jsonify({
                "msg": "User not found"
            }), 404
            
        try:
            user_update.email = body["email"]
            user_update.first_name = body["first_name"]
            user_update.last_name = body["last_name"]
            user_update.username = body["username"]
            db.session.commit()
            return jsonify(user_update.serialize()), 202
        except Exception as error:
            db.session.rollback()
            return jsonify(error.args)

# @socketIo.on("message")
# def handleMessage(msg):
#     user_id = request.args.get("user")
#     user = User.query.filter_by(id = user_id).first()
#     if user is not None:
#         try:
#             mensaje = Messages (
#             msg = msg,
#             username = user.username
#         )
#             db.session.add(mensaje)
#             db.session.commit()
#             send(msg, broadcast=True)
#         except Exception as error:
#             db.session.rollback()
#             return jsonify(error)
#     return None

user = {}

# @socketIo.on('login')
# def assing_sid(username):
#     user[username] = request.sid
#     print(user)

@socketIo.on('login')
def handle_connect(id):
    user_id = id

    if user_id is None:
        return print("NO EXISTE")
    else:
        user[id] = request.sid


# @socketIo.on('disconnect')
# @jwt_required()
# def handle_disconnect():
#     user_id = get_jwt_identity()
#     close_room(user_id)

@socketIo.on("private_message")
def handle_private(payload):
    user_to = User.query.filter_by(username = payload["username"]).first()
    user_from = User.query.filter_by(id = payload['id']).first()

    if user_to is not None and user_from is not None:
        user_to = user_to.serialize()
        user_from = user_from.serialize()

        user_to_id = str(user_to['id'])
        user_from_id = str(user_from['id'])

        user2 = user[user_to_id]
        msg = payload['msg']

        try:
            private_message = PrivateMessages (
                msg = msg,
                user_to = user_to_id,
                username_to = user_to['username'],
                user_from = user_from_id,
                username_from = user_from['username'],
                date = datetime.datetime.now()
            )
            db.session.add(private_message)
            db.session.commit()
            emit("new_private_msg", msg, room = user2)
        except Exception as error:
            db.session.rollback()
            return jsonify(error)
    else:
        return None

@socketIo.on("message")
def handleMessage(msg):
    user_id = request.args.get("user")
    user = User.query.filter_by(id = user_id).first()
    if user is not None:
        try:
            mensaje = Messages (
            msg = msg,
            username = user.username,
            date = datetime.datetime.now()
        )
            db.session.add(mensaje)
            db.session.commit()
            send(msg, broadcast=True)
        except Exception as error:
            db.session.rollback()
            return jsonify(error)
    return None

@app.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():

    if request.method == 'GET':
        messages = Messages.query.all()
        messages = list(map(
            lambda message : message.serialize(),
            messages
        ))
        return jsonify(messages),200
    else:
        return jsonify({
            "msg": "Not found messages in this chat room"
        }), 404 


@app.route('/private/<int:user_to>', methods=['GET'])
@jwt_required()
def get_private_messages(user_to = None):

    user_id = get_jwt_identity()

    if request.method == 'GET':
        if user_to is not None:
            
            messages = PrivateMessages.query.filter_by(user_from = user_id, user_to = user_to).all()
            messages = list(map(
                lambda message : message.serialize(),
                messages
            ))
            print(messages)
            return jsonify(messages)
        else:
            return jsonify({
                "msg": "U dont have messages here"
            }), 404

# @socketIo.on("create_channel")
# def handle_channel(payload):
#     user = payload["id"]
#     room = payload["name"]
#     try:
#         channel = Channels(
#             name = room,
#             user_id = user
#         )
#         db.session.add(channel)
#         db.session.commit()
#         # join_room(room)
#         return emit(user + "has entered the room", to = room)
#     except Exception as error:
#         db.session.rollback()
#         return jsonify(error)

@app.route('/createchannel', methods = ['POST'])
@jwt_required()
def handle_channel():
    user = get_jwt_identity()
    room = request.json.get("channel")
    try:
        channel = Channels(
            name = room,
            user_id = user
        )
        db.session.add(channel)
        db.session.commit()
        return jsonify({
            "msg": "channel created"
        }), 201
    except Exception as error:
        db.session.rollback()
        return jsonify(error), 500

@socketIo.on("join")
def handle_join(channel):
    user = request.sid
    join_room(user)

@socketIo.on("channel")
def handle_chat(payload):
    msg = payload["msg"]
    room = payload["channel"]
    emit("mensaje", msg, room = room, broadcast = True)

@app.route('/channels', methods = ['GET'])
@jwt_required()
def handle_channels():
    user = get_jwt_identity()
    user_channels = Channels.query.filter_by(user_id = user).all()
    if user_channels is not None:
        user_channels = list(map(lambda channels : channels.serialize(), user_channels))
        return jsonify(user_channels)
    else: 
        return jsonify(
            {"msg": "channel not found"}
    ), 404

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
