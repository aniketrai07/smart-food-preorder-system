import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
from models import get_db, DB

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.secret_key = "change-this-secret"

print("BASE_DIR:", BASE_DIR)
print("TEMPLATE FOLDER:", app.template_folder)
print("TEMPLATES FILES:", os.listdir(app.template_folder))

def init_db():
    conn = get_db()
    with open("schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    cur = conn.cursor()

    # Seed stalls
    cur.execute("SELECT COUNT(*) as c FROM stalls")
    if cur.fetchone()["c"] == 0:
        cur.execute("INSERT INTO stalls(name) VALUES (?)", ("Main Food Stall",))
        stall_id = cur.lastrowid

        cur.executemany(
    "INSERT INTO menu_items(stall_id,name,price,category,is_available,prep_minutes) VALUES (?,?,?,?,?,?)",
    [
        (stall_id, "Veg Burger", 60, "Snacks", 1, 7),
        (stall_id, "Sandwich", 50, "Snacks", 1, 6),
        (stall_id, "Cold Coffee", 70, "Drinks", 1, 4),
        (stall_id, "Samosa", 20, "Snacks", 1, 3),
        (stall_id, "Noodles", 80, "Meals", 1, 10),

        # ---- 20+ MORE ITEMS ----
        (stall_id, "Pav Bhaji", 90, "Meals", 1, 12),
        (stall_id, "Chole Bhature", 110, "Meals", 1, 15),
        (stall_id, "Veg Momos", 70, "Snacks", 1, 10),
        (stall_id, "Paneer Momos", 85, "Snacks", 1, 11),
        (stall_id, "French Fries", 60, "Snacks", 1, 8),
        (stall_id, "Cheese Fries", 80, "Snacks", 1, 9),
        (stall_id, "Veg Pizza Slice", 65, "Snacks", 1, 8),
        (stall_id, "Paneer Pizza Slice", 80, "Snacks", 1, 9),
        (stall_id, "Veg Roll", 70, "Snacks", 1, 8),
        (stall_id, "Paneer Roll", 85, "Snacks", 1, 9),
        (stall_id, "Veg Maggi", 50, "Snacks", 1, 7),
        (stall_id, "Cheese Maggi", 65, "Snacks", 1, 8),
        (stall_id, "Masala Dosa", 90, "South Indian", 1, 12),
        (stall_id, "Idli Sambhar", 70, "South Indian", 1, 10),
        (stall_id, "Uttapam", 85, "South Indian", 1, 12),
        (stall_id, "Aloo Paratha", 60, "North Indian", 1, 10),
        (stall_id, "Paneer Paratha", 75, "North Indian", 1, 11),
        (stall_id, "Rajma Chawal", 100, "Meals", 1, 14),
        (stall_id, "Dal Chawal", 90, "Meals", 1, 12),
        (stall_id, "Veg Biryani", 120, "Meals", 1, 18),
        (stall_id, "Paneer Biryani", 140, "Meals", 1, 20),
        (stall_id, "Chicken Biryani", 160, "Meals", 1, 20),
        (stall_id, "Veg Thali", 130, "Meals", 1, 18),
        (stall_id, "Paneer Thali", 150, "Meals", 1, 20),

        # Drinks
        (stall_id, "Lemon Soda", 35, "Drinks", 1, 3),
        (stall_id, "Masala Chai", 20, "Drinks", 1, 4),
        (stall_id, "Green Tea", 25, "Drinks", 1, 4),
        (stall_id, "Hot Coffee", 30, "Drinks", 1, 5),
        (stall_id, "Chocolate Shake", 90, "Drinks", 1, 6),
    ],
)

    # Seed time slots
    cur.execute("SELECT COUNT(*) as c FROM time_slots")
    if cur.fetchone()["c"] == 0:
        cur.executemany(
            "INSERT INTO time_slots(label,start_time,end_time,max_orders) VALUES (?,?,?,?)",
            [
                ("10:30-10:45", "10:30", "10:45", 15),
                ("10:45-11:00", "10:45", "11:00", 15),
                ("11:00-11:15", "11:00", "11:15", 15),
                ("11:15-11:30", "11:15", "11:30", 15),
            ],
        )

    # Seed admin user
    cur.execute("SELECT COUNT(*) as c FROM users WHERE role='admin'")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)",
            ("Admin", "admin@campus.com", generate_password_hash("admin123"), "admin"),
        )

    conn.commit()
    conn.close()

def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return user

def login_required():
    if "user_id" not in session:
        flash("Please login first.")
        return False
    return True

def admin_required():
    u = current_user()
    return u and u["role"] == "admin"


@app.route("/")
def index():
    return render_template("index.html", user=current_user())


