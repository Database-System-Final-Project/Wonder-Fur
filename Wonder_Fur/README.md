#### Project Overview
**Wonder Fur** is a pet-friendly web application designed to help users locate pet-friendly parks, hospitals, restaurants, and trashcans. Users can register, log in, and save favorite locations, all managed seamlessly through an intuitive interface.

---

#### File Structure
```
.
├── app.py
├── static/
│   ├── image/
│   │   ├── back.png
│   │   ├── logo.png
│   │   └── logo_white.png
├── templates/
│   ├── add_favorites.html
│   ├── index.html
│   ├── login.html
│   ├── map.html
│   ├── modify.html
│   └── register.html
```

- **`app.py`**  
  The main application file. Implements backend functionality using **Flask**:
  - User management: Registration, login, password modification, and account deletion.
  - Interactive map functionality using **Folium**.
  - Integration with **MySQL** for user authentication and **MongoDB** for location storage.

- **Static Files**:
  - **`image/back.png`**: Background image.
  - **`image/logo.png`** and **`image/logo_white.png`**: Logo images for branding.

- **Templates**:
  - **`index.html`**: Home page and login form.
  - **`register.html`**: User registration form.
  - **`login.html`**: User login page.
  - **`map.html`**: Displays the interactive map with markers and favorite buttons.
  - **`modify.html`**: User account modification page.
  - **`add_favorites.html`**: Page for managing favorite locations.

---

#### Database Usage
1. **MySQL**:  
   - User credentials and account management.
   - Table: `users` with fields (`id`, `username`, `email`, `password`).

2. **MongoDB**:  
   - Stores geospatial location data for:
     - Parks
     - Pet hospitals
     - Restaurants
     - Trashcans
   - User favorites are saved in the `user_favorites` collection.

---

#### Getting Started
**Run the Application**:
   - Start the Flask server:  
     ```bash
     python app.py
     ```
   - Access the app at `http://127.0.0.1:5000`.

---

Enjoy using Wonder Fur to explore pet-friendly locations and organize your favorites!
