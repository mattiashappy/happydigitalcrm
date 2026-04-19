import os
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def _send_reminder(to_email, to_name, tasks):
    api_key = os.environ.get('SENDGRID_API_KEY')
    from_email = os.environ.get('FROM_EMAIL', 'noreply@example.com')
    if not api_key:
        return
    lines = '\n'.join(f"  • {t.title} (due {t.due_date})" for t in tasks)
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject='Tasks due today',
        plain_text_content=(
            f"Hi {to_name},\n\n"
            f"You have {len(tasks)} task(s) due today or overdue:\n\n"
            f"{lines}\n\n"
            f"Log in to mark them done."
        ),
    )
    try:
        SendGridAPIClient(api_key).send(message)
    except Exception as e:
        print(f"[scheduler] SendGrid error: {e}")


def _check_tasks(app):
    with app.app_context():
        from models import db, Task, User
        today = date.today()
        for user in User.query.all():
            due = (
                Task.query
                .filter(
                    Task.assigned_to_id == user.id,
                    Task.completed == False,
                    Task.due_date <= today,
                    Task.reminder_sent == False,
                )
                .all()
            )
            if due:
                _send_reminder(user.email, user.name, due)
                for task in due:
                    task.reminder_sent = True
                db.session.commit()


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: _check_tasks(app), 'cron', hour=8, minute=0)
    scheduler.start()
