// TRAKN - Personal Expense Tracker JavaScript

const API_BASE_URL = '/api';

// ==================== THEME ====================

const ThemeManager = {
    init() {
        const savedTheme = localStorage.getItem('trakn-theme') || 'light';
        this.setTheme(savedTheme);
        document.querySelectorAll('.theme-toggle, [data-theme-toggle]').forEach(btn => {
            btn.addEventListener('click', () => this.toggle());
        });
    },
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('trakn-theme', theme);
        document.querySelectorAll('.theme-toggle span').forEach(span => {
            span.textContent = theme === 'dark' ? 'Light' : 'Dark';
        });
    },
    toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        this.setTheme(current === 'dark' ? 'light' : 'dark');
    },
    get() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }
};

// ==================== TOAST ====================

const Toast = {
    container: null,
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    },
    show(message, type = 'success', duration = 3000) {
        this.init();
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : '⚠';
        toast.innerHTML = `<span style="font-weight:bold;">${icon}</span><span>${message}</span>`;
        this.container.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    success(message) { this.show(message, 'success'); },
    error(message)   { this.show(message, 'error'); },
    warning(message) { this.show(message, 'warning'); }
};

// ==================== API ====================

const API = {
    getToken() {
        return localStorage.getItem('trakn-token');
    },
    async request(endpoint, options = {}) {
        const headers = {};
        const token = this.getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`;
        if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            credentials: 'include',
            ...options,
            headers: { ...headers, ...options.headers }
        });

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'An error occurred');
            return data;
        } else {
            if (!response.ok) throw new Error('An error occurred');
            return response;
        }
    },
    get(endpoint)        { return this.request(endpoint, { method: 'GET' }); },
    delete(endpoint)     { return this.request(endpoint, { method: 'DELETE' }); },
    put(endpoint, body)  { return this.request(endpoint, { method: 'PUT',  body: JSON.stringify(body) }); },
    post(endpoint, body) {
        if (body instanceof FormData)
            return this.request(endpoint, { method: 'POST', body });
        return this.request(endpoint, { method: 'POST', body: JSON.stringify(body) });
    }
};

// ==================== AUTH ====================

const Auth = {
    async login(email, password) {
        const response = await API.post('/auth/login', { email, password });
        localStorage.setItem('trakn-token', response.token);
        localStorage.setItem('trakn-user',  JSON.stringify(response.user));
        localStorage.setItem('trakn-is-admin', response.user?.role === 'admin' ? 'true' : 'false');
        return response;
    },
    async register(userData) {
        const response = await API.post('/auth/register', userData);
        localStorage.setItem('trakn-token', response.token);
        localStorage.setItem('trakn-user',  JSON.stringify(response.user));
        localStorage.setItem('trakn-is-admin', 'false');
        return response;
    },
    logout() {
        localStorage.removeItem('trakn-token');
        localStorage.removeItem('trakn-user');
        localStorage.removeItem('trakn-is-admin');
        window.location.href = '/login.html';
    },
    getUser()         { const u = localStorage.getItem('trakn-user'); return u ? JSON.parse(u) : null; },
    getToken()        { return localStorage.getItem('trakn-token'); },
    isAuthenticated() { return !!this.getToken(); },
    isAdmin()         { return localStorage.getItem('trakn-is-admin') === 'true'; },
    checkAuth() {
        if (!this.isAuthenticated()) { window.location.href = '/login.html'; return false; }
        return true;
    }
};

// ==================== TRANSACTIONS ====================

const Transactions = {
    async getAll(filters = {}) {
        const params = new URLSearchParams();
        for (const key in filters) { if (filters[key]) params.append(key, filters[key]); }
        const qs = params.toString();
        return API.get(`/transactions${qs ? '?' + qs : ''}`);
    },
    async getById(id)      { return API.get(`/transactions/${id}`); },
    async create(data)     { return API.post('/transactions', data); },
    async update(id, data) { return API.put(`/transactions/${id}`, data); },
    async delete(id)       { return API.delete(`/transactions/${id}`); },
    async getSummary(month, year) {
        const params = new URLSearchParams();
        if (month) params.append('month', month);
        if (year)  params.append('year', year);
        const qs = params.toString();
        return API.get(`/transactions/summary${qs ? '?' + qs : ''}`);
    },
    async exportCSV() {
        const response = await API.get('/transactions/export');
        const blob = await response.blob();
        const url  = window.URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href = url;
        a.download = `trakn-transactions-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        return true;
    },
    async importCSV(file) {
        const formData = new FormData();
        formData.append('file', file);
        return API.post('/transactions/import', formData);
    }
};

