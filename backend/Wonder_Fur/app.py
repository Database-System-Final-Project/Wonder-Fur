from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import mysql.connector
from pymongo import MongoClient
from folium.plugins import LocateControl
from werkzeug.security import generate_password_hash, check_password_hash
import folium
from datetime import datetime  # 新增

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'zhen41171119H',
    'database': 'Wonder_fur'
}

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client["DB_Final_Project"]
favorites_collection = db["user_favorites"]  

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, hashed_password)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('register.html')

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
                flash(f'Welcome back, {user["username"]}!', 'success')
                # return redirect(url_for('surf'))
                return redirect(url_for('map_view'))
            else:
                flash('Login failed. Please check your email and password.', 'danger')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'danger')
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

    return render_template('index.html')

@app.route('/modify', methods=['GET', 'POST'])
def modify():
    if 'user_id' not in session:
        flash('Please log in to modify your account.', 'warning')
        return redirect(url_for('login'))
    return render_template('modify.html')

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        flash('Please log in to update your password.', 'warning')
        return redirect(url_for('login'))

    current_password = request.form['current_password']
    new_password = request.form['new_password']

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], current_password):
            hashed_password = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, session['user_id']))
            conn.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('index'))  # 修改成功後跳轉到首頁
        else:
            flash('Current password is incorrect.', 'danger')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    return redirect(url_for('modify'))  # 修改失敗回到修改頁面


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash('Please log in to delete your account.', 'warning')
        return redirect(url_for('login'))

    password = request.form['password']

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            cursor.execute("DELETE FROM users WHERE id = %s", (session['user_id'],))
            conn.commit()
            session.clear()  # 清空會話
            flash('Account deleted successfully.', 'success')
            return redirect(url_for('index'))  # 刪除成功後跳轉到首頁
        else:
            flash('Password is incorrect.', 'danger')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

    return redirect(url_for('modify'))  # 刪除失敗回到修改頁面



@app.route('/surf')
def surf():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    return render_template('surf.html')



