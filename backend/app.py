from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
from werkzeug.utils import secure_filename
import subprocess
from pathlib import Path
from zipfile import ZipFile
from tqdm import tqdm
import threading

app = Flask(__name__)
CORS(app)  # Allow CORS for your React frontend

# Configure file upload settings
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'rar', 'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database helper function
def get_db_connection():
    conn = sqlite3.connect("my_database.db", timeout=10)  # Increase timeout to 10 seconds
    conn.row_factory = sqlite3.Row
    return conn


# Function to check if file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Modify the database schema
def create_file_table():
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# Create the file table (if not created)
create_file_table()

@app.route("/api/users", methods=["GET"])
def get_users():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

@app.route("/api/register", methods=["POST"])
def register_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Invalid input"}), 400

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

    return jsonify({"message": "User registered successfully"}), 201

# api - login
@app.route("/api/login", methods=["POST"])
def login_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
    ).fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401

# File upload route
def get_db_connection():
    conn = sqlite3.connect("my_database.db", timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    # print(file)
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_type = file.mimetype
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Use context manager to ensure the connection is properly handled
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO files (filename, file_path, file_type) VALUES (?, ?, ?)",
                    (filename, file_path, file_type)
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return jsonify({"error": "Database error"}), 500

        return jsonify({"message": "File uploaded successfully", "file_path": file_path, "file_type": file_type}), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400


# Fetch uploaded files
@app.route("/api/files", methods=["GET"])
def get_files():
    conn = get_db_connection()
    files = conn.execute("SELECT * FROM files").fetchall()
    conn.close()
    return jsonify([{"id": file["id"], "filename": file["filename"], "file_path": file["file_path"], "file_type": file["file_type"]} for file in files])

#brute force code
# Dummy function to simulate database connection (replace with actual database logic)
def get_db_connection():
    import sqlite3
    conn = sqlite3.connect("my_database.db")  # Replace with your actual database path
    conn.row_factory = sqlite3.Row
    return conn


# Brute force password cracking function
def crack_password(wordlist_path, zip_file_path, file_id):
    zip_file = ZipFile(zip_file_path)
    n_words = len(list(open(wordlist_path, 'rb')))

    print('[2] Total passwords to test:', f'{n_words:,}')
    with open(wordlist_path, 'rb') as wordlist:
        for word in tqdm(wordlist, total=n_words, unit='word'):
            try:
                zip_file.extractall(pwd=word.strip())
            except:
                continue
            else:
                print('\n[+] Password found:', word.decode().strip())
                # Update the database
                conn = get_db_connection()
                conn.execute(
                    "UPDATE files SET bruteforce_status = ?, password = ? WHERE id = ?",
                    ("Completed", word.decode().strip(), file_id),
                )
                conn.commit()
                conn.close()
                return True  # Password found
    print("\n[!] Password not found, try another wordlist.")
    conn = get_db_connection()
    conn.execute(
        "UPDATE files SET bruteforce_status = ? WHERE id = ?",
        ("Failed", file_id),
    )
    conn.commit()
    conn.close()
    return False  # Password not found


@app.route("/api/bruteforce", methods=["POST"])
def bruteforce_file():
    data = request.json
    file_id = data.get("file_id")
    wordlist_path = r"C:\Users\Gelgin\Desktop\BruteForce_Project\backend\wordlist.txt"

    if not file_id:
        return jsonify({"error": "File ID is required"}), 400

    # Fetch file details from the database
    conn = get_db_connection()
    file = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    conn.close()

    if not file:
        return jsonify({"error": "File not found"}), 404

    # Get file path
    zip_file_path = Path(file["file_path"])

    if not zip_file_path.exists():
        return jsonify({"error": "Zip file does not exist"}), 404

    # Define a thread function to perform the brute force in the background
    def thread_func():
        with app.app_context():  # Ensure Flask application context is available in the thread
            crack_password(wordlist_path, zip_file_path, file_id)

    # Start the thread
    threading.Thread(target=thread_func).start()
    return jsonify({"message": f"Started bruteforce for file ID {file_id}"}), 200

if __name__ == "__main__":
    app.run(debug=True)