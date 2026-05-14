"""
TRAKN - Personal Expense Tracker
Flask API Application with SQLite Database
"""

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import csv
import io
import uuid
from datetime import datetime
from functools import wraps
import jwt
import os
import base64
import re

# Import database module
from database import (
    init_db, create_default_admin,
    create_user, get_user_by_email, get_user_by_id, update_user,
    verify_password, get_all_users, update_user_status, delete_user,
    is_admin, update_user_role, count_admins,
    create_transaction, get_transactions, get_transaction_by_id,
    update_transaction, delete_transaction as db_delete_transaction,
    get_transaction_summary, get_category_breakdown,
    get_dashboard_data, get_admin_stats,
    create_budget, get_budgets, update_budget, delete_budget as db_delete_budget,update_password,
    create_recurring, get_recurring, delete_recurring, update_recurring,
    create_goal, get_goals, delete_goal,
    create_asset, get_assets, delete_asset,
    create_liability, get_liabilities, delete_liability,get_db
)

# ==================== APP SETUP ====================

app = Flask(__name__,
            static_folder='../static',
            template_folder='../templates')
CORS(app)
app.config['SECRET_KEY'] = 'trakn-super-secret-key-2024-secure'

# ==================== CONFIGURATION ====================

ADMIN_NOTIFICATION_EMAIL = "your-email@gmail.com"   # UPDATE THIS

SOCIAL_LINKS = {
    'github':    'https://github.com/yourusername',
    'linkedin':  'https://linkedin.com/in/yourusername',
    'twitter':   'https://twitter.com/yourusername',
    'instagram': 'https://instagram.com/yourusername'
}

APP_INFO = {
    'name':          'TRAKN',
    'version':       '1.0.0',
    'support_email': 'support@trakn.com',
    'phone':         '+91 9876543210'
}

USER_DATA_CSV = os.path.join(os.path.dirname(__file__), '..', 'data', 'users_data.csv')

# ==================== IN-MEMORY STORES ====================
# FIX: Single set of stores — no duplicates, no Blueprint conflicts




def _find_by_id(store, item_id):
    return next((i for i in store if str(i.get('id')) == str(item_id)), None)


# ==================== JWT HELPERS ====================

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow().timestamp() + 86400 * 30
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')


def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ==================== USER TRACKING ====================

def save_user_to_csv(user_data):
    os.makedirs(os.path.dirname(USER_DATA_CSV), exist_ok=True)
    file_exists = os.path.exists(USER_DATA_CSV)
    with open(USER_DATA_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['Date', 'Name', 'Email', 'Phone', 'Role', 'Status'])
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_data.get('name', ''), user_data.get('email', ''),
            user_data.get('phone', ''), user_data.get('role', 'user'),
            user_data.get('status', 'active')
        ])


def log_user_activity(user_id, activity_type, details=''):
    user = get_user_by_id(user_id)
    if user:
        print(f"[ACTIVITY] {datetime.now().isoformat()} | {activity_type} | {user['email']} | {details}")