// ==================== BUDGETS ====================

const Budgets = {
    async getAll()         { return API.get('/budgets'); },
    async create(data)     { return API.post('/budgets', data); },
    async update(id, data) { return API.put(`/budgets/${id}`, data); },
    async delete(id)       { return API.delete(`/budgets/${id}`); }
};

// ==================== RECURRING ====================

const Recurring = {
    async getAll()         { return API.get('/recurring'); },
    async create(data)     { return API.post('/recurring', data); },
    async update(id, data) { return API.put(`/recurring/${id}`, data); },
    async delete(id)       { return API.delete(`/recurring/${id}`); }
};

// ==================== BALANCE SHEET ====================

const BalanceSheet = {
    async getAssets()          { return API.get('/assets'); },
    async getLiabilities()     { return API.get('/liabilities'); },
    async addAsset(data)       { return API.post('/assets', data); },
    async addLiability(data)   { return API.post('/liabilities', data); },
    async deleteAsset(id)      { return API.delete(`/assets/${id}`); },
    async deleteLiability(id)  { return API.delete(`/liabilities/${id}`); }
};

// ==================== GOALS ====================

const Goals = {
    async getAll()         { return API.get('/goals'); },
    async create(data)     { return API.post('/goals', data); },
    async update(id, data) { return API.put(`/goals/${id}`, data); },
    async delete(id)       { return API.delete(`/goals/${id}`); }
};

// ==================== PROFILE ====================

const Profile = {
    async get()                                      { return API.get('/profile'); },
    async update(data)                               { return API.put('/profile', data); },
    async removeAvatar()                             { return API.delete('/profile/avatar'); },
    async changePassword(currentPassword, newPassword) {
        return API.put('/profile/password', { currentPassword, newPassword });
    },
    async uploadAvatar(file) {
        const formData = new FormData();
        formData.append('avatar', file);
        return API.post('/profile/avatar', formData);
    }
};

// ==================== ADMIN ====================

const Admin = {
    async getStats()           { return API.get('/admin/stats'); },
    async getUsers()           { return API.get('/admin/users'); },
    async createUser(data)     { return API.post('/admin/users', data); },
    async updateUser(id, data) { return API.put(`/admin/users/${id}`, data); },
    async deleteUser(id)       { return API.delete(`/admin/users/${id}`); }
};

// ==================== ANALYTICS ====================

const Analytics = {
    async getData(period = 'month') {
        return API.get(`/analytics?period=${period}`);
    },
    async getCategoryBreakdown(type = 'expense', period = 'month') {
        return API.get(`/analytics/categories?type=${type}&period=${period}`);
    },
    async getMonthlyTrend(months = 6) {
        return API.get(`/analytics/trend?months=${months}`);
    }
};

// ==================== UTILS ====================

