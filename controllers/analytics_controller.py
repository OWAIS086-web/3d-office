from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.performance import Performance
from models.task import Task
from models.log import Log
from models.user import User
from app import db
from datetime import datetime, date, timedelta
from sqlalchemy import func, case

analytics_bp = Blueprint('analytics', __name__)

# ------------------------------
# Dashboard Overview
# ------------------------------
@analytics_bp.route('/')
@login_required
def index():
    days = int(request.args.get('days', 30))
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)

    # Performance data
    performance_data = Performance.query.filter(
        Performance.user_id == current_user.id,
        Performance.date >= start_date
    ).order_by(Performance.date).all()

    # Task stats
    total_tasks = Task.query.filter_by(user_id=current_user.id).count()
    completed_tasks = Task.query.filter_by(user_id=current_user.id, status='completed').count()

    # Overdue tasks
    overdue_tasks = Task.query.filter_by(user_id=current_user.id).filter(
        Task.status != 'completed'
    ).all()
    overdue_tasks = len([t for t in overdue_tasks if hasattr(t, "is_overdue") and t.is_overdue()])

    # Work hours
    work_hours_data = Performance.query.filter(
        Performance.user_id == current_user.id,
        Performance.date >= start_date
    ).with_entities(Performance.date, Performance.total_work_hours).all()

    return render_template('analytics/index.html',
        performance_data=performance_data,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        work_hours_data=work_hours_data,
        days=days
    )

# ------------------------------
# Performance Analytics
# ------------------------------
@analytics_bp.route('/performance')
@login_required
def performance():
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    performance_data = Performance.query.filter(
        Performance.user_id == current_user.id,
        Performance.date >= start_date,
        Performance.date <= end_date
    ).order_by(Performance.date.desc()).all()

    if performance_data:
        avg_overall = sum(p.overall_score for p in performance_data) / len(performance_data)
        avg_task_score = sum(p.task_completion_score for p in performance_data) / len(performance_data)
        avg_activity_score = sum(p.activity_score for p in performance_data) / len(performance_data)
        avg_punctuality_score = sum(p.punctuality_score for p in performance_data) / len(performance_data)
        total_work_hours = sum(p.total_work_hours for p in performance_data)
    else:
        avg_overall = avg_task_score = avg_activity_score = avg_punctuality_score = total_work_hours = 0

    return render_template('analytics/performance.html',
        performance_data=performance_data,
        avg_overall=round(avg_overall, 2),
        avg_task_score=round(avg_task_score, 2),
        avg_activity_score=round(avg_activity_score, 2),
        avg_punctuality_score=round(avg_punctuality_score, 2),
        total_work_hours=round(total_work_hours, 2),
        days=days
    )

# ------------------------------
# Task Analytics
# ------------------------------
@analytics_bp.route('/tasks')
@login_required
def tasks():
    # Task stats by status
    task_stats = db.session.query(
        Task.status,
        func.count(Task.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(Task.status).all()

    # Task stats by priority
    priority_stats = db.session.query(
        Task.priority,
        func.count(Task.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(Task.priority).all()

    # Completion rate over time
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    completion_data = db.session.query(
        func.date(Task.created_at).label('date'),
        func.count(Task.id).label('total_tasks'),
        func.sum(case((Task.status == 'completed', 1), else_=0)).label('completed_tasks')
    ).filter(
        Task.user_id == current_user.id,
        Task.created_at >= start_date
    ).group_by(func.date(Task.created_at)).order_by(func.date(Task.created_at)).all()

    return render_template('analytics/tasks.html',
        task_stats=task_stats,
        priority_stats=priority_stats,
        completion_data=completion_data,
        days=days
    )

# ------------------------------
# API - Performance Chart
# ------------------------------
@analytics_bp.route('/api/performance_chart')
@login_required
def api_performance_chart():
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    performance_data = Performance.query.filter(
        Performance.user_id == current_user.id,
        Performance.date >= start_date,
        Performance.date <= end_date
    ).order_by(Performance.date).all()

    chart_data = [{
        'date': p.date.strftime('%Y-%m-%d'),
        'overall_score': p.overall_score,
        'task_score': p.task_completion_score,
        'activity_score': p.activity_score,
        'punctuality_score': p.punctuality_score,
        'work_hours': p.total_work_hours
    } for p in performance_data]

    return jsonify(chart_data)

# ------------------------------
# API - Task Completion Chart
# ------------------------------
@analytics_bp.route('/api/task_completion_chart')
@login_required
def api_task_completion_chart():
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    completion_data = db.session.query(
        func.date(Task.created_at).label('date'),
        func.count(Task.id).label('total_tasks'),
        func.sum(case((Task.status == 'completed', 1), else_=0)).label('completed_tasks')
    ).filter(
        Task.user_id == current_user.id,
        Task.created_at >= start_date
    ).group_by(func.date(Task.created_at)).order_by(func.date(Task.created_at)).all()

    chart_data = []
    for d in completion_data:
        completion_rate = (d.completed_tasks / d.total_tasks * 100) if d.total_tasks > 0 else 0
        chart_data.append({
            'date': d.date.strftime('%Y-%m-%d'),
            'total_tasks': d.total_tasks,
            'completed_tasks': d.completed_tasks,
            'completion_rate': round(completion_rate, 2)
        })

    return jsonify(chart_data)

# ------------------------------
# API - Work Hours Chart
# ------------------------------
@analytics_bp.route('/api/work_hours_chart')
@login_required
def api_work_hours_chart():
    days = request.args.get('days', 30, type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    work_hours_data = db.session.query(
        Performance.date,
        func.avg(Performance.total_work_hours).label('avg_hours')
    ).filter(
        Performance.user_id == current_user.id,
        Performance.date >= start_date,
        Performance.date <= end_date
    ).group_by(Performance.date).order_by(Performance.date).all()

    chart_data = [{
        'date': d.date.strftime('%Y-%m-%d'),
        'hours': round(float(d.avg_hours or 0), 2)
    } for d in work_hours_data]

    return jsonify(chart_data)
