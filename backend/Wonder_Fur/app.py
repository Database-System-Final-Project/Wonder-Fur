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

    park_layer = folium.FeatureGroup(name="Park")
    for item in park_data:
        try:
            folium.Marker(
                location=[float(item["latitude"]), float(item["longitude"])],
                tooltip=item["Park Name"],
                icon=folium.Icon(color="green", icon="tree"),
                popup=(f"<b>Park Name:</b> {item['Park Name']}<br>"
                       f"<b>Address:</b> {item['address']}<br>"
                       f"<b>Opening Hours:</b> {item['Opening hours']}<br>")
            ).add_to(park_layer)
        except (ValueError, TypeError):
            print(f"Skipping invalid park data: {item}")
    park_layer.add_to(map_osm)

    # Pet Hospital layer
    hospital_collection = db["petHospital_location"]
    hospital_data = list(hospital_collection.find({}, {"_id": 0, "name": 1, "contact phone": 1, "address": 1, "latitude": 1, "longitude": 1}))

    hospital_layer = folium.FeatureGroup(name="Pet Hospital")
    for item in hospital_data:
        try:
            folium.Marker(
                location=[float(item["latitude"]), float(item["longitude"])],
                tooltip=item["name"],
                icon=folium.Icon(color="red", icon="heartbeat"),
                popup=(f"<b>Hospital Name:</b> {item['name']}<br>"
                       f"<b>Contact Phone:</b> {item['contact phone']}<br>"
                       f"<b>Address:</b> {item['address']}<br>")
            ).add_to(hospital_layer)
        except (ValueError, TypeError):
            print(f"Skipping invalid hospital data: {item}")
    hospital_layer.add_to(map_osm)

    # Trashcan layer
    trashcan_collection = db["trashcan_location"]
    trashcan_data = list(trashcan_collection.find({}, {"_id": 0, "address": 1, "latitude": 1, "longitude": 1}))

    trashcan_layer = folium.FeatureGroup(name="Trashcan")
    for item in trashcan_data:
        try:
            folium.Marker(
                location=[float(item["latitude"]), float(item["longitude"])],
                tooltip="Trashcan Location",
                icon=folium.Icon(color="blue", icon="trash"),
                popup=(f"<b>Address:</b> {item['address']}<br>")
            ).add_to(trashcan_layer)
        except (ValueError, TypeError):
            print(f"Skipping invalid trashcan data: {item}")
    trashcan_layer.add_to(map_osm)

    # Restaurant layer
    restaurant_collection = db["restaurant_location"]
    restaurant_data = list(restaurant_collection.find({}, {"_id": 0, "Type": 1, "Restaurant Name": 1, "Address": 1, "Business Hours": 1, "Features": 1, "latitude": 1, "longitude": 1}))

    restaurant_layer = folium.FeatureGroup(name="Restaurant")
    for item in restaurant_data:
        try:
            folium.Marker(
                location=[float(item["latitude"]), float(item["longitude"])],
                tooltip=item["Restaurant Name"],
                icon=folium.Icon(color="orange", icon="cutlery"),
                popup=(f"<b>Restaurant Name:</b> {item['Restaurant Name']}<br>"
                       f"<b>Address:</b> {item['Address']}<br>"
                       f"<b>Type:</b> {item['Type']}<br>"
                       f"<b>Business Hours:</b> {item['Business Hours']}<br>"
                       f"<b>Features:</b> {item['Features']}<br>")
            ).add_to(restaurant_layer)
        except (ValueError, TypeError):
            print(f"Skipping invalid restaurant data: {item}")
    restaurant_layer.add_to(map_osm)

    # Add layer controls and locate control
    folium.LayerControl().add_to(map_osm)
    LocateControl().add_to(map_osm)

    # Render the map as HTML
    map_html = map_osm._repr_html_()

    return render_template('map.html', map_html=map_html)


'''
@app.route('/marker_info', methods=['GET'])
def marker_info():
    # API to return marker details
    category = request.args.get('category')
    name = request.args.get('name')
    address = request.args.get('address')
    latitude = request.args.get('latitude')
    longitude = request.args.get('longitude')

    return jsonify({
        'category': category,
        'name': name,
        'address': address,
        'latitude': latitude,
        'longitude': longitude
    })
'''