const Utils = {
    formatCurrency(amount, currency = '₹') {
        return `${currency}${parseFloat(amount || 0).toLocaleString('en-IN', {
            minimumFractionDigits: 2, maximumFractionDigits: 2
        })}`;
    },

    // FIXED: No new Date() - parse YYYY-MM-DD string directly to avoid timezone shift
    formatDate(dateStr) {
        if (!dateStr) return '';
        const str = String(dateStr).split('T')[0];
        const parts = str.split('-').map(Number);
        if (parts.length !== 3 || !parts[0] || !parts[1] || !parts[2]) return dateStr;
        const [y, m, d] = parts;
        const months = ['Jan','Feb','Mar','Apr','May','Jun',
                        'Jul','Aug','Sep','Oct','Nov','Dec'];
        if (!months[m - 1]) return dateStr;
        return `${d} ${months[m - 1]} ${y}`;
    },

    formatDateTime(date) {
        return new Date(date).toLocaleString('en-IN',
            { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    },

    // Safe today string without timezone shift
    todayStr() {
        const d = new Date();
        return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
    },

    getGreeting() {
        const h = new Date().getHours();
        if (h < 12) return 'Good Morning';
        if (h < 17) return 'Good Afternoon';
        return 'Good Evening';
    },
    debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    },
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
};

// ==================== VALIDATOR ====================

const Validator = {
    email(v)          { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? null : 'Please enter a valid email address'; },
    required(v)       { return v && v.trim() ? null : 'This field is required'; },
    minLength(v, min) { return v && v.length >= min ? null : `Minimum ${min} characters required`; },
    maxLength(v, max) { return v && v.length <= max ? null : `Maximum ${max} characters allowed`; },
    amount(v)         { const n = parseFloat(v); return !isNaN(n) && n > 0 ? null : 'Please enter a valid amount'; },
    password(v)       { return v && v.length >= 8 ? null : 'Password must be at least 8 characters'; },

    validate(form, rules) {
        const errors = {}; let isValid = true;
        for (const field in rules) {
            for (const rule of rules[field]) {
                let error;
                if (typeof rule === 'string') {
                    error = this[rule](form[field]);
                } else {
                    const [name, param] = Object.entries(rule)[0];
                    error = this[name](form[field], param);
                }
                if (error) { errors[field] = error; isValid = false; break; }
            }
        }
        return { isValid, errors };
    },

    showErrors(form, errors) {
        form.querySelectorAll('.form-error').forEach(el => el.remove());
        form.querySelectorAll('.form-control.error').forEach(el => el.classList.remove('error'));
        for (const field in errors) {
            const input = form.querySelector(`[name="${field}"]`);
            if (input) {
                input.classList.add('error');
                const el = document.createElement('div');
                el.className = 'form-error';
                el.style.cssText = 'color:var(--red-expense);font-size:0.85rem;margin-top:0.25rem;';
                el.textContent = errors[field];
                input.parentNode.appendChild(el);
            }
        }
    }
};

// ==================== SIDEBAR ====================

function toggleSidebar() {
    document.querySelector('.sidebar')?.classList.toggle('open');
}

// ==================== DOM INIT ====================

document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();

    const greetingEl = document.querySelector('.greeting-text');
    if (greetingEl) greetingEl.textContent = Utils.getGreeting();

    const dateEl = document.querySelector('.current-date');
    if (dateEl) dateEl.textContent = Utils.formatDateTime(new Date());

    document.querySelector('.menu-toggle')?.addEventListener('click', toggleSidebar);

    document.querySelectorAll('[data-logout]').forEach(btn => {
        btn.addEventListener('click', (e) => { e.preventDefault(); Auth.logout(); });
    });

    document.querySelectorAll('form[data-api]').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data     = Object.fromEntries(new FormData(form));
            const endpoint = form.getAttribute('data-api');
            const method   = form.getAttribute('data-method') || 'POST';
            const redirect = form.getAttribute('data-redirect');
            const btn      = form.querySelector('button[type="submit"]');
            const original = btn.textContent;
            try {
                btn.disabled = true; btn.textContent = 'Processing...';
                method === 'POST' ? await API.post(endpoint, data) : await API.put(endpoint, data);
                Toast.success('Operation successful!');
                if (redirect) setTimeout(() => { window.location.href = redirect; }, 1000);
                else form.reset();
            } catch (error) {
                Toast.error(error.message);
            } finally {
                btn.textContent = original; btn.disabled = false;
            }
        });
    });
});

