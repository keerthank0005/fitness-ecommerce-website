import os
import datetime
import smtplib
import sqlite3

from flask import Flask, render_template, request, redirect, session, jsonify, url_for, flash
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

import razorpay

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "fitai_secret_123"

# ================= DATABASE CONFIG =================

app.config['MYSQL_HOST'] = os.environ.get("mysql.railway.internal")
app.config['MYSQL_USER'] = os.environ.get("root")
app.config['MYSQL_PASSWORD'] = os.environ.get("MWlOUWeyZeKChEuqvWgMtwEFWvhwuoIF")
app.config['MYSQL_DB'] = os.environ.get("railway")
app.config['MYSQL_PORT'] = int(os.environ.get("MYSQLPORT", 3306))

mysql = MySQL(app) 

# ================= RAZORPAY CONFIG =================

RAZORPAY_KEY_ID = "rzp_test_SeyoxAKE4PxyuQ"
RAZORPAY_SECRET = "gA2YEfTj8gyrf18N6fDKIh8h"

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))

# ================= EMAIL CONFIG =================

SENDER_EMAIL = "keerthan0505@gmail.com"
SENDER_PASSWORD = "ixqrluqlzouewthj"

# ================= SINGLE ADMIN CONFIG =================
# Only this email can open admin dashboard from same /login page

ADMIN_EMAIL = "keerthan0505@gmail.com"
ADMIN_PASSWORD_HASH = generate_password_hash("Admin@123")

# ================= HELPER FUNCTIONS =================

def is_admin_logged_in():
    return session.get('admin') == ADMIN_EMAIL


def create_invoice_pdf(name, email, cart, total, order_id, order_date, order_time, filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>FitAI Store</b>", styles["Title"]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<b>ORDER INVOICE</b>", styles["Heading2"]))
    elements.append(Spacer(1, 18))

    info_data = [
        ["Customer Name", name],
        ["Customer Email", email],
        ["Order ID", order_id],
        ["Order Date", order_date],
        ["Order Time", order_time]
    ]

    info_table = Table(info_data, colWidths=[120, 350])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    data = [["Product", "Qty", "Unit Price", "Subtotal"]]

    for item in cart:
        product_name = item.get("name", "Unknown Product")
        quantity = int(item.get("quantity", 1))
        price = float(item.get("price", 0))
        subtotal = price * quantity

        data.append([
            product_name,
            str(quantity),
            f"Rs. {price:.2f}",
            f"Rs. {subtotal:.2f}"
        ])

    data.append(["", "", "Grand Total", f"Rs. {float(total):.2f}"])

    product_table = Table(data, colWidths=[220, 60, 110, 110])
    product_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.whitesmoke, colors.HexColor("#eaf2f8")]),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (2, -1), (3, -1), "Helvetica-Bold"),
        ("BACKGROUND", (2, -1), (3, -1), colors.HexColor("#d9ead3")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(product_table)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(
        "Thank you for shopping with FitAI Store. We appreciate your order.",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "For support, contact: support@fitai.com",
        styles["Normal"]
    ))

    doc.build(elements)


def send_invoice_email(uid, cart, total):
    cur = mysql.connection.cursor()
    cur.execute("SELECT email, name FROM users WHERE id=%s", (uid,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return

    email = user[0]
    name = user[1]

    now = datetime.datetime.now()
    order_date = now.strftime("%d-%b-%Y")
    order_time = now.strftime("%I:%M %p")
    order_id = f"FITAI-{uid}-{now.strftime('%Y%m%d%H%M%S')}"

    filename = f"invoice_{uid}_{now.strftime('%Y%m%d%H%M%S')}.pdf"

    create_invoice_pdf(
        name=name,
        email=email,
        cart=cart,
        total=total,
        order_id=order_id,
        order_date=order_date,
        order_time=order_time,
        filename=filename
    )

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = email
    msg["Subject"] = "FitAI Order Invoice"

    body = f"""Hello {name},

Thank you for shopping with FitAI Store.

Your order has been placed successfully.

Order ID: {order_id}
Total Paid: Rs. {float(total):.2f}
Order Date: {order_date}
Order Time: {order_time}

Please find your invoice attached.

Regards,
FitAI Store Team
support@fitai.com
"""
    msg.attach(MIMEText(body, "plain"))

    with open(filename, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()

    if os.path.exists(filename):
        os.remove(filename)

# ================= HOME =================

@app.route('/')
def home():
    return render_template("index.html")

# ================= SIGNUP =================

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].strip().lower()
        password = request.form['password']
        age = request.form['age']
        weight = request.form['weight']
        height = request.form['height']
        goal = request.form['goal']
        sport = request.form['sport']

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO users (name, email, password, age, weight, height, goal, sport)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, hashed_password, age, weight, height, goal, sport))
        mysql.connection.commit()
        cur.close()

        flash("Signup successful. Please login.", "success")
        return redirect('/login')

    return render_template("signup.html")

# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        # ===== ADMIN LOGIN USING SAME LOGIN PAGE =====
        if email == ADMIN_EMAIL.lower():
            if check_password_hash(ADMIN_PASSWORD_HASH, password):
                session.clear()
                session['admin'] = ADMIN_EMAIL
                flash("Admin login successful", "success")
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Invalid admin password", "danger")
                return redirect('/login')

        # ===== NORMAL USER LOGIN =====
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            stored_password = user[3]
            valid_login = False

            if stored_password:
                try:
                    if check_password_hash(stored_password, password):
                        valid_login = True
                except Exception:
                    pass

                if stored_password == password:
                    valid_login = True

            if valid_login:
                session.clear()
                session['user_id'] = user[0]
                flash("Login successful", "success")
                return redirect('/profile')

        flash("Invalid credentials", "danger")
        return redirect('/login')

    return render_template("login.html")

# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= PROFILE =================

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT id, name, email, age, weight, height, goal, sport
        FROM users
        WHERE id=%s
    """, (session['user_id'],))
    data = cur.fetchone()
    cur.close()

    if data is None:
        session.clear()
        return redirect('/login')

    user = {
        "id": data[0],
        "name": data[1],
        "email": data[2],
        "age": data[3],
        "weight": data[4],
        "height": data[5],
        "goal": data[6],
        "sport": data[7]
    }

    try:
        height_m = float(user["height"]) / 100
        bmi = round(float(user["weight"]) / (height_m * height_m), 2)
    except Exception:
        bmi = "N/A"

    return render_template("profile.html", user=user, bmi=bmi)

# ================= ADD TO CART =================

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'cart' not in session:
        session['cart'] = []

    name = request.form['name']
    price = int(request.form['price'])
    image = request.form.get('image', '')

    for item in session['cart']:
        if item['name'] == name:
            item['quantity'] = item.get('quantity', 1) + 1
            session.modified = True
            return jsonify({"status": "success"})

    session['cart'].append({
        "name": name,
        "price": price,
        "image": image,
        "quantity": 1
    })

    session.modified = True
    return jsonify({"status": "success"})

# ================= REMOVE FROM CART =================

@app.route('/remove_from_cart', methods=['POST'])
def remove():
    name = request.form['name']
    cart = session.get('cart', [])
    cart = [i for i in cart if i['name'] != name]
    session['cart'] = cart
    session.modified = True
    return redirect('/cart')

# ================= CART =================

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])

    for item in cart_items:
        if 'quantity' not in item:
            item['quantity'] = 1

    session.modified = True
    total = sum(item['price'] * item['quantity'] for item in cart_items)

    return render_template("cart.html", cart=cart_items, total=total)

# ================= GET CART =================

@app.route('/get_cart')
def get_cart():
    cart = session.get('cart', [])

    for item in cart:
        if 'quantity' not in item:
            item['quantity'] = 1

    return jsonify({"cart": cart})

# ================= UPDATE QUANTITY =================

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    data = request.get_json()
    name = data['name']
    change = int(data['change'])

    for item in session.get('cart', []):
        if item['name'] == name:
            item['quantity'] = item.get('quantity', 1) + change

            if item['quantity'] <= 0:
                session['cart'].remove(item)
            break

    session.modified = True
    return jsonify({"status": "success"})

# ================= PAYMENT =================

@app.route('/payment')
def payment():
    if 'user_id' not in session:
        return redirect('/login')

    cart_items = session.get('cart', [])

    if len(cart_items) == 0:
        return redirect('/cart')

    total = sum(i['price'] * i.get('quantity', 1) for i in cart_items)

    order = razorpay_client.order.create({
        "amount": total * 100,
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template(
        "payment.html",
        cart=cart_items,
        total=total,
        razorpay_key=RAZORPAY_KEY_ID,
        order_id=order['id']
    )

# ================= CREATE ORDER =================

@app.route('/create_order')
def create_order():
    cart = session.get('cart', [])
    total = sum(i['price'] * i.get('quantity', 1) for i in cart)

    order = razorpay_client.order.create({
        "amount": total * 100,
        "currency": "INR"
    })

    return jsonify({
        "order_id": order['id'],
        "amount": total * 100,
        "key": RAZORPAY_KEY_ID
    })

# ================= PAYMENT SUCCESS =================

@app.route('/payment_success', methods=['POST'])
def payment_success():
    if 'user_id' not in session:
        return jsonify({"status": "User not logged in"}), 401

    data = request.get_json()

    if not data:
        return jsonify({"status": "No data received"}), 400

    params_dict = {
        'razorpay_order_id': data.get('razorpay_order_id'),
        'razorpay_payment_id': data.get('razorpay_payment_id'),
        'razorpay_signature': data.get('razorpay_signature')
    }

    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
    except Exception:
        return jsonify({"status": "Verification Failed"}), 400

    cart_items = session.get('cart', [])

    if not cart_items:
        return jsonify({"status": "Cart is empty"}), 400

    total = sum(i['price'] * i.get('quantity', 1) for i in cart_items)

    cur = mysql.connection.cursor()
    for item in cart_items:
        quantity = int(item.get('quantity', 1))
        for _ in range(quantity):
            cur.execute("""
                INSERT INTO orders (user_id, product_name, price)
                VALUES (%s, %s, %s)
            """, (session['user_id'], item['name'], item['price']))
    mysql.connection.commit()
    cur.close()

    try:
        send_invoice_email(session['user_id'], cart_items, total)
    except Exception as e:
        print("Email sending failed:", e)

    session.pop('cart', None)

    return jsonify({"status": "Payment Successful"})

# ================= FITAI AI =================

@app.route('/ai', methods=['GET','POST'])
def ai():

    answer = ""

    if request.method == "POST":

        q = request.form['question'].lower()

        # WEIGHT LOSS
        if "weight" in q or "fat" in q:
            answer = """
