from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models.task import Task
from models.performance import Performance
from models.user import User
from models.notification import Notification
from app import db, socketio
from datetime import datetime, date, timedelta

task_bp = Blueprint('task', __name__)

@task_bp.route('/tasks')
@login_required
def tasks():
    """Task board page"""
    status_filter = request.args.get('status', 'all')
    priority_filter = request.args.get('priority', 'all')
    
    query = Task.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
    
    tasks = query.order_by(Task.due_date.asc()).all()
    
    # Group tasks by status
    tasks_by_status = {
        'todo': [t for t in tasks if t.status == 'todo'],
        'in_progress': [t for t in tasks if t.status == 'in_progress'],
        'completed': [t for t in tasks if t.status == 'completed'],
        'overdue': [t for t in tasks if t.is_overdue()]
    }
    
    # Get all users for displaying assigned_by information
    users = User.query.all()
    
    return render_template('dashboard/tasks.html', 
                         tasks_by_status=tasks_by_status,
                         users=users,
                         current_status=status_filter,
                         current_priority=priority_filter)

@task_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new task"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        priority = request.form.get('priority')
        due_date_str = request.form.get('due_date')
        
        if not title:
            flash('Title is required', 'error')
            return render_template('tasks/create.html')
        
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid due date format', 'error')
                return render_template('tasks/create.html')
        
        task = Task(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority or 'medium',
            due_date=due_date
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task created successfully', 'success')
        return redirect(url_for('tasks.index'))
    
    return render_template('tasks/create.html')

@task_bp.route('/<int:task_id>')
@login_required
def view(task_id):
    """View task details"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    return render_template('tasks/view.html', task=task)

@task_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    """Edit task"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.priority = request.form.get('priority')
        
        due_date_str = request.form.get('due_date')
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid due date format', 'error')
                return render_template('tasks/edit.html', task=task)
        else:
            task.due_date = None
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash('Task updated successfully', 'success')
        return redirect(url_for('tasks.view', task_id=task.id))
    
    return render_template('tasks/edit.html', task=task)

@task_bp.route('/<int:task_id>/update_status', methods=['POST'])
@login_required
def update_status(task_id):
    """Update task status"""
    try:
        task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
        new_status = request.json.get('status')
        
        if new_status not in ['todo', 'in_progress', 'completed']:
            return jsonify({'success': False, 'message': 'Invalid status'})
        
        old_status = task.status
        task.status = new_status
        
        # If task is marked as completed, set completed_at timestamp
        if new_status == 'completed' and not task.completed_at:
            task.completed_at = datetime.now()
            
            # Create notification for admin
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                notification = Notification(
                    user_id=admin.id,
                    title='Task Completed',
                    message=f"Task '{task.title}' has been completed by {current_user.username}",
                    type="task_update",
                    icon='check-circle'
                )
                db.session.add(notification)
        
        # If task is marked as in_progress, record start time
        if new_status == 'in_progress' and old_status != 'in_progress':
            task.started_at = datetime.now()
            
            # Create notification for admin
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                notification = Notification(
                    user_id=admin.id,
                    title='Task Started',
                    message=f"Task '{task.title}' has been started by {current_user.username}",
                    type="task_update",
                    icon='play-circle'
                )
                db.session.add(notification)
        
        db.session.commit()
        
        # Update performance metrics
        update_performance_metrics(current_user.id)
        
        # Send real-time notification to admins
        try:
            admin_users = User.query.filter_by(is_admin=True).all()
            for admin in admin_users:
                socketio.emit('notification', {
                    'title': 'Task Status Update',
                    'message': f"Task '{task.title}' status changed from {old_status} to {new_status} by {current_user.username}",
                    'type': 'task_update'
                }, room=f"user_{admin.id}")
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
        
        return jsonify({
            'success': True, 
            'message': f'Task status updated from {old_status} to {new_status}',
            'new_status': new_status
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error updating task status: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to update task status: {str(e)}'}), 500

@task_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    """Delete task"""
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(task)
    db.session.commit()
    
    flash('Task deleted successfully', 'success')
    return redirect(url_for('tasks.index'))

@task_bp.route('/api/tasks')
@login_required
def api_tasks():
    """API endpoint for tasks data"""
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    
    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'is_overdue': task.is_overdue(),
            'days_until_due': task.get_days_until_due()
        })
    
    return jsonify(tasks_data)

def update_performance_metrics(user_id):
    """Update performance metrics for a user"""
    today = date.today()
    performance = Performance.query.filter_by(user_id=user_id, date=today).first()
    
    if not performance:
        performance = Performance(user_id=user_id, date=today)
        db.session.add(performance)
    
    # Calculate task completion score
    total_tasks = Task.query.filter_by(user_id=user_id).count()
    completed_tasks = Task.query.filter_by(user_id=user_id, status='completed').count()
    overdue_tasks = Task.query.filter_by(user_id=user_id).filter(Task.status != 'completed').all()
    overdue_count = len([t for t in overdue_tasks if t.is_overdue()])
    
    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
        overdue_penalty = (overdue_count / total_tasks) * 20  # 20% penalty per overdue task
        task_score = max(0, completion_rate - overdue_penalty)
    else:
        task_score = 100  # No tasks means perfect score
    
    # Calculate activity score (simplified - based on recent activity)
    from models.log import Log
    recent_logs = Log.query.filter(
        Log.user_id == user_id,
        Log.timestamp >= datetime.utcnow() - timedelta(hours=8)
    ).count()
    
    activity_score = min(100, recent_logs * 10)  # 10 points per activity in last 8 hours
    
    # Calculate punctuality score (simplified - based on login time)
    from config import Config
    work_start = datetime.utcnow().replace(hour=Config.WORK_HOURS_START, minute=0, second=0, microsecond=0)
    work_end = datetime.utcnow().replace(hour=Config.WORK_HOURS_END, minute=0, second=0, microsecond=0)
    
    today_login = Log.query.filter(
        Log.user_id == user_id,
        Log.action == 'login',
        Log.timestamp >= work_start,
        Log.timestamp <= work_end
    ).first()
    
    if today_login:
        punctuality_score = 100  # Logged in during work hours
    else:
        punctuality_score = 50  # Partial credit for logging in
    
    # Update performance
    performance.update_scores(
        task_score=task_score,
        activity_score=activity_score,
        punctuality_score=punctuality_score
    )
    
    performance.tasks_completed = completed_tasks
    performance.tasks_overdue = overdue_count
    performance.total_work_hours = current_user.get_total_work_hours_today()
    
    db.session.commit()
