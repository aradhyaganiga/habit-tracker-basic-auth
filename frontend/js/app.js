const API_URL = 'http://localhost:5000/api';

let habits = [];
let charts = { streak: null, weekly: null, pie: null };

const addHabitForm = document.getElementById('add-habit-form');
const habitsList = document.getElementById('habits-list');
const emptyState = document.getElementById('empty-state');
const themeToggle = document.getElementById('theme-toggle');
const sunIcon = document.getElementById('sun-icon');
const moonIcon = document.getElementById('moon-icon');
const logoutBtn = document.getElementById('logout-btn');

// Get stored credentials
function getAuthHeaders() {
    const username = localStorage.getItem('username');
    const password = localStorage.getItem('password');
    
    if (!username || !password) {
        return null;
    }
    
    const credentials = btoa(`${username}:${password}`);
    return {
        'Authorization': `Basic ${credentials}`,
        'Content-Type': 'application/json'
    };
}

// Fetch with Basic Auth
async function fetchWithAuth(url, options = {}) {
    const authHeaders = getAuthHeaders();
    
    if (!authHeaders) {
        window.location.replace('/auth.html');
        return null;
    }
    
    const response = await fetch(url, {
        ...options,
        headers: {
            ...authHeaders,
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        localStorage.removeItem('username');
        localStorage.removeItem('password');
        window.location.replace('/auth.html');
        return null;
    }
    
    return response;
}

// Logout
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('username');
        localStorage.removeItem('password');
        window.location.replace('/auth.html');
    });
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    if (!getAuthHeaders()) {
        window.location.replace('/auth.html');
        return;
    }
    
    displayUsername();
    initializeTheme();
    await loadHabits();
    await loadAnalytics();
    setupEventListeners();
});

function displayUsername() {
    const username = localStorage.getItem('username');
    const userDisplay = document.getElementById('user-display');
    if (userDisplay && username) {
        userDisplay.textContent = `👋 ${username}`;
    }
}

// Theme
function initializeTheme() {
    const isDark = localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (isDark) {
        document.documentElement.classList.add('dark');
        sunIcon.classList.add('hidden');
        moonIcon.classList.remove('hidden');
    }
}

themeToggle.addEventListener('click', () => {
    document.documentElement.classList.toggle('dark');
    const isDark = document.documentElement.classList.contains('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    sunIcon.classList.toggle('hidden');
    moonIcon.classList.toggle('hidden');
    updateChartsTheme();
});

function updateChartsTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#ffffff' : '#111827';
    const gridColor = isDark ? '#374151' : '#e5e7eb';
    
    Object.values(charts).forEach(chart => {
        if (chart) {
            chart.options.plugins.legend.labels.color = textColor;
            if (chart.options.scales) {
                if (chart.options.scales.x) {
                    chart.options.scales.x.ticks.color = textColor;
                    chart.options.scales.x.grid.color = gridColor;
                }
                if (chart.options.scales.y) {
                    chart.options.scales.y.ticks.color = textColor;
                    chart.options.scales.y.grid.color = gridColor;
                }
            }
            chart.update();
        }
    });
}

function setupEventListeners() {
    addHabitForm.addEventListener('submit', handleAddHabit);
}

function showToast(message, duration = 3000) {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    toastMessage.textContent = message;
    toast.classList.remove('hidden');
    setTimeout(() => toast.classList.add('hidden'), duration);
}

// API Calls
async function loadHabits() {
    try {
        const response = await fetchWithAuth(`${API_URL}/habits`);
        if (!response) return;
        if (!response.ok) throw new Error('Failed to load habits');
        habits = await response.json();
        renderHabits();
    } catch (error) {
        console.error('Error loading habits:', error);
        showToast('Failed to load habits');
    }
}

async function handleAddHabit(e) {
    e.preventDefault();
    const name = document.getElementById('habit-name').value.trim();
    const description = document.getElementById('habit-description').value.trim();
    
    if (!name) {
        showToast('Please enter a habit name');
        return;
    }
    
    try {
        const response = await fetchWithAuth(`${API_URL}/habits`, {
            method: 'POST',
            body: JSON.stringify({ name, description })
        });
        
        if (!response) return;
        if (!response.ok) throw new Error('Failed to add habit');
        
        const newHabit = await response.json();
        habits.push(newHabit);
        document.getElementById('habit-name').value = '';
        document.getElementById('habit-description').value = '';
        renderHabits();
        loadAnalytics();
        showToast('✨ Habit added successfully!');
    } catch (error) {
        console.error('Error adding habit:', error);
        showToast('Failed to add habit');
    }
}

async function deleteHabit(habitId) {
    if (!confirm('Are you sure you want to delete this habit?')) return;
    
    try {
        const response = await fetchWithAuth(`${API_URL}/habits/${habitId}`, { method: 'DELETE' });
        if (!response) return;
        if (!response.ok) throw new Error('Failed to delete habit');
        
        habits = habits.filter(h => h.id !== habitId);
        renderHabits();
        loadAnalytics();
        showToast('🗑️ Habit deleted');
    } catch (error) {
        console.error('Error deleting habit:', error);
        showToast('Failed to delete habit');
    }
}