# ==================== DECORATORS ====================

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        user = get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        if user['status'] != 'active':
            return jsonify({'error': 'Account is inactive'}), 401
        return f(user_id, *args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(user_id, *args, **kwargs):
        if not is_admin(user_id):
            return jsonify({'error': 'Admin access required'}), 403
        return f(user_id, *args, **kwargs)
    return decorated


# ==================== STATIC / PAGE SERVING ====================

@app.route('/')
def index():
    return send_from_directory('../templates', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('../static', path)

@app.route('/<path:path>')
def serve_page(path):
    if path.startswith('api/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    if path.endswith('.html'):
        return send_from_directory('../templates', path)
    return send_from_directory('../static', path)


# ==================== AUTH ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    for field in ['name', 'email', 'password']:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    email = data['email'].strip().lower()
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Invalid email format'}), 400
    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if get_user_by_email(email):
        return jsonify({'error': 'Email already registered'}), 400
    user_id = create_user(name=data['name'].strip(), email=email,
                          password=data['password'], phone=data.get('phone', ''))
    if not user_id:
        return jsonify({'error': 'Failed to create user'}), 500
    save_user_to_csv({'name': data['name'].strip(), 'email': email,
                      'phone': data.get('phone', ''), 'role': 'user', 'status': 'active'})
    log_user_activity(user_id, 'NEW_REGISTRATION', email)
    token = generate_token(user_id)
    user  = get_user_by_id(user_id)
    return jsonify({
        'message': 'User registered successfully', 'token': token,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email'],
                 'phone': user.get('phone', ''), 'role': user['role']}
    }), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    email = data['email'].strip().lower()
    user  = verify_password(email, data['password'])
    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401
    if user['status'] != 'active':
        return jsonify({'error': 'Account is inactive. Please contact admin.'}), 401
    log_user_activity(user['id'], 'USER_LOGIN', email)
    token = generate_token(user['id'])
    return jsonify({
        'message': 'Login successful', 'token': token,
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email'],
                 'phone': user.get('phone', ''), 'role': user['role'], 'avatar': user['avatar']}
    })


@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify(user_id):
    user = get_user_by_id(user_id)
    return jsonify({
        'user': {'id': user['id'], 'name': user['name'], 'email': user['email'],
                 'phone': user.get('phone', ''), 'role': user['role'], 'avatar': user['avatar']}
    })


# ==================== CONFIG ====================

@app.route('/api/config/social-links', methods=['GET'])
def get_social_links():
    return jsonify(SOCIAL_LINKS)

@app.route('/api/config/app-info', methods=['GET'])
def get_app_info():
    return jsonify(APP_INFO)


# ==================== NOTIFICATIONS ====================

@app.route('/api/notifications', methods=['GET'])
@token_required
def get_notifications(user_id):
    notifications = []
    transactions = get_transactions(user_id)
    if transactions:
        for t in transactions[:5]:
            notifications.append({
                'type': t['type'],
                'title': 'Income Received' if t['type'] == 'income' else 'Expense Added',
                'text': f"{t['title']} - ₹{float(t['amount']):,.2f}",
                'time': t['date'], 'unread': True
            })
    budgets = get_budgets(user_id)
    if budgets:
        for b in budgets:
            notifications.append({
                'type': 'budget', 'title': 'Budget Active',
                'text': f"{b['category']}: ₹{float(b['amount']):,.2f}",
                'time': 'Active', 'unread': False
            })
    if not notifications:
        notifications.append({
            'type': 'system', 'title': 'Welcome to TRAKN!',
            'text': 'Start tracking your expenses by adding your first transaction.',
            'time': 'Just now', 'unread': True
        })
    return jsonify(notifications)


@app.route('/api/notifications/admin', methods=['GET'])
@admin_required
def get_admin_notifications(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, phone, created_at FROM users ORDER BY created_at DESC LIMIT 10')
        return jsonify([{
            'type': 'new_user', 'title': 'New User Registered',
            'text': f"{u['name']} ({u['email']})", 'time': u['created_at'],
            'phone': u['phone'] or 'Not provided', 'unread': True
        } for u in cursor.fetchall()])


# ==================== DASHBOARD ====================

@app.route('/api/dashboard', methods=['GET'])
@token_required
def dashboard(user_id):
    return jsonify(get_dashboard_data(user_id))


# ==================== TRANSACTIONS ====================

@app.route('/api/transactions', methods=['GET'])
@token_required
def get_user_transactions(user_id):
    filters = {k: request.args.get(k)
               for k in ('type', 'category', 'start_date', 'end_date') if request.args.get(k)}
    return jsonify([dict(t) for t in get_transactions(user_id, filters or None)])


@app.route('/api/transactions', methods=['POST'])
@token_required
def add_transaction(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    for field in ['title', 'amount', 'type', 'date']:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    if data['type'] not in ['income', 'expense']:
        return jsonify({'error': 'Type must be income or expense'}), 400
    try:
        amount = float(data['amount'])
        if amount <= 0: raise ValueError
    except ValueError:
        return jsonify({'error': 'Amount must be a positive number'}), 400
    tid = create_transaction(
        user_id=user_id, title=data['title'].strip(), amount=amount,
        trans_type=data['type'], category=data.get('category', 'other'),
        date=data['date'], notes=(data.get('notes') or '').strip() or None
    )
    return jsonify({'message': 'Transaction added successfully', 'id': tid}), 201


@app.route('/api/transactions/<int:transaction_id>', methods=['GET'])
@token_required
def get_transaction(user_id, transaction_id):
    t = get_transaction_by_id(transaction_id, user_id)
    if not t:
        return jsonify({'error': 'Transaction not found'}), 404
    return jsonify(dict(t))


@app.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@token_required
def edit_transaction(user_id, transaction_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if not get_transaction_by_id(transaction_id, user_id):
        return jsonify({'error': 'Transaction not found'}), 404
    if update_transaction(transaction_id, user_id, **data):
        return jsonify({'message': 'Transaction updated successfully'})
    return jsonify({'error': 'Failed to update transaction'}), 500


@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@token_required
def remove_transaction(user_id, transaction_id):
    if db_delete_transaction(transaction_id, user_id):
        return jsonify({'message': 'Transaction deleted successfully'})
    return jsonify({'error': 'Transaction not found'}), 404


@app.route('/api/transactions/summary', methods=['GET'])
@token_required
def transaction_summary(user_id):
    month   = request.args.get('month', type=int)
    year    = request.args.get('year',  type=int)
    summary = get_transaction_summary(user_id, month, year)
    return jsonify([dict(s) for s in summary])


@app.route('/api/transactions/export', methods=['GET'])
@token_required
def export_transactions(user_id):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Title', 'Type', 'Category', 'Amount', 'Notes'])
    for t in get_transactions(user_id):
        date_str = str(t['date'])
        try:
            date_str = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            pass
        writer.writerow([date_str, t['title'], t['type'],
                         t['category'] or '', f"{float(t['amount']):.2f}", t['notes'] or ''])
    output.seek(0)
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition':
                             f'attachment; filename=trakn-transactions-{datetime.now().strftime("%Y-%m-%d")}.csv'})


@app.route('/api/transactions/import', methods=['POST'])
@token_required
def import_transactions(user_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not file.filename or not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Only CSV files are supported'}), 400

    count, errors = 0, []
    try:
        content = file.stream.read()
        text_content = None
        for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
            try:
                text_content = content.decode(enc); break
            except Exception:
                continue

        field_map = {
            'date':     ['date', 'Date', 'DATE', 'transaction_date'],
            'title':    ['title', 'Title', 'description', 'Description', 'name'],
            'amount':   ['amount', 'Amount', 'value', 'Value'],
            'type':     ['type', 'Type', 'transaction_type'],
            'category': ['category', 'Category'],
            'notes':    ['notes', 'Notes', 'remarks']
        }

        def get_field(row, field_name):
            for alias in field_map.get(field_name, [field_name]):
                if alias in row and row[alias]:
                    v = row[alias]
                    return v.strip() if isinstance(v, str) else v
            return None

        for row_num, row in enumerate(csv.DictReader(io.StringIO(text_content, newline=None)), start=2):
            try:
                title      = get_field(row, 'title')
                amount_str = get_field(row, 'amount')
                trans_type = get_field(row, 'type')
                date_str   = get_field(row, 'date')

                if not all([title, amount_str, trans_type, date_str]):
                    errors.append(f"Row {row_num}: Missing required fields"); continue

                trans_type = trans_type.lower().strip()
                if trans_type not in ['income', 'expense']:
                    errors.append(f"Row {row_num}: Invalid type '{trans_type}'"); continue

                amount = float(re.sub(r'[^\d.]', '', str(amount_str)))
                if amount <= 0:
                    errors.append(f"Row {row_num}: Amount must be positive"); continue

                date_parsed = None
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%Y/%m/%d'):
                    try:
                        date_parsed = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d'); break
                    except ValueError:
                        continue
                if not date_parsed:
                    errors.append(f"Row {row_num}: Invalid date '{date_str}'"); continue

                create_transaction(
                    user_id=user_id, title=title, amount=amount, trans_type=trans_type,
                    category=(get_field(row, 'category') or 'other').lower(),
                    date=date_parsed, notes=get_field(row, 'notes') or ''
                )
                count += 1
            except Exception as ex:
                errors.append(f"Row {row_num}: {ex}")

        result = {'message': f'Successfully imported {count} transactions', 'count': count}
        if errors:
            result['errors'] = errors[:10]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Failed to import: {e}'}), 500


# ==================== AI CHAT ====================

@app.route('/api/ai/chat', methods=['POST'])
@token_required
def ai_chat(user_id):
    import random
    data         = request.get_json()
    question     = data.get('question', '').lower().strip()
    transactions = get_transactions(user_id)
    budgets      = get_budgets(user_id)

    total_income  = sum(float(t['amount']) for t in transactions if t['type'] == 'income')
    total_expense = sum(float(t['amount']) for t in transactions if t['type'] == 'expense')
    balance       = total_income - total_expense
    now = datetime.now()
    month_expense = sum(float(t['amount']) for t in transactions
                        if t['type'] == 'expense' and str(t['date']).startswith(f'{now.year}-{now.month:02d}'))
    month_income  = sum(float(t['amount']) for t in transactions
                        if t['type'] == 'income'  and str(t['date']).startswith(f'{now.year}-{now.month:02d}'))
    category_expenses = {}
    for t in transactions:
        if t['type'] == 'expense':
            cat = t['category'] or 'other'
            category_expenses[cat] = category_expenses.get(cat, 0) + float(t['amount'])
    total_budget = sum(float(b['amount']) for b in budgets) if budgets else 0

    if 'budget' in question:
        response = f"You have {len(budgets) if budgets else 0} active budgets totalling ₹{total_budget:,.2f}. This month's spending: ₹{month_expense:,.2f}."
    elif 'income' in question:
        response = f"Total income: ₹{total_income:,.2f}. This month: ₹{month_income:,.2f}."
    elif 'expense' in question or 'spend' in question:
        top = max(category_expenses, key=category_expenses.get).title() if category_expenses else 'N/A'
        response = f"Total expenses: ₹{total_expense:,.2f}. This month: ₹{month_expense:,.2f}. Top category: {top}."
    elif 'save' in question or 'saving' in question:
        savings = total_income - total_expense
        rate    = (savings / total_income * 100) if total_income > 0 else 0
        response = f"Total savings: ₹{savings:,.2f}. Savings rate: {rate:.1f}%."
    elif 'tip' in question or 'advice' in question:
        tips = [
            "Track every expense, no matter how small.",
            "Follow the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
            "Build an emergency fund covering 3-6 months of expenses.",
            "Review subscriptions regularly and cancel unused ones."
        ]
        response = f"💡 Financial Tip: {random.choice(tips)}"
    else:
        response = f"I can help with budget, income, expenses, savings, and tips. Current balance: ₹{balance:,.2f}."
    return jsonify({'response': response, 'type': 'ai_generated'})


# ==================== BUDGETS ====================

@app.route('/api/budgets', methods=['GET'])
@token_required
def list_budgets(user_id):
    return jsonify([dict(b) for b in get_budgets(user_id)])


@app.route('/api/budgets', methods=['POST'])
@token_required
def add_budget(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if not data.get('category'):
        return jsonify({'error': 'Category is required'}), 400
    if not data.get('amount'):
        return jsonify({'error': 'Amount is required'}), 400
    try:
        amount = float(data['amount'])
        if amount <= 0: raise ValueError
    except ValueError:
        return jsonify({'error': 'Amount must be a positive number'}), 400
    budget_id = create_budget(user_id=user_id, category=data['category'],
                              amount=amount, alert_threshold=data.get('alertThreshold', 80))
    if not budget_id:
        return jsonify({'error': 'Budget already exists for this category'}), 400
    return jsonify({'message': 'Budget created successfully', 'id': budget_id}), 201


@app.route('/api/budgets/<int:budget_id>', methods=['PUT'])
@token_required
def edit_budget(user_id, budget_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if update_budget(budget_id, user_id, **data):
        return jsonify({'message': 'Budget updated successfully'})
    return jsonify({'error': 'Budget not found'}), 404


@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@token_required
def remove_budget(user_id, budget_id):
    if db_delete_budget(budget_id, user_id):
        return jsonify({'message': 'Budget deleted successfully'})
    return jsonify({'error': 'Budget not found'}), 404


# ==================== RECURRING ROUTES FIX FOR app.py ====================
# Replace your existing recurring routes with these:

@app.route('/api/recurring', methods=['GET'])
@token_required
def get_all_recurring(user_id):
    return jsonify(get_recurring(user_id))


@app.route('/api/recurring', methods=['POST'])
@token_required
def create_recurring_route(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    required = ['title', 'amount', 'type', 'frequency', 'category', 'startDate']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
    if data['type'] not in ('income', 'expense'):
        return jsonify({'error': 'type must be income or expense'}), 400
    try:
        amount = float(data['amount'])
        if amount <= 0: raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'amount must be a positive number'}), 400

    new_id = create_recurring(
        user_id    = user_id,
        title      = data['title'].strip(),
        amount     = amount,
        trans_type = data['type'],
        frequency  = data['frequency'],
        category   = data['category'],
        start_date = data.get('startDate'),
        end_date   = data.get('endDate') or None,
        notes      = data.get('notes', '')
    )
    return jsonify({'id': new_id, 'message': 'Recurring created successfully'}), 201


@app.route('/api/recurring/<string:item_id>', methods=['PUT'])
@token_required
def update_recurring_route(user_id, item_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    def clean_date(val):
        if not val:
            return None
        val = str(val).strip()
        if len(val) == 10 and val[4] == '-':
            return val
        try:
            from datetime import datetime
            for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%Y-%m-%dT%H:%M:%S', '%d/%m/%Y']:
                try:
                    return datetime.strptime(val, fmt).strftime('%Y-%m-%d')
                except:
                    continue
        except:
            pass
        return None

    mapped = {}
    field_map = {
        'title':       ('title',       None),
        'amount':      ('amount',      None),
        'type':        ('type',        None),
        'frequency':   ('frequency',   None),
        'category':    ('category',    None),
        'startDate':   ('start_date',  'date'),
        'endDate':     ('end_date',    'date'),
        'notes':       ('notes',       None),
        'isActive':    ('is_active',   None),
        'last_posted': ('last_posted', 'date'),
    }

    for frontend_key, (db_key, field_type) in field_map.items():
        if frontend_key in data:
            val = data[frontend_key]
            if field_type == 'date':
                val = clean_date(val)
            mapped[db_key] = val

    if update_recurring(item_id, user_id, **mapped):
        return jsonify({'message': 'Updated successfully'})
    return jsonify({'error': 'Item not found'}), 404


@app.route('/api/recurring/<string:item_id>', methods=['DELETE'])
@token_required
def delete_recurring_route(user_id, item_id):
    if delete_recurring(item_id, user_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Item not found'}), 404
# ==================== ASSETS ====================

@app.route('/api/assets', methods=['GET'])
@token_required
def get_assets_route(user_id):
    return jsonify(get_assets(user_id))


@app.route('/api/assets', methods=['POST'])
@token_required
def add_asset(user_id):
    data = request.get_json()
    if not data or not data.get('name') or data.get('value') is None:
        return jsonify({'error': 'name and value are required'}), 400
    new_id = create_asset(user_id, data['name'].strip(), float(data['value']))
    return jsonify({'id': new_id, 'message': 'Asset created'}), 201


@app.route('/api/assets/<string:item_id>', methods=['DELETE'])
@token_required
def delete_asset_route(user_id, item_id):
    if delete_asset(item_id, user_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/liabilities', methods=['GET'])
@token_required
def get_liabilities_route(user_id):
    return jsonify(get_liabilities(user_id))


@app.route('/api/liabilities', methods=['POST'])
@token_required
def add_liability(user_id):
    data = request.get_json()
    if not data or not data.get('name') or data.get('amount') is None:
        return jsonify({'error': 'name and amount are required'}), 400
    new_id = create_liability(user_id, data['name'].strip(), float(data['amount']))
    return jsonify({'id': new_id, 'message': 'Liability created'}), 201


@app.route('/api/liabilities/<string:item_id>', methods=['DELETE'])
@token_required
def delete_liability_route(user_id, item_id):
    if delete_liability(item_id, user_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Not found'}), 404


# ==================== GOALS ====================
# FIX: Only ONE set of goal routes. Removed two duplicate implementations
#      that used session-based auth and undefined uuid import.

@app.route('/api/goals', methods=['GET'])
@token_required
def get_goals_route(user_id):
    return jsonify(get_goals(user_id))


@app.route('/api/goals', methods=['POST'])
@token_required
def create_goal_route(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    required = ['title', 'target_amount', 'target_date']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
    try:
        target_amount = float(data['target_amount'])
        current_amount = float(data.get('current_amount', 0))
        if target_amount <= 0: raise ValueError
    except (ValueError, TypeError):
        return jsonify({'error': 'target_amount must be a positive number'}), 400
    new_id = create_goal(
        user_id=user_id, title=data['title'].strip(),
        target_amount=target_amount, current_amount=current_amount,
        target_date=data['target_date'], notes=data.get('notes', '')
    )
    return jsonify({'id': new_id, 'message': 'Goal created'}), 201

@app.route('/api/goals/<string:goal_id>', methods=['PUT'])
@token_required
def update_goal_route(user_id, goal_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    # update current_amount in DB
    with get_db() as conn:
        cursor = conn.cursor()
        from database import ph
        new_amount = data.get('current_amount')
        if new_amount is None:
            return jsonify({'error': 'current_amount required'}), 400
        cursor.execute(
            f'UPDATE goals SET current_amount = {ph()} WHERE id = {ph()} AND user_id = {ph()}',
            (float(new_amount), goal_id, user_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'Goal not found'}), 404
    return jsonify({'message': 'Goal updated'})


@app.route('/api/goals/<string:goal_id>', methods=['DELETE'])
@token_required
def delete_goal_route(user_id, goal_id):
    if delete_goal(goal_id, user_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Goal not found'}), 404


# ==================== PROFILE ====================

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(user_id):
    user = get_user_by_id(user_id)
    return jsonify({'id': user['id'], 'name': user['name'], 'email': user['email'],
                    'phone': user.get('phone', ''), 'avatar': user['avatar'],
                    'role': user['role'], 'created_at': user['created_at']})


@app.route('/api/profile', methods=['PUT'])
@token_required
def update_profile(user_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if update_user(user_id, **data):
        return jsonify({'message': 'Profile updated successfully'})
    return jsonify({'error': 'Failed to update profile'}), 500


@app.route('/api/profile/avatar', methods=['POST'])
@token_required
def upload_avatar(user_id):
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['avatar']
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    avatar_url = f"data:{file.content_type};base64,{base64.b64encode(file.read()).decode('utf-8')}"
    update_user(user_id, avatar=avatar_url)
    return jsonify({'message': 'Avatar uploaded successfully', 'avatar': avatar_url})


@app.route('/api/profile/avatar', methods=['DELETE'])
@token_required
def remove_avatar(user_id):
    update_user(user_id, avatar=None)
    return jsonify({'message': 'Avatar removed successfully'})


@app.route('/api/profile/password', methods=['PUT'])
@token_required
def change_password(user_id):
    import hashlib
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    user = get_user_by_id(user_id)
    if not verify_password(user['email'], data.get('currentPassword')):
        return jsonify({'error': 'Current password is incorrect'}), 400
    if len(data.get('newPassword', '')) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    password_hash = hashlib.sha256(data['newPassword'].encode()).hexdigest()
    update_password(user_id, password_hash)
    return jsonify({'message': 'Password changed successfully'})

# ==================== ADMIN ====================

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def admin_stats(user_id):
    return jsonify(get_admin_stats())


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def admin_users(user_id):
    return jsonify([dict(u) for u in get_all_users()])


@app.route('/api/admin/users', methods=['POST'])
@admin_required
def admin_create_user(user_id):
    data = request.get_json()
    if not data or not all([data.get('email'), data.get('password'), data.get('name')]):
        return jsonify({'error': 'Name, email and password are required'}), 400
    if get_user_by_email(data['email']):
        return jsonify({'error': 'Email already registered'}), 400
    role   = data.get('role', 'user') if data.get('role') in ['user', 'admin'] else 'user'
    new_id = create_user(name=data['name'].strip(), email=data['email'].strip().lower(),
                         password=data['password'], phone=data.get('phone', ''), role=role)
    if not new_id:
        return jsonify({'error': 'Failed to create user'}), 500
    save_user_to_csv({'name': data['name'].strip(), 'email': data['email'].strip().lower(),
                      'phone': data.get('phone', ''), 'role': role, 'status': 'active'})
    return jsonify({'message': f'{role.capitalize()} created successfully', 'id': new_id}), 201


@app.route('/api/admin/users/<int:target_user_id>', methods=['PUT'])
@admin_required
def admin_update_user(user_id, target_user_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    target_user = get_user_by_id(target_user_id)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    if target_user['role'] == 'admin':
        if data.get('status') and data['status'] != 'active':
            return jsonify({'error': 'Admin users cannot be deactivated'}), 403
        if data.get('role') and data['role'] != 'admin':
            return jsonify({'error': 'Admin role cannot be changed'}), 403
    if 'status' in data:
        ok, msg = update_user_status(target_user_id, data['status'])
        if not ok: return jsonify({'error': msg}), 403
    if 'role' in data and target_user['role'] != 'admin':
        ok, msg = update_user_role(target_user_id, data['role'])
        if not ok: return jsonify({'error': msg}), 403
    return jsonify({'message': 'User updated successfully'})


@app.route('/api/admin/users/<int:target_user_id>', methods=['DELETE'])
@admin_required
def admin_delete_user(user_id, target_user_id):
    if target_user_id == user_id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    target_user = get_user_by_id(target_user_id)
    if not target_user:
        return jsonify({'error': 'User not found'}), 404
    if target_user['role'] == 'admin':
        return jsonify({'error': 'Admin users cannot be deleted'}), 403
    ok, msg = delete_user(target_user_id)
    if ok: return jsonify({'message': msg})
    return jsonify({'error': msg}), 500


@app.route('/api/admin/admins', methods=['GET'])
@admin_required
def admin_list_admins(user_id):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, status, created_at FROM users WHERE role = 'admin'")
        return jsonify([dict(a) for a in cursor.fetchall()])


@app.route('/api/admin/export-users', methods=['GET'])
@admin_required
def export_users(user_id):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Name', 'Email', 'Phone', 'Role', 'Status'])
    for u in get_all_users():
        writer.writerow([u['created_at'], u['name'], u['email'],
                         u.get('phone', ''), u['role'], u['status']])
    output.seek(0)
    return Response('\ufeff' + output.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={'Content-Disposition':
                             f'attachment; filename=trakn-users-{datetime.now().strftime("%Y-%m-%d")}.csv'})


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== STARTUP ====================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("   TRAKN - Personal Expense Tracker")
    print("="*60)
    init_db()
    create_default_admin()
    print("\n  Server: http://localhost:5000")
    print("  Admin:  admin@trakn.com / admin123")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)