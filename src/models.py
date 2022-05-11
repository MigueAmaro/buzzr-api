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

    server = db.relationship("Server")
    server_id = db.Column(db.Integer, db.ForeignKey("server.id"))

    def __repr__(self):
        return '<Channel %r>' % self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "server": self.server_id
        }