# ---------------- AUTH ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if not name or not email or not password:
            flash("All fields required.")
            return redirect(url_for("register"))

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users(name,email,password_hash,role) VALUES (?,?,?,?)",
                (name, email, generate_password_hash(password), "student"),
            )
            conn.commit()
            flash("Registered successfully. Login now.")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already exists.")
            return redirect(url_for("register"))
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session.setdefault("cart", {})
            flash("Logged in!")
            return redirect(url_for("menu"))

        flash("Invalid credentials.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for("index"))


# ---------------- MENU ----------------
@app.route("/menu")
def menu():
    conn = get_db()
    stall = conn.execute("SELECT * FROM stalls LIMIT 1").fetchone()
    items = conn.execute(
        "SELECT * FROM menu_items WHERE stall_id=? ORDER BY category, name",
        (stall["id"],),
    ).fetchall()

    demand = conn.execute("""
        SELECT time_slots.id, time_slots.label,
               COUNT(orders.id) as orders_count,
               time_slots.max_orders as max_orders
        FROM time_slots
        LEFT JOIN orders ON orders.slot_id = time_slots.id AND orders.status != 'Cancelled'
        GROUP BY time_slots.id
        ORDER BY time_slots.id
    """).fetchall()

    # best slot recommendation: minimum orders_count
    best_slot = min(demand, key=lambda x: x["orders_count"]) if demand else None

    conn.close()
    cart = session.get("cart", {})
    return render_template("menu.html", stall=stall, items=items, demand=demand, best_slot=best_slot, cart=cart, user=current_user())


# ---------------- CART ----------------
@app.route("/cart/add/<int:item_id>", methods=["POST"])
def cart_add(item_id):
    if not login_required():
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    cart[str(item_id)] = cart.get(str(item_id), 0) + 1
    session["cart"] = cart
    flash("Added to cart.")
    return redirect(url_for("menu"))

@app.route("/cart/remove/<int:item_id>")
def cart_remove(item_id):
    if not login_required():
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    cart.pop(str(item_id), None)
    session["cart"] = cart
    flash("Removed item.")
    return redirect(url_for("cart_view"))

@app.route("/cart")
def cart_view():
    if not login_required():
        return redirect(url_for("login"))

    cart = session.get("cart", {})
    conn = get_db()
    stall = conn.execute("SELECT * FROM stalls LIMIT 1").fetchone()

    item_rows = []
    total = 0

    for item_id, qty in cart.items():
        item = conn.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
        if item:
            line = item["price"] * qty
            total += line
            item_rows.append({"item": item, "qty": qty, "line": line})

    slots = conn.execute("""
        SELECT ts.*,
               (SELECT COUNT(*) FROM orders o WHERE o.slot_id=ts.id AND o.status != 'Cancelled') as filled
        FROM time_slots ts
        ORDER BY ts.id
    """).fetchall()

    conn.close()
    return render_template("cart.html", item_rows=item_rows, total=total, slots=slots, stall=stall)

@app.route("/cart/update", methods=["POST"])
def cart_update():
    if not login_required():
        return redirect(url_for("login"))

    new_cart = {}
    for key, val in request.form.items():
        if key.startswith("qty_"):
            item_id = key.replace("qty_", "")
            try:
                q = int(val)
                if q > 0:
                    new_cart[item_id] = q
            except ValueError:
                pass

    session["cart"] = new_cart
    flash("Cart updated.")
    return redirect(url_for("cart_view"))


# ---------------- CHECKOUT ----------------
@app.route("/checkout", methods=["GET"])
def checkout_page():
    if not login_required():
        return redirect(url_for("login"))
    return render_template("checkout.html")


@app.route("/checkout", methods=["POST"])
def checkout():
    if not login_required():
        return redirect(url_for("login"))

    slot_id = int(request.form["slot_id"])
    cart = session.get("cart", {})
    if not cart:
        flash("Cart is empty.")
        return redirect(url_for("menu"))

    conn = get_db()
    stall = conn.execute("SELECT * FROM stalls LIMIT 1").fetchone()

    slot = conn.execute("SELECT * FROM time_slots WHERE id=?", (slot_id,)).fetchone()
    if not slot:
        conn.close()
        flash("Invalid slot.")
        return redirect(url_for("cart_view"))

    current_count = conn.execute("""
        SELECT COUNT(*) as c FROM orders
        WHERE slot_id=? AND status != 'Cancelled'
    """, (slot_id,)).fetchone()["c"]

    if current_count >= slot["max_orders"]:
        conn.close()
        flash("Slot is full. Choose another slot.")
        return redirect(url_for("cart_view"))

    # calculate total + validate availability
    total = 0
    items_for_insert = []
    for item_id, qty in cart.items():
        item = conn.execute(
            "SELECT * FROM menu_items WHERE id=? AND is_available=1", (item_id,)
        ).fetchone()
        if not item:
            conn.close()
            flash("Some items are unavailable now. Update your cart.")
            return redirect(url_for("cart_view"))

        total += item["price"] * qty
        items_for_insert.append((item["id"], qty, item["price"]))

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders(user_id,stall_id,slot_id,total_amount,status,created_at) VALUES (?,?,?,?,?,?)",
        (session["user_id"], stall["id"], slot_id, total, "Pending",
         datetime.now().isoformat(timespec="seconds")),
    )
    order_id = cur.lastrowid

    cur.executemany(
        "INSERT INTO order_items(order_id,item_id,qty,price_each) VALUES (?,?,?,?)",
        [(order_id, iid, qty, price) for (iid, qty, price) in items_for_insert],
    )

    conn.commit()
    conn.close()

    session["cart"] = {}
    flash("Order placed successfully ✅")
    return redirect(url_for("my_orders"))