Weight Loss Suggestions:

Workout:
- Running 30 mins
- Cycling
- HIIT training
- Skipping

Recommended Products:
- Treadmill
- Exercise Bike
- Jump Rope
- Resistance Bands
- Yoga Mat

Extra Suggestions:
- Calorie deficit diet
- Track BMI weekly
- Drink 4 liters water
"""

        elif "muscle" in q or "bulk" in q or "gain" in q:
            answer = """
Muscle Gain Suggestions:

Workout:
- Bench Press
- Squats
- Deadlifts

Recommended Products:
- Adjustable Dumbbells
- Bench Press Set
- Kettlebells
- Protein Powder
- Creatine
- Gym Gloves

Extra Suggestions:
- High protein diet
- 8 hours sleep
"""

        elif "abs" in q:
            answer = """
Abs Training:

Exercises:
- Crunches
- Planks
- Leg Raises

Products:
- Ab Roller
- Yoga Mat
- Push-up Bars
- Medicine Ball
"""

        elif "home workout" in q:
            answer = """
Home Workout Kit:

Recommended Products:
- Resistance Bands
- Dumbbells
- Yoga Mat
- Pull-up Bar
- Push-up Bars
- Kettlebell
"""

        elif "football" in q:
            answer = """
Football Training:

Practice:
- Passing drills
- Dribbling
- Sprint work

Products:
- Football
- Football Studs
- Shin Guards
- Agility Cones
- Training Ladder
"""

        elif "cricket" in q:
            answer = """
Cricket Training:

Practice:
- Batting drills
- Bowling drills

Products:
- Cricket Bat
- Cricket Ball
- Batting Gloves
- Agility Cones
"""

        elif "basketball" in q:
            answer = """
Basketball Training:

Products:
- Basketball
- Training Ladder
- Agility Cones
- Resistance Bands
"""

        elif "badminton" in q:
            answer = """
Badminton Training:

Products:
- Badminton Racket
- Resistance Bands
- Agility Cones
"""

        elif "tennis" in q:
            answer = """
Tennis Training:

Products:
- Tennis Racket
- Training Ladder
- Foam Roller
"""

        elif "protein" in q or "supplement" in q:
            answer = """
Supplements:
- Protein Powder
- Creatine
- Shaker Bottle
"""

        elif "beginner" in q:
            answer = """
Beginner Starter Kit:
- Dumbbells
- Resistance Bands
- Yoga Mat
- Jump Rope
"""

        elif "cardio" in q:
            answer = """
Cardio Products:
- Treadmill
- Exercise Bike
- Jump Rope
"""

        elif "recovery" in q or "pain" in q:
            answer = """
Recovery Tools:
- Foam Roller
- Yoga Mat
- Resistance Bands
"""

        elif "equipment" in q:
            answer = """
Popular Equipment:
- Dumbbells
- Bench Press
- Kettlebell
- Treadmill
- Pull-up Bar
"""

        else:
            answer = """
