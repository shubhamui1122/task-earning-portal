from flask import Flask, render_template_string, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_key_task_portal'

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    # UTR / Deposits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            utr TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# HTML Templates
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <title>Task Earning Portal</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f9; margin: 0; padding: 20px; }
        .container { max-width: 600px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin: auto; }
        h2 { color: #333; }
        .btn { display: inline-block; padding: 10px 15px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 5px 0; }
        .btn-danger { background: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Task Earning Portal</h2>
        {% if session.get('user') %}
            <p>लॉगिन यूजर: <b>{{ session['user'] }}</b> | आपका बैलेंस: ₹{{ balance }}</p>
            {% if session.get('is_admin') %}
                <a href="/admin" class="btn" style="background: #28a745;">🛡️ एडमिन पैनल खोलें</a>
            {% endif %}
            <br><br>
            <a href="/deposit" class="btn">पेमेंट / UTR जमा करें</a>
            <a href="/logout" class="btn btn-danger">लॉग आउट</a>
        {% else %}
            <p>कृपया पहले लॉगिन करें।</p>
            <a href="/login" class="btn">लॉगिन करें</a>
            <a href="/register" class="btn" style="background: #28a745;">नया खाता बनाएँ</a>
        {% endif %}
    </div>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <title>लॉगिन - Task Earning Portal</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f9; padding: 50px; }
        .box { max-width: 400px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin: auto; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="box">
        <h2>लॉगिन करें</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <p style="color: red;">{{ messages[0] }}</p>
          {% endif %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="username" placeholder="यूजरनेम" required>
            <input type="password" name="password" placeholder="पासवर्ड" required>
            <button type="submit">लॉगिन</button>
        </form>
        <p>नया खाता बनाना है? <a href="/register">रजिस्टर करें</a></p>
    </div>
</body>
</html>
'''

ADMIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <title>एडमिन पैनल</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f9; padding: 20px; }
        .container { max-width: 800px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin: auto; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #007bff; color: white; }
        input, select { padding: 6px; margin: 5px 0; }
        .btn { padding: 8px 12px; background: #28a745; color: white; border: none; cursor: pointer; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🛡️ एडमिन कंट्रोल पैनल</h2>
        <a href="/" style="text-decoration: none; color: #007bff;">&larr; होम पेज पर जाएं</a>
        
        <hr>
        <h3>💰 यूजर बैलेंस अपडेट करें (जोड़ें या काटें)</h3>
        <form method="POST" action="/admin/update_balance">
            <input type="text" name="username" placeholder="यूजरनेम डालें" required>
            <input type="number" step="0.01" name="amount" placeholder="राशि (₹)" required>
            <select name="action">
                <option value="add">बैलेंस जोड़ें (+)</option>
                <option value="deduct">बैलेंस काटें (-)</option>
            </select>
            <button type="submit" class="btn">बदलाव लागू करें</button>
        </form>

        <hr>
        <h3>📋 पेंडिंग UTR / पेमेंट अनुरोध</h3>
        <table>
            <tr>
                <th>ID</th>
                <th>यूजर</th>
                <th>UTR नंबर</th>
                <th>राशि</th>
                <th>स्थिति</th>
                <th>कारवाई</th>
            </tr>
            {% for dep in deposits %}
            <tr>
                <td>{{ dep[0] }}</td>
                <td>{{ dep[1] }}</td>
                <td>{{ dep[2] }}</td>
                <td>₹{{ dep[3] }}</td>
                <td>{{ dep[4] }}</td>
                <td>
                    {% if dep[4] == 'Pending' %}
                        <a href="/admin/approve/{{ dep[0] }}" style="color: green; font-weight: bold;">मंजूर करें</a>
                    {% else %}
                        {{ dep[4] }}
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    balance = 0.0
    if 'user' in session:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username = ?", (session['user'],))
        row = cursor.fetchone()
        if row:
            balance = row[0]
        conn.close()
    return render_template_string(INDEX_TEMPLATE, balance=balance)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Custom Admin Credentials Check
        if username == 'ADMINSHUBHAM11' and password == 'ADMINHUMAIN':
            session['user'] = 'ADMINSHUBHAM11'
            session['is_admin'] = True
            return redirect(url_for('admin_panel'))
            
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user'] = user[1]
            session['is_admin'] = bool(user[4])
            return redirect(url_for('home'))
        else:
            flash('गलत यूजरनेम या पासवर्ड!')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, balance, is_admin) VALUES (?, ?, 0.0, 0)", (username, password))
            conn.commit()
            conn.close()
            flash('रजिस्ट्रेशन सफल! अब लॉगिन करें।')
            return redirect(url_for('login'))
        except:
            conn.close()
            flash('यह यूजरनेम पहले से मौजूद है!')
    return render_template_string('''
    <div style="max-width:400px; margin:50px auto; font-family:Arial;">
        <h2>नया खाता बनाएँ</h2>
        {% with messages = get_flashed_messages() %}{% if messages %}<p style="color:red;">{{ messages[0] }}</p>{% endif %}{% endwith %}
        <form method="POST">
            <input type="text" name="username" placeholder="यूजरनेम" required style="width:100%; padding:10px; margin:10px 0;"><br>
            <input type="password" name="password" placeholder="पासवर्ड" required style="width:100%; padding:10px; margin:10px 0;"><br>
            <button type="submit" style="width:100%; padding:10px; background:#28a745; color:white; border:none; cursor:pointer;">रजिस्टर</button>
        </form>
        <p>खाता है? <a href="/login">लॉगिन करें</a></p>
    </div>
    ''')

@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, utr, amount, status FROM deposits")
    deposits = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, deposits=deposits)

@app.route('/admin/update_balance', methods=['POST'])
def update_balance():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    username = request.form['username']
    amount = float(request.form['amount'])
    action = request.form['action']
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if action == 'add':
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, username))
    else:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username = ?", (amount, username))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/approve/<int:dep_id>')
def approve_dep(dep_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, amount FROM deposits WHERE id = ? AND status = 'Pending'", (dep_id,))
    dep = cursor.fetchone()
    if dep:
        username, amount = dep
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username = ?", (amount, username))
        cursor.execute("UPDATE deposits SET status = 'Approved' WHERE id = ?", (dep_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        utr = request.form['utr']
        amount = float(request.form['amount'])
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO deposits (username, utr, amount, status) VALUES (?, ?, ?, 'Pending')", (session['user'], utr, amount))
        conn.commit()
        conn.close()
        return "<h3>UTR सफलताಪूर्वक जमा हो गया है!</h3><a href='/'>होम जाएं</a>"
    return '''
    <div style="max-width:400px; margin:50px auto; font-family:Arial;">
        <h2>UTR और पेमेंट जमा करें</h2>
        <form method="POST">
            <input type="text" name="utr" placeholder="UTR / ट्रांजैक्शन आईडी" required style="width:100%; padding:10px; margin:10px 0;"><br>
            <input type="number" step="0.01" name="amount" placeholder="राशि (₹)" required style="width:100%; padding:10px; margin:10px 0;"><br>
            <button type="submit" style="width:100%; padding:10px; background:#007bff; color:white; border:none; cursor:pointer;">सबमिट करें</button>
        </form>
        <a href="/">वापस जाएं</a>
    </div>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

