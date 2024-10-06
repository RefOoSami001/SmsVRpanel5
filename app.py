import sqlite3
import requests
import json
from flask import Flask, request, render_template, redirect, url_for, session, flash
from datetime import datetime
import re
app = Flask(__name__)
app.secret_key = 'refooSami'  # Secret key for session management

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        number TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (username) REFERENCES users(username)
                        UNIQUE(username, number, status)
                    )''')
    conn.commit()
    conn.close()

# Add a new user to the SQLite database
def add_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        flash('User already exists', 'danger')
    finally:
        conn.close()
# Remove a user from the SQLite database
def remove_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    cursor.execute('DELETE FROM user_data WHERE username = ?', (username,))
    conn.commit()
    conn.close()
# Authenticate user credentials
def authenticate_user(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Add data for a specific user
def add_user_data(username, number, status):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO user_data (username, number, status) VALUES (?, ?, ?)', (username, number, status))
    conn.commit()
    conn.close()

# Retrieve user data for a specific user
def get_user_data(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_data WHERE username = ?', (username,))
    data = cursor.fetchall()
    conn.close()
    return data
# Retrieve user data by number
def get_number_data(numbers):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in numbers)
    query = f'SELECT username, number, status, timestamp FROM user_data WHERE number IN ({placeholders})'
    cursor.execute(query, numbers)
    data = cursor.fetchall()
    conn.close()
    return data
@app.route('/manage_users', methods=['GET', 'POST'])
def add_user_route():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        action = request.form.get('action', '').strip()
        
        # Validate input fields
        if not username:
            flash('Username is required.', 'danger')
        elif action == 'add':
            if not password:
                flash('Password is required for adding a user.', 'danger')
            else:
                try:
                    add_user(username, password)
                    flash('User added successfully', 'success')
                except Exception as e:
                    flash(f'An error occurred: {str(e)}', 'danger')
        elif action == 'remove':
            try:
                remove_user(username)
                flash('User removed successfully', 'success')
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'danger')
        else:
            flash('Invalid action specified.', 'danger')

    return render_template('add_user.html')

@app.route('/search_user', methods=['GET', 'POST'])
def search_user():
    if request.method == 'POST':
        search_type = request.form.get('search_type', '').strip()
        search_value = request.form.get('search_value', '').strip()

        if search_type == 'username':
            user_data = get_user_data(search_value)
            if user_data:
                total_success = sum(1 for entry in user_data if entry[3] != 'Failed')
                total_failed = sum(1 for entry in user_data if entry[3] == 'Failed')

                return render_template(
                    'user_data.html',
                    user_data=user_data,
                    search_type='username',
                    search_value=search_value,
                    total_success=total_success,
                    total_failed=total_failed
                )
            else:
                flash('No data found for the user', 'danger')

        elif search_type == 'number':
            # Allow multiple numbers, split by comma or space
            numbers = re.split(r'[,\s]+', search_value)
            number_data = get_number_data(numbers)
            if number_data:
                total_success = sum(1 for entry in number_data if entry[2] != 'Failed')
                total_failed = sum(1 for entry in number_data if entry[2] == 'Failed')

                return render_template(
                    'user_data.html',
                    number_data=number_data,
                    search_type='number',
                    search_value=search_value,
                    total_success=total_success,
                    total_failed=total_failed
                )
            else:
                flash('No data found for these numbers', 'danger')

    return render_template('user_data.html')





# Root route redirects to login
@app.route('/')
def index():
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate_user(username, password)
        if user:
            
            session['user'] = username
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful', 'success')
            return redirect(url_for('verification_code_finder'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# Verification code finder route
@app.route('/verification_code_finder', methods=['GET', 'POST'])
def verification_code_finder():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if 'user' in session:
        if request.method == 'POST':
            numbers = request.form['numbers'].split()

            total_success = 0
            total_fail = 0
            codes = {}

            for number in numbers:
                code = get_panel_code(number)
                status = 'Failed'
                if code:
                    total_success += 1
                    status = code
                else:
                    total_fail += 1

                codes[number] = status
                add_user_data(session['user'], number, status)  # Save data to database

            results = {
                'total_success': total_success,
                'total_fail': total_fail,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'codes': codes
            }
            return render_template('verification.html', results=results)
        return render_template('verification.html')
    else:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))



def get_panel_code(number):
    cookies = {
        'PHPSESSID': 'j2amq0mh5848v110nk4imef651',
    }

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        # 'Cookie': 'PHPSESSID=j2amq0mh5848v110nk4imef651',
        'Referer': 'http://zodiacpanel.com/agent/SMSCDRStats',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }


    response = requests.get(
        f'http://zodiacpanel.com/agent/res/data_smscdr.php?fdate1=2024-10-06%2000:00:00&fdate2=2024-10-06%2023:59:59&frange=&fclient=&fnum={number}&fcli=&fgdate=&fgmonth=&fgrange=&fgclient=&fgnumber=&fgcli=&fg=0&sEcho=1&iColumns=9&sColumns=%2C%2C%2C%2C%2C%2C%2C%2C&iDisplayStart=0&iDisplayLength=25&mDataProp_0=0&sSearch_0=&bRegex_0=false&bSearchable_0=true&bSortable_0=true&mDataProp_1=1&sSearch_1=&bRegex_1=false&bSearchable_1=true&bSortable_1=true&mDataProp_2=2&sSearch_2=&bRegex_2=false&bSearchable_2=true&bSortable_2=true&mDataProp_3=3&sSearch_3=&bRegex_3=false&bSearchable_3=true&bSortable_3=true&mDataProp_4=4&sSearch_4=&bRegex_4=false&bSearchable_4=true&bSortable_4=true&mDataProp_5=5&sSearch_5=&bRegex_5=false&bSearchable_5=true&bSortable_5=true&mDataProp_6=6&sSearch_6=&bRegex_6=false&bSearchable_6=true&bSortable_6=true&mDataProp_7=7&sSearch_7=&bRegex_7=false&bSearchable_7=true&bSortable_7=true&mDataProp_8=8&sSearch_8=&bRegex_8=false&bSearchable_8=true&bSortable_8=false&sSearch=&bRegex=false&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1&_=1728219621497',
        cookies=cookies,
        headers=headers,
        verify=False,
    )
    try:
        data = json.loads(response.text)

        # Extract the message
        message_text = data['aaData'][0][5]

        verification_code = re.search(r'\d+', message_text)
            
        if verification_code:
            return verification_code.group()
        else:
            return None
    except:
        return None
if __name__ == '__main__':
    init_db()
    app.run(debug=False)