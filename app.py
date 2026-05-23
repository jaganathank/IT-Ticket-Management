import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from database.models import (
    init_db,
    get_user,
    get_user_by_id,
    create_ticket,
    fetch_tickets_for_employee,
    fetch_all_tickets,
    get_ticket,
    get_ticket_comments,
    get_ticket_activities,
    add_comment,
    update_ticket_status,
    assign_ticket,
    add_resolution_notes,
    ticket_stats_for_employee,
    dashboard_metrics,
)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

init_db()

ROLE_ROUTES = {
    'employee': 'employee_dashboard',
    'it': 'it_dashboard',
}

STATUS_OPTIONS = ['Open', 'In Progress', 'Pending', 'Resolved', 'Closed']
CATEGORIES = ['Hardware', 'Software', 'Network', 'Access', 'Other']
PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
SEVERITIES = ['Minor', 'Major', 'Critical']


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_user_by_id(user_id)


def login_required(role=None):
    def wrapper(fn):
        def decorated_view(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('login'))
            if role and g.user['role'] != role:
                flash('Access denied for your role.', 'warning')
                return redirect(url_for(ROLE_ROUTES[g.user['role']]))
            return fn(*args, **kwargs)

        decorated_view.__name__ = fn.__name__
        return decorated_view

    return wrapper


@app.route('/')
def root():
    if g.user:
        return redirect(url_for(ROLE_ROUTES[g.user['role']]))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = get_user(username, password)
        if user:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for(ROLE_ROUTES[user['role']]))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/employee/dashboard')
@login_required('employee')
def employee_dashboard():
    filters = {
        'category': request.args.get('category'),
        'status': request.args.get('status'),
        'priority': request.args.get('priority'),
        'severity': request.args.get('severity'),
    }
    tickets = fetch_tickets_for_employee(g.user['id'], filters)
    stats = ticket_stats_for_employee(g.user['id'])
    return render_template(
        'employee_dashboard.html',
        user=g.user,
        tickets=tickets,
        stats=stats,
        categories=CATEGORIES,
        priorities=PRIORITIES,
        severities=SEVERITIES,
        status_options=STATUS_OPTIONS,
        filters=filters,
    )


@app.route('/employee/raise', methods=['GET', 'POST'])
@login_required('employee')
def raise_ticket():
    if request.method == 'POST':
        title = request.form['title'].strip()
        category = request.form['category']
        priority = request.form['priority']
        severity = request.form['severity']
        description = request.form['description'].strip()
        if not title or not description:
            flash('Please complete the ticket title and description.', 'warning')
        else:
            ticket_id = create_ticket(title, category, priority, severity, description, g.user['id'])
            flash('Ticket submitted successfully.', 'success')
            return redirect(url_for('ticket_details', ticket_id=ticket_id))
    return render_template(
        'raise_ticket.html',
        user=g.user,
        categories=CATEGORIES,
        priorities=PRIORITIES,
        severities=SEVERITIES,
    )


@app.route('/employee/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required('employee')
def ticket_details(ticket_id):
    ticket = get_ticket(ticket_id)
    if ticket is None or ticket['employee_id'] != g.user['id']:
        flash('Ticket not found or access denied.', 'danger')
        return redirect(url_for('employee_dashboard'))

    if request.method == 'POST':
        comment_text = request.form['comment'].strip()
        if comment_text:
            add_comment(ticket_id, g.user['id'], comment_text)
            flash('Comment added successfully.', 'success')
        return redirect(url_for('ticket_details', ticket_id=ticket_id))

    comments = get_ticket_comments(ticket_id)
    activities = get_ticket_activities(ticket_id)
    assignee = get_user_by_id(ticket['assigned_to']) if ticket['assigned_to'] else None
    return render_template(
        'ticket_details.html',
        user=g.user,
        ticket=ticket,
        comments=comments,
        activities=activities,
        assignee=assignee,
        status_options=STATUS_OPTIONS,
        categories=CATEGORIES,
        priorities=PRIORITIES,
        severities=SEVERITIES,
    )


@app.route('/it/dashboard')
@login_required('it')
def it_dashboard():
    metrics = dashboard_metrics()
    open_count = metrics['status'].get('Open', 0)
    critical_count = metrics['critical']
    overdue_count = 0
    total = sum(metrics['status'].values())
    return render_template(
        'it_dashboard.html',
        user=g.user,
        metrics=metrics,
        total=total,
        open_count=open_count,
        critical_count=critical_count,
        overdue_count=overdue_count,
        categories=CATEGORIES,
    )


@app.route('/it/manage')
@login_required('it')
def manage_tickets():
    filters = {
        'category': request.args.get('category'),
        'status': request.args.get('status'),
        'priority': request.args.get('priority'),
        'severity': request.args.get('severity'),
        'assigned_to': request.args.get('assigned_to') or None,
    }
    tickets = fetch_all_tickets(filters)
    technicians = get_all_it_members()
    return render_template(
        'manage_tickets.html',
        user=g.user,
        tickets=tickets,
        filters=filters,
        categories=CATEGORIES,
        priorities=PRIORITIES,
        severities=SEVERITIES,
        status_options=STATUS_OPTIONS,
        technicians=technicians,
    )


def get_all_it_members():
    from database.models import query_db
    return query_db('SELECT id, fullname FROM users WHERE role = ?', ('it',))


@app.route('/it/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required('it')
def it_ticket_detail(ticket_id):
    ticket = get_ticket(ticket_id)
    if ticket is None:
        flash('Ticket not found.', 'danger')
        return redirect(url_for('manage_tickets'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'assign':
            assignee = request.form.get('assigned_to')
            assign_ticket(ticket_id, int(assignee) if assignee else None, g.user['id'])
            flash('Ticket assignment updated.', 'success')
        elif action == 'status':
            status_value = request.form.get('status')
            update_ticket_status(ticket_id, status_value, g.user['id'])
            flash('Ticket status updated.', 'success')
        elif action == 'resolution':
            notes = request.form.get('resolution_notes').strip()
            add_resolution_notes(ticket_id, notes, g.user['id'])
            flash('Resolution notes saved.', 'success')
        elif action == 'comment':
            comment_text = request.form.get('comment').strip()
            if comment_text:
                add_comment(ticket_id, g.user['id'], comment_text)
                flash('Comment added.', 'success')
        return redirect(url_for('it_ticket_detail', ticket_id=ticket_id))

    comments = get_ticket_comments(ticket_id)
    activities = get_ticket_activities(ticket_id)
    assignee = get_user_by_id(ticket['assigned_to']) if ticket['assigned_to'] else None
    technicians = get_all_it_members()
    return render_template(
        'ticket_details.html',
        user=g.user,
        ticket=ticket,
        comments=comments,
        activities=activities,
        assignee=assignee,
        technicians=technicians,
        status_options=STATUS_OPTIONS,
        categories=CATEGORIES,
        priorities=PRIORITIES,
        severities=SEVERITIES,
    )


if __name__ == '__main__':
    app.run(debug=True)
