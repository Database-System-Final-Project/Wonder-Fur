from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# 資料庫連線設定
db_config = {
    'host': 'localhost',
    'user': 'root',  # 替換為您的 MySQL 使用者名稱
    'password': '',  # 替換為您的 MySQL 密碼
    'database': 'Wonder_fur'
}

# 註冊頁面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # 加密密碼
        hashed_password = generate_password_hash(password)

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            conn.commit()
            flash('Register successfully！Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'error：{err}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('register.html')

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash(f'Welcome back :), {user["username"]}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Fail to log in, please check your input.', 'danger')
        except mysql.connector.Error as err:
            flash(f'error:{err}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('login.html')

# 首頁 index.thml
@app.route('/')
def index():
    if 'user_id' not in session:
        flash('Please log in.', 'warning')
        return redirect(url_for('login'))

    return render_template('index.html', username=session['username'])

# 登出
@app.route('/logout')
def logout():
    session.clear()
    flash('You have logged out successful, glad to see yo soon :)', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