var _nc = {val:'0',expr:'',op:null,prev:null,newNum:true,mem:0,lastOp:null,lastVal:null,evaled:false};

function ncFmt(n) {
  if (!isFinite(n)) return 'Error';
  var s = parseFloat(n.toFixed(10)).toString();
  if (s.length > 14) s = parseFloat(n.toPrecision(10)).toString();
  return s;
}
function ncUp() {
  var v = _nc.val, el = document.getElementById('nc-val');
  el.textContent = v;
  el.style.fontSize = v.length > 10 ? '28px' : v.length > 7 ? '36px' : '44px';
  document.getElementById('nc-expr').textContent = _nc.expr;
  document.getElementById('nc-mem').textContent = _nc.mem !== 0 ? 'M: ' + ncFmt(_nc.mem) : '';
}
function ncCompute(a, b, op) {
  if (op === '÷') return b === 0 ? Infinity : a / b;
  if (op === '×') return a * b;
  if (op === '−') return a - b;
  if (op === '+') return a + b;
  return b;
}
function nc(k) {
  var s = _nc;
  if (k === 'AC') { _nc = {val:'0',expr:'',op:null,prev:null,newNum:true,mem:s.mem,lastOp:null,lastVal:null,evaled:false}; ncUp(); return; }
  if (k === 'C')  { s.val='0'; s.newNum=true; ncUp(); return; }
  if (/^[0-9]$/.test(k)) {
    if (s.evaled) { s.expr=''; s.evaled=false; }
    s.val = s.newNum ? k : (s.val.length < 14 ? (s.val==='0'?k:s.val+k) : s.val);
    s.newNum = false; ncUp(); return;
  }
  if (k === '.') {
    if (s.evaled) { s.val='0'; s.expr=''; s.evaled=false; }
    if (s.newNum) { s.val='0.'; s.newNum=false; }
    else if (!s.val.includes('.')) s.val += '.';
    ncUp(); return;
  }
  if (k === '+/-') { s.val = ncFmt(-parseFloat(s.val)); ncUp(); return; }
  if (k === '%') {
    var pv = parseFloat(s.val);
    s.val = ncFmt(s.prev != null && s.op ? s.prev * pv / 100 : pv / 100);
    ncUp(); return;
  }
  if (k === 'MC') { s.mem = 0; ncUp(); return; }
  if (k === 'MR') { s.val = ncFmt(s.mem); s.newNum = true; ncUp(); return; }
  if (k === 'M+') { s.mem += parseFloat(s.val); ncUp(); return; }
  if (k === 'M-') { s.mem -= parseFloat(s.val); ncUp(); return; }
  if ('÷×−+'.includes(k)) {
    s.evaled = false;
    var cv = parseFloat(s.val);
    if (s.op && !s.newNum) { var rr = ncCompute(s.prev, cv, s.op); s.prev = rr; s.val = ncFmt(rr); } else { s.prev = cv; }
    s.op = k; s.newNum = true; s.expr = ncFmt(s.prev) + ' ' + k;
    document.getElementById('nc-hist').textContent = '';
    ncUp(); return;
  }
  if (k === '=') {
    var b = s.evaled ? s.lastVal : parseFloat(s.val);
    if (!s.evaled) s.lastVal = b;
    if (s.op) {
      var res = ncCompute(s.prev, b, s.op);
      document.getElementById('nc-hist').textContent = ncFmt(s.prev) + ' ' + s.op + ' ' + ncFmt(b) + ' =';
      s.expr = ''; s.val = ncFmt(res); s.prev = res; s.evaled = true; s.newNum = true;
      ncUp();
    }
  }
}



// ==================== GLOBAL EXPORT ====================

window.FinFlow = {
    API,
    Auth,
    Transactions,
    Budgets,
    Recurring,
    BalanceSheet,
    Goals,
    Profile,
    Admin,
    Analytics,
    Utils,
    Validator,
    Toast,
    ThemeManager
};