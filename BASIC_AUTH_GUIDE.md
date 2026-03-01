# 🔥 Habit Tracker - BASIC AUTHENTICATION VERSION

## ✨ What This Is

**SIMPLE HTTP BASIC AUTHENTICATION!**

✅ NO sessions  
✅ NO cookies  
✅ NO JWT tokens  
✅ **Just username + password stored in browser**  
✅ **Sent with EVERY request**  

---

## 🚀 How It Works

### **Login Flow:**
1. User enters username/password
2. Credentials stored in `localStorage`
3. Every API request includes `Authorization: Basic [credentials]`
4. Backend checks username/password on EVERY request
5. If valid → Process request
6. If invalid → Return 401

### **No Sessions = No Problems!**
- Browser stores credentials locally
- Every request = fresh authentication
- Logout = delete credentials from localStorage
- Simple and reliable!

---

## 📝 Setup (5 Steps)

### **Step 1: Database**
```bash
mysql -u root -p
CREATE DATABASE habit_tracker;
USE habit_tracker;
SOURCE database/schema.sql;
EXIT;
```

### **Step 2: Update Password**
Edit `backend/app.py` line 12:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:YOUR_PASSWORD@localhost/habit_tracker'
```

### **Step 3: Install Packages**
```bash
cd backend
pip install -r requirements.txt
```

### **Step 4: Run**
```bash
python app.py
```

### **Step 5: Open Browser**
```
http://localhost:5000/auth.html
```

---

## 🎯 How to Use

1. **Register** - Create account
2. **Login** - Enter credentials (stored in browser)
3. **Use app** - All requests automatically include credentials
4. **Logout** - Clears stored credentials

---

## 🔒 Security Notes

**⚠️ Important:**
- Credentials stored in plain text in `localStorage`
- **For development/demo ONLY**
- **NOT for production without HTTPS!**

**For Production:**
- Use HTTPS (encrypts credentials in transit)
- Consider adding encryption for localStorage
- Or use JWT/sessions instead

---

## ✅ Advantages

✅ **Simple** - No complex session management  
✅ **Works** - No cookie/session issues  
✅ **Stateless** - Backend doesn't store sessions  
✅ **Reliable** - No 401/302 redirect loops  
✅ **Easy to debug** - Check localStorage for credentials  

---

## 📚 How Basic Auth Works

### **Request Example:**
```javascript
fetch('/api/habits', {
    headers: {
        'Authorization': 'Basic ' + btoa('username:password')
    }
})
```

### **Backend Check:**
```python
@require_auth
def get_habits(user):
    # User is authenticated!
    # Do stuff...
```

---

## 🐛 Troubleshooting

### **Can't login?**
- Check MySQL password in `app.py`
- Check database exists
- Check credentials are correct

### **401 Unauthorized?**
- Check `localStorage` has username/password
- Try clearing localStorage and login again
- Check backend is running

### **How to check stored credentials:**
```javascript
// In browser console (F12)
console.log(localStorage.getItem('username'))
console.log(localStorage.getItem('password'))
```

---

## 💡 Why This Works

**Unlike sessions/JWT:**
- No server-side storage
- No cookie issues
- No token expiry
- No session management

**Every request is independent!**

---

## 🎉 Done!

Simple, reliable, basic authentication! 🔥

**For production:** Use HTTPS + consider JWT for better security!

---

Happy coding! 💪
