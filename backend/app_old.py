from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Habit, HabitLog
from datetime import datetime, timedelta
import bcrypt
import os

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/habit_tracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize extensions
CORS(app, supports_credentials=True)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

# ============= HELPER FUNCTIONS =============

def calculate_streak(habit_id):
    """Calculate current and longest streaks"""
    logs = HabitLog.query.filter_by(habit_id=habit_id).order_by(HabitLog.completed_date.desc()).all()
    
    if not logs:
        return 0, 0
    
    # Current streak
    current_streak = 0
    today = datetime.now().date()
    expected_date = today
    
    for log in logs:
        log_date = log.completed_date.date() if isinstance(log.completed_date, datetime) else log.completed_date
        if log_date == expected_date:
            current_streak += 1
            expected_date -= timedelta(days=1)
        elif log_date < expected_date:
            break
    
    # Longest streak
    longest_streak = 0
    temp_streak = 0
    prev_date = None
    
    for log in reversed(logs):
        log_date = log.completed_date.date() if isinstance(log.completed_date, datetime) else log.completed_date
        if prev_date is None:
            temp_streak = 1
        elif (log_date - prev_date).days == 1:
            temp_streak += 1
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 1
        prev_date = log_date
    
    longest_streak = max(longest_streak, temp_streak)
    return current_streak, longest_streak

# ============= STATIC ROUTES =============

@app.route('/')
def index():
    if current_user.is_authenticated:
        return app.send_static_file('index.html')
    return redirect('/auth.html')

@app.route('/auth.html')
def login_page():
    if current_user.is_authenticated:
        return redirect('/')
    return app.send_static_file('auth.html')

# ============= AUTH ROUTES =============

@app.route('/api/register', methods=['POST'])
def register():
    """Register new user"""
    try:
        data = request.get_json()
        
        # Validation
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check existing user
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Login user
        login_user(new_user, remember=True)
        
        return jsonify({
            'message': 'Registration successful!',
            'user': {
                'id': new_user.id,
                'username': new_user.username,
                'email': new_user.email
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user with username or email"""
    try:
        data = request.get_json()
        
        login_input = data.get('login', '').strip()  # Can be username or email
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not login_input or not password:
            return jsonify({'error': 'Login and password are required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Login user
        login_user(user, remember=remember)
        
        return jsonify({
            'message': 'Login successful!',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """Logout current user"""
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/user', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged in user"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email
    }), 200

# ============= HABIT ROUTES =============

@app.route('/api/habits', methods=['GET'])
@login_required
def get_habits():
    """Get all habits for current user"""
    try:
        habits = Habit.query.filter_by(user_id=current_user.id).all()
        result = []
        
        for habit in habits:
            current_streak, longest_streak = calculate_streak(habit.id)
            result.append({
                'id': habit.id,
                'name': habit.name,
                'description': habit.description,
                'created_at': habit.created_at.isoformat(),
                'current_streak': current_streak,
                'longest_streak': longest_streak
            })
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/habits', methods=['POST'])
@login_required
def create_habit():
    """Create new habit"""
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Habit name is required'}), 400
        
        new_habit = Habit(
            name=data['name'],
            description=data.get('description', ''),
            user_id=current_user.id
        )
        
        db.session.add(new_habit)
        db.session.commit()
        
        return jsonify({
            'id': new_habit.id,
            'name': new_habit.name,
            'description': new_habit.description,
            'created_at': new_habit.created_at.isoformat(),
            'current_streak': 0,
            'longest_streak': 0
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/habits/<int:habit_id>', methods=['DELETE'])
@login_required
def delete_habit(habit_id):
    """Delete habit"""
    try:
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        
        if not habit:
            return jsonify({'error': 'Habit not found'}), 404
        
        HabitLog.query.filter_by(habit_id=habit_id).delete()
        db.session.delete(habit)
        db.session.commit()
        
        return jsonify({'message': 'Habit deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/habits/<int:habit_id>/complete', methods=['POST'])
@login_required
def complete_habit(habit_id):
    """Mark habit as completed"""
    try:
        habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first()
        
        if not habit:
            return jsonify({'error': 'Habit not found'}), 404
        
        today = datetime.now().date()
        
        existing_log = HabitLog.query.filter_by(
            habit_id=habit_id,
            completed_date=today
        ).first()
        
        if existing_log:
            return jsonify({'error': 'Habit already completed today'}), 400
        
        new_log = HabitLog(
            habit_id=habit_id,
            completed_date=today
        )
        
        db.session.add(new_log)
        db.session.commit()
        
        current_streak, longest_streak = calculate_streak(habit_id)
        
        return jsonify({
            'message': 'Habit completed!',
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics():
    """Get analytics for current user"""
    try:
        habits = Habit.query.filter_by(user_id=current_user.id).all()
        
        total_habits = len(habits)
        overall_longest_streak = 0
        
        for habit in habits:
            _, longest_streak = calculate_streak(habit.id)
            overall_longest_streak = max(overall_longest_streak, longest_streak)
        
        # Analytics calculations
        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        recent_logs = HabitLog.query.join(Habit).filter(
            Habit.user_id == current_user.id,
            HabitLog.completed_date >= thirty_days_ago
        ).all()
        
        expected_completions = total_habits * 30
        actual_completions = len(recent_logs)
        completion_percentage = (actual_completions / expected_completions * 100) if expected_completions > 0 else 0
        consistency_score = min(100, completion_percentage * 1.2)
        
        # Weekly data
        weekly_data = {}
        for i in range(7):
            date = datetime.now().date() - timedelta(days=i)
            count = HabitLog.query.join(Habit).filter(
                Habit.user_id == current_user.id,
                HabitLog.completed_date == date
            ).count()
            weekly_data[date.strftime('%a')] = count
        
        # Streak growth
        streak_data = {}
        for i in range(30, -1, -1):
            date = datetime.now().date() - timedelta(days=i)
            count = HabitLog.query.join(Habit).filter(
                Habit.user_id == current_user.id,
                HabitLog.completed_date == date
            ).count()
            streak_data[date.strftime('%m/%d')] = count
        
        # Heatmap
        heatmap_data = []
        for i in range(90):
            date = datetime.now().date() - timedelta(days=i)
            count = HabitLog.query.join(Habit).filter(
                Habit.user_id == current_user.id,
                HabitLog.completed_date == date
            ).count()
            heatmap_data.append({
                'date': date.isoformat(),
                'count': count
            })
        
        completed = len(recent_logs)
        missed = expected_completions - completed
        
        return jsonify({
            'dashboard': {
                'total_habits': total_habits,
                'longest_streak': overall_longest_streak,
                'completion_percentage': round(completion_percentage, 1),
                'consistency_score': round(consistency_score, 1)
            },
            'charts': {
                'weekly_completion': weekly_data,
                'streak_growth': streak_data,
                'completed_vs_missed': {
                    'completed': completed,
                    'missed': max(0, missed)
                },
                'heatmap': heatmap_data
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
