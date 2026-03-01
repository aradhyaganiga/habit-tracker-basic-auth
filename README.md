python app.py
```

Visit: `http://localhost:5000/auth.html`

---

## 💡 How to Use

### **Getting Started**
1. **Register** - Create your account with username, email, and password
2. **Login** - Sign in to access your personal dashboard
3. **Add Habits** - Create habits you want to track (e.g., "Morning Meditation", "Daily Exercise")
4. **Mark Complete** - Click "✓ Complete" each day you complete a habit
5. **Watch Streaks Grow** - See your current and longest streaks increase!

### **Dashboard Stats Explained**
* **Total Habits** - Number of habits you're currently tracking
* **Longest Streak** - Your best streak across all habits
* **Completion Rate** - Percentage of habits completed in the last 30 days
* **Consistency Score** - Overall consistency metric (completion rate × 1.2)

### **Analytics Charts**
* **Streak Growth (Line)** - Daily completion trend over 30 days
* **Weekly Activity (Bar)** - Completions per day of the week
* **Completion Ratio (Pie)** - Completed vs. Missed in the last 30 days
* **Activity Heatmap** - Visual 90-day history (darker = more completions)

---

## 📁 Project Structure
```
habit-tracker-visualizer/
├── backend/
│   ├── app.py              # Flask application with Basic Auth
│   ├── models.py           # SQLAlchemy database models
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Main habit tracker interface
│   ├── auth.html           # Login/Register page
│   ├── css/
│   │   ├── styles.css      # Main app styles
│   │   └── auth.css        # Authentication page styles
│   └── js/
│       ├── app.js          # Main application logic
│       └── auth.js         # Authentication logic
├── database/
│   └── schema.sql          # MySQL database schema
└── README.md