# ---------------- STUDENT ORDERS ----------------
@app.route("/my-orders")
def my_orders():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    orders = conn.execute("""
        SELECT o.*, ts.label as slot_label
        FROM orders o
        JOIN time_slots ts ON ts.id = o.slot_id
        WHERE o.user_id=?
        ORDER BY o.id DESC
    """, (session["user_id"],)).fetchall()
    conn.close()

    return render_template("my_orders.html", orders=orders)


@app.route("/order/<int:order_id>")
def order_detail(order_id):
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    order = conn.execute("""
        SELECT o.*, ts.label as slot_label, s.name as stall_name
        FROM orders o
        JOIN time_slots ts ON ts.id = o.slot_id
        JOIN stalls s ON s.id = o.stall_id
        WHERE o.id=? AND o.user_id=?
    """, (order_id, session["user_id"])).fetchone()

    items = conn.execute("""
        SELECT oi.qty, oi.price_each, mi.name
        FROM order_items oi
        JOIN menu_items mi ON mi.id = oi.item_id
        WHERE oi.order_id=?
    """, (order_id,)).fetchall()

    conn.close()

    if not order:
        flash("Order not found.")
        return redirect(url_for("my_orders"))

    return render_template("checkout.html", show_summary=True, order=order, items=items)


# ---------------- ADMIN ----------------
@app.route("/admin")
def admin_dashboard():
    if not admin_required():
        flash("Admin access required.")
        return redirect(url_for("index"))

    conn = get_db()

    slot_stats = conn.execute("""
        SELECT ts.id, ts.label,
               COUNT(o.id) as orders_count,
               ts.max_orders as max_orders
        FROM time_slots ts
        LEFT JOIN orders o ON o.slot_id = ts.id AND o.status != 'Cancelled'
        GROUP BY ts.id
        ORDER BY ts.id
    """).fetchall()

    pending = conn.execute("""
        SELECT o.id, u.name, ts.label as slot_label, o.total_amount, o.status, o.created_at
        FROM orders o
        JOIN users u ON u.id = o.user_id
        JOIN time_slots ts ON ts.id = o.slot_id
        ORDER BY o.id DESC
        LIMIT 30
    """).fetchall()

    conn.close()
    return render_template("admin_dashboard.html", slot_stats=slot_stats, pending=pending)

@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
def admin_update_status(order_id):
    if not admin_required():
        flash("Admin access required.")
        return redirect(url_for("index"))

    new_status = request.form["status"]
    if new_status not in ("Pending", "Accepted", "Ready", "Picked", "Cancelled"):
        flash("Invalid status.")
        return redirect(url_for("admin_dashboard"))

    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    conn.commit()
    conn.close()

    flash("Order status updated.")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/menu")
def admin_menu():
    if not admin_required():
        flash("Admin access required.")
        return redirect(url_for("index"))

    conn = get_db()
    stall = conn.execute("SELECT * FROM stalls LIMIT 1").fetchone()
    items = conn.execute("SELECT * FROM menu_items WHERE stall_id=? ORDER BY category, name", (stall["id"],)).fetchall()
    conn.close()
    return render_template("admin_menu.html", stall=stall, items=items)

@app.route("/admin/menu/add", methods=["POST"])
def admin_menu_add():
    if not admin_required():
        flash("Admin access required.")
        return redirect(url_for("index"))

    name = request.form["name"].strip()
    price = request.form["price"].strip()
    category = request.form["category"].strip()
    prep = request.form["prep_minutes"].strip()

    if not name or not price.isdigit() or not prep.isdigit():
        flash("Enter valid details.")
        return redirect(url_for("admin_menu"))

    conn = get_db()
    stall = conn.execute("SELECT * FROM stalls LIMIT 1").fetchone()
    conn.execute(
        "INSERT INTO menu_items(stall_id,name,price,category,is_available,prep_minutes) VALUES (?,?,?,?,?,?)",
        (stall["id"], name, int(price), category, 1, int(prep)),
    )
    conn.commit()
    conn.close()
    flash("Item added.")
    return redirect(url_for("admin_menu"))

@app.route("/admin/menu/toggle/<int:item_id>")
def admin_menu_toggle(item_id):
    if not admin_required():
        flash("Admin access required.")
        return redirect(url_for("index"))

    conn = get_db()
    item = conn.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
    if item:
        new_val = 0 if item["is_available"] == 1 else 1
        conn.execute("UPDATE menu_items SET is_available=? WHERE id=?", (new_val, item_id))
        conn.commit()
    conn.close()

    flash("Availability updated.")
    return redirect(url_for("admin_menu"))

@app.route("/admin/menu/delete/<int:item_id>")
def admin_menu_delete(item_id):
    if not admin_required():
        flash("Admin access required.")
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

    flash("Item deleted.")
    return redirect(url_for("admin_menu"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)