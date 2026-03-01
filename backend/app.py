from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
from models import db, User, Habit, HabitLog
from datetime import datetime, timedelta
import bcrypt

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-12345678901234567890'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:#Aradhya007@localhost/habit_tracker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize
CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

# Basic Auth Decorator
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        
        if not auth or not auth.username or not auth.password:
            return jsonify({'error': 'Authentication required'}), 401
        
        user = User.query.filter(
            (User.username == auth.username) | (User.email == auth.username)
        ).first()
        
        if not user or not bcrypt.checkpw(auth.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        return f(user, *args, **kwargs)
    return decorated

# Helper
def calculate_streak(habit_id):
    logs = HabitLog.query.filter_by(habit_id=habit_id).order_by(HabitLog.completed_date.desc()).all()
    if not logs:
        return 0, 0
    
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

# Routes
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/auth.html')
def auth_page():
    return app.send_static_file('auth.html')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'All fields required'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = User(username=username, email=email, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'Registration successful! Please login.',
        'user': {'id': new_user.id, 'username': new_user.username}
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    login_input = data.get('login', '').strip()
    password = data.get('password', '')
    
    user = User.query.filter((User.username == login_input) | (User.email == login_input)).first()
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    return jsonify({
        'message': 'Login successful!',
        'user': {'id': user.id, 'username': user.username, 'email': user.email}
    }), 200

@app.route('/api/user', methods=['GET'])
@require_auth
def get_user(user):
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email}), 200

@app.route('/api/habits', methods=['GET'])
@require_auth
def get_habits(user):
    habits = Habit.query.filter_by(user_id=user.id).all()
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

@app.route('/api/habits', methods=['POST'])
@require_auth
def create_habit(user):
    data = request.get_json()
    if not data.get('name'):
        return jsonify({'error': 'Habit name required'}), 400
    
    new_habit = Habit(name=data['name'], description=data.get('description', ''), user_id=user.id)
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

@app.route('/api/habits/<int:habit_id>', methods=['DELETE'])
@require_auth
def delete_habit(user, habit_id):
    habit = Habit.query.filter_by(id=habit_id, user_id=user.id).first()
    if not habit:
        return jsonify({'error': 'Habit not found'}), 404
    
    db.session.delete(habit)
    db.session.commit()
    return jsonify({'message': 'Habit deleted'}), 200

@app.route('/api/habits/<int:habit_id>/complete', methods=['POST'])
@require_auth
def complete_habit(user, habit_id):
    habit = Habit.query.filter_by(id=habit_id, user_id=user.id).first()
    if not habit:
        return jsonify({'error': 'Habit not found'}), 404
    
    today = datetime.now().date()
    if HabitLog.query.filter_by(habit_id=habit_id, completed_date=today).first():
        return jsonify({'error': 'Already completed today'}), 400
    
    new_log = HabitLog(habit_id=habit_id, completed_date=today)
    db.session.add(new_log)
    db.session.commit()
    
    current_streak, longest_streak = calculate_streak(habit_id)
    return jsonify({'message': 'Habit completed!', 'current_streak': current_streak, 'longest_streak': longest_streak}), 200

@app.route('/api/analytics', methods=['GET'])
@require_auth
def get_analytics(user):
    habits = Habit.query.filter_by(user_id=user.id).all()
    total_habits = len(habits)
    overall_longest_streak = 0
    
    for habit in habits:
        _, longest_streak = calculate_streak(habit.id)
        overall_longest_streak = max(overall_longest_streak, longest_streak)
    
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    recent_logs = HabitLog.query.join(Habit).filter(Habit.user_id == user.id, HabitLog.completed_date >= thirty_days_ago).all()
    
    expected_completions = total_habits * 30
    actual_completions = len(recent_logs)
    completion_percentage = (actual_completions / expected_completions * 100) if expected_completions > 0 else 0
    consistency_score = min(100, completion_percentage * 1.2)
    
    weekly_data = {}
    for i in range(7):
        date = datetime.now().date() - timedelta(days=i)
        count = HabitLog.query.join(Habit).filter(Habit.user_id == user.id, HabitLog.completed_date == date).count()
        weekly_data[date.strftime('%a')] = count
    
    streak_data = {}
    for i in range(30, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        count = HabitLog.query.join(Habit).filter(Habit.user_id == user.id, HabitLog.completed_date == date).count()
        streak_data[date.strftime('%m/%d')] = count
    
    heatmap_data = []
    for i in range(90):
        date = datetime.now().date() - timedelta(days=i)
        count = HabitLog.query.join(Habit).filter(Habit.user_id == user.id, HabitLog.completed_date == date).count()
        heatmap_data.append({'date': date.isoformat(), 'count': count})
    
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
            'completed_vs_missed': {'completed': len(recent_logs), 'missed': max(0, expected_completions - len(recent_logs))},
            'heatmap': heatmap_data
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
