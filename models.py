from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

STAGES = ['new_lead', 'meeting_booked', 'proposal_sent', 'won', 'lost']
STAGE_LABELS = {
    'new_lead': 'New Lead',
    'meeting_booked': 'Meeting Booked',
    'proposal_sent': 'Proposal Sent',
    'won': 'Won',
    'lost': 'Lost',
}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    company = db.Column(db.String(100))
    notes = db.Column(db.Text)
    monthly_fee = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    deals = db.relationship('Deal', backref='contact', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='contact', lazy=True)
    note_entries = db.relationship('Note', backref='contact', lazy=True, cascade='all, delete-orphan')


class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=False)
    stage = db.Column(db.String(30), default='new_lead')
    value = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id])
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    completed = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'))
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


COST_CATEGORIES = ['Salary', 'Software', 'Office', 'Marketing', 'Other']


class Cost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default='Other')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
