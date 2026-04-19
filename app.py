import os
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Contact, Deal, Task, Note, STAGES, STAGE_LABELS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production')

database_url = os.environ.get('DATABASE_URL', 'sqlite:///crm.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def seed_users():
    if User.query.count() == 0:
        users = [
            User(
                name='Mattias Olsson',
                email='mattias@example.com',
                password_hash=generate_password_hash('changeme123'),
            ),
            User(
                name='Daniel Olsson',
                email='daniel@example.com',
                password_hash=generate_password_hash('changeme123'),
            ),
        ]
        db.session.add_all(users)
        db.session.commit()


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    total_contacts = Contact.query.count()
    active_deals = Deal.query.filter(Deal.stage.notin_(['won', 'lost'])).count()
    open_tasks = Task.query.filter_by(completed=False).count()
    won_deals = Deal.query.filter_by(stage='won').count()
    pipeline_value = (
        db.session.query(db.func.sum(Deal.value))
        .filter(Deal.stage.notin_(['won', 'lost']))
        .scalar() or 0
    )
    overdue_tasks = (
        Task.query
        .filter(Task.completed == False, Task.due_date < date.today())
        .order_by(Task.due_date)
        .all()
    )
    upcoming_tasks = (
        Task.query
        .filter(Task.completed == False, Task.due_date >= date.today())
        .order_by(Task.due_date)
        .limit(5)
        .all()
    )
    return render_template(
        'dashboard.html',
        total_contacts=total_contacts,
        active_deals=active_deals,
        open_tasks=open_tasks,
        won_deals=won_deals,
        pipeline_value=pipeline_value,
        overdue_tasks=overdue_tasks,
        upcoming_tasks=upcoming_tasks,
        today=date.today(),
    )


# ── Contacts ──────────────────────────────────────────────────────────────────

@app.route('/contacts')
@login_required
def contacts():
    q = request.args.get('q', '').strip()
    query = Contact.query
    if q:
        query = query.filter(
            db.or_(
                Contact.name.ilike(f'%{q}%'),
                Contact.email.ilike(f'%{q}%'),
                Contact.company.ilike(f'%{q}%'),
            )
        )
    all_contacts = query.order_by(Contact.created_at.desc()).all()
    return render_template('contacts.html', contacts=all_contacts, q=q)


@app.route('/contacts/new', methods=['GET', 'POST'])
@login_required
def new_contact():
    if request.method == 'POST':
        contact = Contact(
            name=request.form['name'],
            email=request.form.get('email') or None,
            phone=request.form.get('phone') or None,
            company=request.form.get('company') or None,
            notes=request.form.get('notes') or None,
        )
        db.session.add(contact)
        db.session.commit()
        flash('Contact added.')
        return redirect(url_for('contact_detail', contact_id=contact.id))
    return render_template('contact_form.html', contact=None)


@app.route('/contacts/<int:contact_id>')
@login_required
def contact_detail(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    users = User.query.all()
    return render_template(
        'contact_detail.html',
        contact=contact,
        users=users,
        STAGE_LABELS=STAGE_LABELS,
        STAGES=STAGES,
    )


@app.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if request.method == 'POST':
        contact.name = request.form['name']
        contact.email = request.form.get('email') or None
        contact.phone = request.form.get('phone') or None
        contact.company = request.form.get('company') or None
        contact.notes = request.form.get('notes') or None
        db.session.commit()
        flash('Contact updated.')
        return redirect(url_for('contact_detail', contact_id=contact.id))
    return render_template('contact_form.html', contact=contact)


@app.route('/contacts/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact deleted.')
    return redirect(url_for('contacts'))


@app.route('/contacts/<int:contact_id>/notes', methods=['POST'])
@login_required
def add_note(contact_id):
    Contact.query.get_or_404(contact_id)
    note = Note(
        content=request.form['content'],
        contact_id=contact_id,
        created_by_id=current_user.id,
    )
    db.session.add(note)
    db.session.commit()
    return redirect(url_for('contact_detail', contact_id=contact_id))


# ── Deals / Pipeline ──────────────────────────────────────────────────────────

@app.route('/deals')
@login_required
def deals():
    users = User.query.all()
    contacts_list = Contact.query.order_by(Contact.name).all()
    pipeline = {stage: Deal.query.filter_by(stage=stage).order_by(Deal.updated_at.desc()).all() for stage in STAGES}
    return render_template(
        'deals.html',
        pipeline=pipeline,
        STAGES=STAGES,
        STAGE_LABELS=STAGE_LABELS,
        users=users,
        contacts=contacts_list,
    )


@app.route('/deals/new', methods=['POST'])
@login_required
def new_deal():
    raw_value = request.form.get('value', '').strip()
    deal = Deal(
        title=request.form['title'],
        contact_id=int(request.form['contact_id']),
        stage=request.form.get('stage', 'new_lead'),
        value=float(raw_value) if raw_value else None,
        notes=request.form.get('notes') or None,
        assigned_to_id=request.form.get('assigned_to_id') or None,
    )
    db.session.add(deal)
    db.session.commit()
    flash('Deal added.')
    return redirect(url_for('deals'))


@app.route('/deals/<int:deal_id>/move', methods=['POST'])
@login_required
def move_deal(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    stage = request.json.get('stage')
    if stage in STAGES:
        deal.stage = stage
        deal.updated_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'ok': True, 'stage': deal.stage})


@app.route('/deals/<int:deal_id>/delete', methods=['POST'])
@login_required
def delete_deal(deal_id):
    deal = Deal.query.get_or_404(deal_id)
    db.session.delete(deal)
    db.session.commit()
    return jsonify({'ok': True})


# ── Tasks ─────────────────────────────────────────────────────────────────────

@app.route('/tasks')
@login_required
def tasks():
    filter_by = request.args.get('filter', 'open')
    users = User.query.all()
    contacts_list = Contact.query.order_by(Contact.name).all()
    query = Task.query
    if filter_by == 'open':
        query = query.filter_by(completed=False)
    elif filter_by == 'mine':
        query = query.filter_by(completed=False, assigned_to_id=current_user.id)
    elif filter_by == 'done':
        query = query.filter_by(completed=True)
    all_tasks = query.order_by(Task.due_date.asc().nullslast()).all()
    return render_template(
        'tasks.html',
        tasks=all_tasks,
        filter_by=filter_by,
        users=users,
        contacts=contacts_list,
        today=date.today(),
    )


@app.route('/tasks/new', methods=['POST'])
@login_required
def new_task():
    raw_date = request.form.get('due_date', '').strip()
    task = Task(
        title=request.form['title'],
        description=request.form.get('description') or None,
        due_date=datetime.strptime(raw_date, '%Y-%m-%d').date() if raw_date else None,
        assigned_to_id=request.form.get('assigned_to_id') or current_user.id,
        contact_id=request.form.get('contact_id') or None,
    )
    db.session.add(task)
    db.session.commit()
    flash('Task added.')
    return redirect(url_for('tasks'))


@app.route('/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    return jsonify({'ok': True, 'completed': task.completed})


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'ok': True})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_users()
    from scheduler import start_scheduler
    start_scheduler(app)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
