import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash



from flask import Flask, render_template, jsonify, request
from flask_mysqldb import MySQL
from flask_cors import CORS

# -----------------------------
# Flask App Setup
# -----------------------------
app = Flask(__name__)
CORS(app)

# -----------------------------
# MySQL Configuration
# -----------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Akshay99452'     # put your MySQL password if any
app.config['MYSQL_DB'] = 'vitaledge'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# -----------------------------
# Route: Load Frontend
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')


# -----------------------------
# Route: Test Database Connection
# Open in browser:
# http://127.0.0.1:5000/testdb
# -----------------------------
@app.route('/testdb')
def testdb():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM products")
        result = cur.fetchone()
        return f"Database Connected ✅ | Products in DB: {result['total']}"
    except Exception as e:
        return f"Database Error ❌ : {str(e)}"


# -----------------------------
# API: Get All Products
# Used by frontend fetch()
# -----------------------------
@app.route('/api/products', methods=['GET'])
def get_products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM products ORDER BY added_date DESC")
    rows = cur.fetchall()

    product_list = []

    for r in rows:
        product_list.append({
        "id": r["id"],
        "name": r["name"],
        "description": r["description"],
        "price": float(r["price"]),
        "category": r["category"],
        "imageUrl": r["image_url"],
        "purchaseLink": r["purchase_link"],
        "source": r["source"],
        "user_id": r["user_id"],
        "addedDate": str(r["added_date"])
    })

    return jsonify(product_list)



# ----------------
#Sign Up API
#---------------

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    city = data.get('city')

    cur = mysql.connection.cursor()

    # Check if user already exists
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    existing = cur.fetchone()

    if existing:
        return jsonify({"success": False, "message": "User already exists"})

    # 🔐 Hash password
    hashed_password = generate_password_hash(password)

    cur.execute("""
        INSERT INTO users (username, email, password, city)
        VALUES (%s, %s, %s, %s)
    """, (username, email, hashed_password, city))

    mysql.connection.commit()

    return jsonify({"success": True})



# ----------------------------
# Login API
# ----------------------------
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json

    identifier = data.get('identifier')
    password = data.get('password')

    cur = mysql.connection.cursor()

    # Fetch user by username OR email
    cur.execute("""
        SELECT * FROM users
        WHERE username=%s OR email=%s
    """, (identifier, identifier))

    user = cur.fetchone()

    # Check hashed password
    if user and check_password_hash(user["password"], password):
        return jsonify({
            "success": True,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "city": user["city"]
            }
        })

    return jsonify({
        "success": False,
        "message": "Invalid credentials"
    })


# -----------------------------
# API: Add Product
# -----------------------------
@app.route('/api/add-product', methods=['POST'])
def add_product():
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "Login required"})
    name = request.form.get('name')
    description = request.form.get('description')
    category = request.form.get('category')
    purchase_link = request.form.get('purchaseLink')
    source = request.form.get('source')
    price = request.form.get('price')

    image = request.files.get('image')

    image_url = None

    if image:
        import time
        filename = str(int(time.time())) + "_" + secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        image_url = f'/static/uploads/{filename}'
    else:
        image_url = '/static/uploads/default.png'

    cur = mysql.connection.cursor()

    cur.execute("""
    INSERT INTO products
    (name, description, price, category, image_url, purchase_link, source, user_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
""", (name, description, price, category, image_url, purchase_link, source, user_id))


    mysql.connection.commit()

    return jsonify({"success": True})

#--------------------------
# delete API
#---------+----------------

@app.route('/api/delete-product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):

    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"success": False, "message": "Login required"})

    cur = mysql.connection.cursor()

    cur.execute("""
        DELETE FROM products
        WHERE id=%s AND user_id=%s
    """, (product_id, user_id))

    if cur.rowcount == 0:
        return jsonify({"success": False, "message": "Unauthorized"})

    mysql.connection.commit()

    return jsonify({"success": True})

@app.route('/api/edit-product/<int:product_id>', methods=['PUT'])
def edit_product(product_id):

    data = request.json
    user_id = data.get("user_id")
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE products
        SET name=%s, description=%s, price=%s
        WHERE id=%s AND user_id=%s
    """, (name, description, price, product_id, user_id))

    mysql.connection.commit()

    if cur.rowcount == 0:
        return jsonify({"success": False, "message": "Not authorized or product not found"})

    return jsonify({"success": True})


@app.route('/api/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT c.product_id, c.quantity,
               p.name, p.price, p.image_url, p.category
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))

    rows = cur.fetchall()

    cart_items = []

    for r in rows:
        cart_items.append({
            "product_id": r["product_id"],
            "name": r["name"],
            "price": float(r["price"]),
            "imageUrl": r["image_url"],
            "category": r["category"],
            "quantity": r["quantity"]
        })

    return jsonify(cart_items)

@app.route('/api/add-to-cart', methods=['POST'])
def add_to_cart():

    data = request.json
    user_id = data.get("user_id")
    product_id = data.get("product_id")

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT * FROM cart
        WHERE user_id=%s AND product_id=%s
    """, (user_id, product_id))

    existing = cur.fetchone()

    if existing:
        cur.execute("""
            UPDATE cart
            SET quantity = quantity + 1
            WHERE user_id=%s AND product_id=%s
        """, (user_id, product_id))
    else:
        cur.execute("""
            INSERT INTO cart (user_id, product_id)
            VALUES (%s, %s)
        """, (user_id, product_id))

    mysql.connection.commit()

    return jsonify({"success": True})

@app.route('/api/remove-from-cart', methods=['POST'])
def remove_from_cart():

    data = request.json
    user_id = data.get("user_id")
    product_id = data.get("product_id")

    cur = mysql.connection.cursor()

    cur.execute("""
        DELETE FROM cart
        WHERE user_id=%s AND product_id=%s
    """, (user_id, product_id))

    mysql.connection.commit()

    return jsonify({"success": True})



# -----------------------------
# Run Server
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
