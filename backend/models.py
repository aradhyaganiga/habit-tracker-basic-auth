from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model with Flask-Login support"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    habits = db.relationship('Habit', backref='user', cascade='all, delete-orphan', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Habit(db.Model):
    """Habit model"""
    __tablename__ = 'habits'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship
    logs = db.relationship('HabitLog', backref='habit', cascade='all, delete-orphan', lazy=True)
    
    def __repr__(self):
        return f'<Habit {self.name}>'

class HabitLog(db.Model):
    """Daily completion logs"""
    __tablename__ = 'habit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    completed_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('habit_id', 'completed_date', name='unique_habit_date'),
    )
    
    def __repr__(self):
        return f'<HabitLog {self.habit_id} on {self.completed_date}>'