#@app.route('/introduce')
#def introduce():
#    return render_template('introduce.html')

@app.route('/favorites')
def favorites_view():
    if 'user_id' not in session:
        flash('Please log in to view your favorites.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']
    favorites = list(favorites_collection.find({"user_id": user_id}))  # 將 Cursor 轉為清單

    return render_template('add_favorites.html', favorites=favorites)

@app.route('/search_favorites', methods=['POST'])
def search_favorites():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in to search.'})

    data = request.json
    query = data.get('query', '').strip()

    if not query:
        return jsonify({'status': 'error', 'message': 'Query cannot be empty.'})

    try:
        # 查詢 MongoDB 地址數據
        mongo_results = []

        # 公園查詢
        park_results = db["park_location"].find(
            {"$or": [
                {"Park Name": {"$regex": query, "$options": "i"}},
                {"address": {"$regex": query, "$options": "i"}}
            ]},
            {"_id": 0, "Park Name": 1, "address": 1, "longitude": 1, "latitude": 1, "Opening hours": 1}
        )
        mongo_results.extend([{
            "category": "Park",
            "name": item["Park Name"],
            "address": item["address"],
            "longitude": item["longitude"],
            "latitude": item["latitude"],
            "extra": {"Opening hours": item.get("Opening hours", "N/A")}
        } for item in park_results])

        # 寵物醫院查詢
        hospital_results = db["petHospital_location"].find(
            {"$or": [{"name": {"$regex": query, "$options": "i"}}, {"address": {"$regex": query, "$options": "i"}}]},
            {"_id": 0, "name": 1, "address": 1, "longitude": 1, "latitude": 1, "contact phone": 1}
        )
        mongo_results.extend([{
            "category": "Pet Hospital",
            "name": item["name"],
            "address": item["address"],
            "longitude": item["longitude"],
            "latitude": item["latitude"],
            "extra": {"contact phone": item.get("contact phone", "N/A")}
        } for item in hospital_results])

        # 餐廳查詢
        restaurant_results = db["restaurant_location"].find(
            {"$or": [{"Restaurant Name": {"$regex": query, "$options": "i"}}, {"Address": {"$regex": query, "$options": "i"}}]},
            {"_id": 0, "Restaurant Name": 1, "Address": 1, "longitude": 1, "latitude": 1, "Type": 1, "Business Hours": 1, "Features": 1}
        )
        mongo_results.extend([{
            "category": "Restaurant",
            "name": item["Restaurant Name"],
            "address": item["Address"],
            "longitude": item["longitude"],
            "latitude": item["latitude"],
            "extra": {
                "Type": item.get("Type", "N/A"),
                "Business Hours": item.get("Business Hours", "N/A"),
                "Features": item.get("Features", "N/A")
            }
        } for item in restaurant_results])

        # 垃圾桶查詢
        trashcan_results = db["trashcan_location"].find(
            {"address": {"$regex": query, "$options": "i"}},
            {"_id": 0, "address": 1, "longitude": 1, "latitude": 1}
        )
        mongo_results.extend([{
            "category": "Trashcan",
            "name": "Trashcan",
            "address": item["address"],
            "longitude": item["longitude"],
            "latitude": item["latitude"]
        } for item in trashcan_results])

        # 返回結果
        return jsonify({'status': 'success', 'results': mongo_results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please log in to add favorites.'})

    data = request.json
    name = data.get('name')
    address = data.get('address')

    if not name or not address:
        return jsonify({'status': 'error', 'message': 'Name and address are required.'})

    user_id = session['user_id']
    try:
        # 插入到 MongoDB 的收藏集合
        favorite = {
            "user_id": user_id,
            "name": name,
            "address": address,
            "created_at": datetime.now()
        }
        favorites_collection.insert_one(favorite)
        return jsonify({'status': 'success', 'message': 'Favorite added successfully!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    


if __name__ == '__main__':
    app.run(debug=True)