@app.route('/map')
def map_view():
    # Initialize the map
    map_osm = folium.Map(location=[25.033964, 121.564468], zoom_start=14)

    # Fetch park data from MongoDB
    park_collection = db["park_location"]
    park_data = list(park_collection.find({}, {"_id": 0, "Park Name": 1, "address": 1, "latitude": 1, "longitude": 1, "Opening hours": 1}))

    park_layer = folium.FeatureGroup(name="公園地圖")
    for item in park_data:
        try:
            folium.Marker(
                location=[float(item["latitude"]), float(item["longitude"])],
                popup=(f"<b>公園名稱:</b> {item['Park Name']}<br>"
                       f"<b>地址:</b> {item['address']}<br>"
                       f"<b>營業時間:</b> {item['Opening hours']}<br>"
                       f"<button onclick=\"saveFavorite('{item['Park Name']}', '{item['address']}')\">收藏</button>"),
                tooltip=item["Park Name"],
                icon=folium.Icon(color="green", icon="tree")
            ).add_to(park_layer)
        except (ValueError, TypeError):
            print(f"跳過無效公園資料: {item}")
    park_layer.add_to(map_osm)

    # ------ 寵物醫院地圖圖層 ------
    hospital_collection = db["petHospital_location"]
    hospital_data = list(hospital_collection.find({}, {"_id": 0, "name": 1, "contact phone": 1, "address": 1, "latitude": 1, "longitude": 1}))

    hospital_layer = folium.FeatureGroup(name="寵物醫院地圖")
    for item in hospital_data:
        try:
            folium.Marker(
                location=[float(item["latitude"]), float(item["longitude"])],
                popup=(f"<b>醫院名稱:</b> {item['name']}<br>"
                       f"<b>聯絡電話:</b> {item['contact phone']}<br>"
                       f"<b>地址:</b> {item['address']}<br>"
                       f"<button onclick=\"saveFavorite('{item['name']}', '{item['address']}')\">收藏</button>"),
                tooltip=item["name"],
                icon=folium.Icon(color="red", icon="heartbeat")
            ).add_to(hospital_layer)
        except (ValueError, TypeError):
            print(f"跳過無效寵物醫院資料: {item}")
    hospital_layer.add_to(map_osm)

    # ------ 垃圾桶地圖圖層 ------
    trashcan_collection = db["trashcan_location"]
    trashcan_data = list(trashcan_collection.find({}, {"_id": 0, "address": 1, "latitude": 1, "longitude": 1}))

    trashcan_layer = folium.FeatureGroup(name="垃圾桶地圖")
    for item in trashcan_data:
        try:
            folium.Marker(
                location=[float(item["latitude"]), float(item["longitude"])],
                popup=(f"<b>地址:</b> {item['address']}<br>"
                       f"<button onclick=\"saveFavorite('垃圾桶', '{item['address']}')\">收藏</button>"),
                tooltip="垃圾桶位置",
                icon=folium.Icon(color="blue", icon="trash")
            ).add_to(trashcan_layer)
        except (ValueError, TypeError):
            print(f"跳過無效垃圾桶資料: {item}")
    trashcan_layer.add_to(map_osm)

    # ------ 餐廳地圖圖層 ------
    restaurant_collection = db["restaurant_location"]
    restaurant_data = list(restaurant_collection.find({}, {"_id": 0, "Type": 1, "Restaurant Name": 1, "Address": 1, "Business Hours": 1, "Features": 1, "latitude": 1, "longitude": 1}))

    restaurant_layer = folium.FeatureGroup(name="餐廳地圖")
    for item in restaurant_data:
        try:
            folium.Marker(
                location=[float(item["latitude"]), float(item["longitude"])],
                popup=(f"<b>餐廳名稱:</b> {item['Restaurant Name']}<br>"
                       f"<b>地址:</b> {item['Address']}<br>"
                       f"<b>類型:</b> {item['Type']}<br>"
                       f"<b>營業時間:</b> {item['Business Hours']}<br>"
                       f"<b>特色:</b> {item['Features']}<br>"
                       f"<button onclick=\"saveFavorite('{item['Restaurant Name']}', '{item['Address']}')\">收藏</button>"),
                tooltip=item["Restaurant Name"],
                icon=folium.Icon(color="orange", icon="cutlery")
            ).add_to(restaurant_layer)
        except (ValueError, TypeError):
            print(f"跳過無效餐廳資料: {item}")
    restaurant_layer.add_to(map_osm)

    # Add layer controls and locate control
    folium.LayerControl().add_to(map_osm)
    LocateControl().add_to(map_osm)

    # Render the map as HTML
    map_html = map_osm._repr_html_()

    # Check login status
    is_logged_in = 'user_id' in session

    return render_template('map.html', map_html=map_html, is_logged_in=is_logged_in)

@app.route('/save_favorite', methods=['POST'])
def save_favorite():
    if 'user_id' not in session:
        return jsonify({'status': 'redirect', 'message': 'Please log in to save favorites.', 'url': url_for('login')})
    
    data = request.json
    user_id = session['user_id']

    # 驗證必需字段
    required_fields = ['category', 'name', 'address', 'latitude', 'longitude']
    if not all(field in data for field in required_fields):
        return jsonify({'status': 'error', 'message': 'Missing required fields'})

    # 插入收藏地點到 MongoDB
    favorite = {
        "user_id": user_id,
        "category": data["category"],
        "name": data["name"],
        "address": data["address"],
        "latitude": float(data["latitude"]),
        "longitude": float(data["longitude"]),
        "extra": data.get("extra"),  # 可選字段
        "created_at": datetime.now()  # 新增
    }

    try:
        favorites_collection.insert_one(favorite)  # 插入數據
        return jsonify({'status': 'success', 'message': 'Favorite saved successfully!'})
    except Exception as err:
        return jsonify({'status': 'error', 'message': str(err)})

#@app.route('/introduce')
#def introduce():
#    return render_template('introduce.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