async function completeHabit(habitId) {
    try {
        const response = await fetchWithAuth(`${API_URL}/habits/${habitId}/complete`, { method: 'POST' });
        if (!response) return;
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to complete habit');
        }
        
        const result = await response.json();
        const habit = habits.find(h => h.id === habitId);
        if (habit) {
            habit.current_streak = result.current_streak;
            habit.longest_streak = result.longest_streak;
        }
        renderHabits();
        loadAnalytics();
        showToast(`🔥 Streak: ${result.current_streak} days!`);
    } catch (error) {
        console.error('Error completing habit:', error);
        showToast(error.message);
    }
}

function renderHabits() {
    if (habits.length === 0) {
        habitsList.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    habitsList.innerHTML = habits.map(habit => `
        <div class="habit-item">
            <div class="habit-info flex-1">
                <h3>${escapeHtml(habit.name)}</h3>
                ${habit.description ? `<p>${escapeHtml(habit.description)}</p>` : ''}
                <div class="habit-streaks">
                    <span class="streak-badge streak-current">🔥 Current: ${habit.current_streak} days</span>
                    <span class="streak-badge streak-longest">🏆 Best: ${habit.longest_streak} days</span>
                </div>
            </div>
            <div class="habit-actions">
                <button class="btn-success" onclick="completeHabit(${habit.id})">✓ Complete</button>
                <button class="btn-danger" onclick="deleteHabit(${habit.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function loadAnalytics() {
    try {
        const response = await fetchWithAuth(`${API_URL}/analytics`);
        if (!response) return;
        if (!response.ok) throw new Error('Failed to load analytics');
        
        const data = await response.json();
        document.getElementById('total-habits').textContent = data.dashboard.total_habits;
        document.getElementById('longest-streak').textContent = data.dashboard.longest_streak;
        document.getElementById('completion-percentage').textContent = data.dashboard.completion_percentage + '%';
        document.getElementById('consistency-score').textContent = data.dashboard.consistency_score;
        
        renderStreakChart(data.charts.streak_growth);
        renderWeeklyChart(data.charts.weekly_completion);
        renderPieChart(data.charts.completed_vs_missed);
        renderHeatmap(data.charts.heatmap);
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

function renderStreakChart(data) {
    const ctx = document.getElementById('streak-chart');
    const isDark = document.documentElement.classList.contains('dark');
    if (charts.streak) charts.streak.destroy();
    
    charts.streak = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Daily Completions',
                data: Object.values(data),
                borderColor: 'rgb(102, 126, 234)',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: isDark ? '#ffffff' : '#111827' } } },
            scales: {
                y: { beginAtZero: true, ticks: { color: isDark ? '#ffffff' : '#111827' }, grid: { color: isDark ? '#374151' : '#e5e7eb' } },
                x: { ticks: { color: isDark ? '#ffffff' : '#111827' }, grid: { color: isDark ? '#374151' : '#e5e7eb' } }
            }
        }
    });
}

function renderWeeklyChart(data) {
    const ctx = document.getElementById('weekly-chart');
    const isDark = document.documentElement.classList.contains('dark');
    if (charts.weekly) charts.weekly.destroy();
    
    charts.weekly = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Completions',
                data: Object.values(data),
                backgroundColor: ['rgba(239, 68, 68, 0.8)', 'rgba(249, 115, 22, 0.8)', 'rgba(234, 179, 8, 0.8)', 'rgba(34, 197, 94, 0.8)', 'rgba(59, 130, 246, 0.8)', 'rgba(139, 92, 246, 0.8)', 'rgba(236, 72, 153, 0.8)'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { labels: { color: isDark ? '#ffffff' : '#111827' } } },
            scales: {
                y: { beginAtZero: true, ticks: { color: isDark ? '#ffffff' : '#111827' }, grid: { color: isDark ? '#374151' : '#e5e7eb' } },
                x: { ticks: { color: isDark ? '#ffffff' : '#111827' }, grid: { display: false } }
            }
        }
    });
}

function renderPieChart(data) {
    const ctx = document.getElementById('pie-chart');
    const isDark = document.documentElement.classList.contains('dark');
    if (charts.pie) charts.pie.destroy();
    
    charts.pie = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Completed', 'Missed'],
            datasets: [{ data: [data.completed, data.missed], backgroundColor: ['rgba(34, 197, 94, 0.8)', 'rgba(239, 68, 68, 0.8)'] }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom', labels: { color: isDark ? '#ffffff' : '#111827', padding: 20 } } }
        }
    });
}

function renderHeatmap(data) {
    const container = document.getElementById('heatmap-container');
    const maxCount = Math.max(...data.map(d => d.count), 1);
    
    container.innerHTML = `<div class="heatmap-grid">${data.map(day => {
        const intensity = day.count === 0 ? 0 : Math.ceil((day.count / maxCount) * 4);
        const date = new Date(day.date);
        return `<div class="heatmap-cell heat-${intensity}" title="${date.toLocaleDateString()}: ${day.count} completions"></div>`;
    }).join('')}</div>`;
}

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}
