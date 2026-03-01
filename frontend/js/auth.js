const API_URL = 'http://localhost:5000/api';

// DOM Elements
const loginContainer = document.getElementById('login-container');
const registerContainer = document.getElementById('register-container');
const showRegisterBtn = document.getElementById('show-register');
const showLoginBtn = document.getElementById('show-login');

// Toggle views
showRegisterBtn.addEventListener('click', (e) => {
    e.preventDefault();
    loginContainer.classList.add('hidden');
    registerContainer.classList.remove('hidden');
});

showLoginBtn.addEventListener('click', (e) => {
    e.preventDefault();
    registerContainer.classList.add('hidden');
    loginContainer.classList.remove('hidden');
});

// Show message
function showMessage(elementId, message, type = 'error') {
    const messageEl = document.getElementById(elementId);
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    setTimeout(() => {
        messageEl.textContent = '';
        messageEl.className = 'message';
    }, 5000);
}

// Register Handler
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    if (!username || !email || !password) {
        showMessage('register-message', 'Please fill in all fields');
        return;
    }
    
    if (password.length < 6) {
        showMessage('register-message', 'Password must be at least 6 characters');
        return;
    }
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account...';
    
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('register-message', 'Account created! Logging you in...', 'success');
            
            // Store credentials
            localStorage.setItem('username', username);
            localStorage.setItem('password', password);
            
            setTimeout(() => {
                window.location.replace('/');
            }, 1000);
        } else {
            showMessage('register-message', data.error || 'Registration failed');
        }
    } catch (error) {
        showMessage('register-message', 'Network error. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Register';
    }
});

// Login Handler
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const loginInput = document.getElementById('login-input').value.trim();
    const password = document.getElementById('login-password').value;
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    if (!loginInput || !password) {
        showMessage('login-message', 'Please fill in all fields');
        return;
    }
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';
    
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ login: loginInput, password: password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('login-message', 'Login successful! Redirecting...', 'success');
            
            // Store credentials
            localStorage.setItem('username', loginInput);
            localStorage.setItem('password', password);
            
            setTimeout(() => {
                window.location.replace('/');
            }, 500);
        } else {
            showMessage('login-message', data.error || 'Login failed');
        }
    } catch (error) {
        showMessage('login-message', 'Network error. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Login';
    }
});
