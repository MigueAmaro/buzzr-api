from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(80), unique = False, nullable = False)
    first_name = db.Column(db.String(80), nullable = False)
    last_name = db.Column(db.String(80), nullable = False)
    username = db.Column(db.String(80), unique = True, nullable = False)
    

    def __repr__(self):
        return '<User %r>' % self.username

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username
        }

class Server(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    name = db.Column(db.String(80), nullable = False)

    user = db.relationship("User")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return '<Server %r>' % self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
        }

class Channels(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    
    name = db.Column(db.String(80), nullable = False)
    user_id = db.Column(db.Integer, nullable = False)


    def __repr__(self):
        return '<Channel %r>' % self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id
        }

class Messages(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    msg = db.Column(db.Text, nullable = False)
    username = db.Column(db.String(50))
    date = db.Column(db.DateTime, nullable=False)
    channel = db.relationship("Channels")
    channel_id = db.Column(db.Integer, db.ForeignKey("channels.id"))
    
    def __repr__(self):
        return '<Msg %r>' % self.msg

    def serialize(self):
        return {
            "id": self.id,
            "msg": self.msg,
            "username": self.username,
            "date": self.date
        }

class PrivateMessages(db.Model):
    id = db.Column(db.Integer, primary_key = True)

    msg = db.Column(db.Text, nullable = False)
    user_from = db.Column(db.String(1000), nullable=False)
    username_from = db.Column(db.String(80), nullable=False)
    user_to = db.Column(db.String(1000), nullable=False)
    username_to = db.Column(db.String(80), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return '<Msg %r>' % self.msg

    def serialize(self):
        return {
            "id": self.id,
            "msg": self.msg,
            "user_from": self.user_from,
            "username_from": self.username_from,
            "user_to": self.user_to,
            "username_to": self.username_from,
            "date": self.date
        }

class ToDo(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    task = db.Column(db.String(100), nullable=False)
    user = db.relationship('User')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return '<ToDo %r>'

    def serialize(self):
        return {
            'id': self.id,
            'task': self.task,
            'user_id': self.user_id
        }