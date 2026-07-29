from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Shoe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model_name = db.Column(db.String(100), nullable=False) 
    max_mileage = db.Column(db.Float, default=500.0)
    current_mileage = db.Column(db.Float, default=0.0)
    
    activities = db.relationship('Activity', backref='shoe', lazy=True)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    duration_minutes = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    shoe_id = db.Column(db.Integer, db.ForeignKey('shoe.id'), nullable=True)