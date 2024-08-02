from flask import Flask, render_template, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import MySQLdb

app = Flask(__name__)
app.secret_key = 'Av43@#g'

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASS = 'Note@123'
DB_NAME = 'note_app'

def get_db_connection():
    conn = MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASS,
        db=DB_NAME
    )
    return conn

@app.route('/')
@app.route('/home')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          id INT AUTO_INCREMENT PRIMARY KEY,
                          name VARCHAR(100) NOT NULL,
                          email VARCHAR(100) UNIQUE NOT NULL,
                          password TEXT NOT NULL
                      )''')
    cursor.execute('''   
                CREATE TABLE IF NOT EXISTS note (
                note_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(10) NOT NULL,
                author VARCHAR(10) NOT NULL,
                title VARCHAR(255) NOT NULL,
                date DATE NOT NULL,
                note TEXT NOT NULL,
                note_type ENUM('public', 'private') NOT NULL,
                FOREIGN KEY (author) REFERENCES user(name));
                ''')
    conn.commit()
    cursor.close()
    conn.close()
    return render_template('index.html')



@app.route('/note/sign_up', methods=['POST'])
def sign_up():
    if request.content_type != 'application/json':
        return jsonify({'error': 'Unsupported Media Type, expected application/json'})

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input, JSON data expected'})

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({'error': 'Name, email, and password are required'})
    
    hash_password = generate_password_hash(password)
    token = jwt.encode({'email': email}, app.secret_key, algorithm='HS256')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Email already exists'})
    
    cursor.execute('INSERT INTO users (name, username, password) VALUES (%s, %s, %s)',
                   (name, email, hash_password))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'token': token})



@app.route('/note/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user_record = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user_record and check_password_hash(user_record['password'], password):
        token = jwt.encode({'email': email}, app.secret_key, algorithm='HS256')
        return jsonify({'token': token})
    else:
        return jsonify({'error': 'Invalid username or password'})


@app.route('/note/add_note', methods=['POST'])
def add_note():
    data = request.get_json()
    date = data['date']
    title = data['title']
    note = data['note']
    note_type = data['note_type']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO notes (title, note, note_type, date) VALUES (%s, %s, %s, %s)',
                   (title, note, note_type, date))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message':"Note added Successfully!"})

@app.route('/getAllNotes', methods=['GET'])
def get_all_notes():
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM notes')
    notes = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'notes': notes}), 200

@app.route('/getNote/<int:id>', methods=['GET'])
def get_note_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM notes WHERE id = %s', (id,))
    note = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'note': note}), 200

if __name__ == '__main__':
    app.run(debug=True)