Ask about:
- Weight loss
- Muscle gain
- Home workout
- Football
- Cricket
- Basketball
- Recovery
- Supplements
- Gym equipment
"""

    return render_template('ai.html', answer=answer)
    
# ================= SUCCESS =================

@app.route('/success')
def success():
    return render_template("success.html")

# ================= OPTIONAL PLACE ORDER =================

@app.route('/place_order', methods=['POST'])
def place_order():
    name = request.form.get('name', 'Customer')
    email = request.form.get('email')

    cart_items = session.get('cart', [])
    if not cart_items:
        return "Cart is empty"

    now = datetime.datetime.now()
    order_date = now.strftime("%d-%b-%Y")
    order_time = now.strftime("%I:%M %p")

    total = sum(item['price'] * item.get('quantity', 1) for item in cart_items)
    filename = "invoice.pdf"
    order_id = f"FITAI-GUEST-{now.strftime('%Y%m%d%H%M%S')}"

    create_invoice_pdf(
        name=name,
        email=email,
        cart=cart_items,
        total=total,
        order_id=order_id,
        order_date=order_date,
        order_time=order_time,
        filename=filename
    )

    product_details = ""
    for item in cart_items:
        product_details += f"- {item['name']} (Qty: {item.get('quantity', 1)})\n"

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = email
    msg['Subject'] = "FitAI Order Confirmation & Invoice"

    body = f"""Hello {name},

Thank you for shopping with FitAI Store! 💪

Your order has been successfully placed. Here are your order details:

-------------------------------
🛒 Products:
{product_details}

💰 Total Paid: ₹{total}

📅 Order Date: {order_date}
⏰ Order Time: {order_time}
-------------------------------

Your invoice is attached with this email.

Thank you for choosing FitAI Store!

Regards,
FitAI Store Team
support@fitai.com
"""

    msg.attach(MIMEText(body, 'plain'))

    with open(filename, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.quit()

    if os.path.exists(filename):
        os.remove(filename)

    return "Order placed, invoice generated & email sent!"

# ================= MY ORDERS =================

@app.route('/my_orders')
def my_orders():
    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT product_name, price, status, order_date
        FROM orders
        WHERE user_id = %s
        ORDER BY id DESC
    """, (session['user_id'],))
    orders = cur.fetchall()
    cur.close()

    return render_template("track_orders.html", orders=orders)

# ================= UPDATE ORDER STATUS =================

@app.route('/update_order/<int:order_id>/<status>')
def update_order(order_id, status):
    if not is_admin_logged_in():
        flash('Please login as admin first.', 'warning')
        return redirect('/login')

    allowed_status = ['Ordered', 'Processing', 'Delivered', 'Cancelled']
    if status not in allowed_status:
        flash('Invalid status', 'danger')
        return redirect(url_for('admin_dashboard'))

    cur = mysql.connection.cursor()
    cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    mysql.connection.commit()
    cur.close()

    flash("Order status updated successfully.", "success")
    return redirect(url_for('admin_dashboard'))
# ================= ADMIN DASHBOARD =================

@app.route('/admin_dashboard')
def admin_dashboard():
    if not is_admin_logged_in():
        flash('Please login as admin first.', 'warning')
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    total_orders = cur.fetchone()[0]

    cur.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cur.fetchall()

    cur.close()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_products=total_products,
        total_orders=total_orders,
        orders=orders
    )

# ================= ADMIN LOGOUT =================

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    flash('Admin logged out successfully.', 'info')
    return redirect('/login')

# ================= ADMIN ADD PRODUCT =================

@app.route('/admin_add_product', methods=['GET', 'POST'])
def admin_add_product():
    if not is_admin_logged_in():
        flash('Please login as admin first.', 'warning')
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        image = request.form['image']

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO products (name, price, category, image) VALUES (%s, %s, %s, %s)",
            (name, price, category, image)
        )
        mysql.connection.commit()
        cur.close()

        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_add_product.html')

# ================= ADMIN DELETE PRODUCT =================

@app.route('/delete_product/<int:id>')
def delete_product(id):
    if not is_admin_logged_in():
        flash('Please login as admin first.', 'warning')
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (id,))
    mysql.connection.commit()
    cur.close()

    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/sell_on_fitai.html')
def sell_on_fitai():
    return render_template('sell_on_fitai.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/help.html')
def help_page():
    return render_template('help.html')

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    # save into database
    pass

@app.route('/admin_dashboard')
def admin():
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback")
    data = cursor.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', feedback=data)

# ================= RUN =================