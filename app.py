from flask import Flask, render_template, request, session, redirect
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt
from datetime import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)
DATABASE = "Harry.db"
app.secret_key = "banana"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/')
def hello_world():
    return render_template("home.html", logged_in=is_logged_in())


@app.route('/menu')
def menu():
    con = create_connection(DATABASE)
    query = "SELECT name, description, volume, image, price, id FROM product"
    cur = con.cursor()
    cur.execute(query)

    product_list = cur.fetchall()
    cur.close()

    return render_template("menu.html", products=product_list, logged_in=is_logged_in())


@app.route('/contact')
def contact():
    return render_template("contact.html", logged_in=is_logged_in())


@app.route('/login', methods=['POST', 'GET'])
def login():
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = "SELECT id, first_name, password FROM customer WHERE email=?"
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            first_name = user_data[0][1]
            db_password = user_data[0][2]
            print(user_id, first_name)

        else:
            return redirect("/login?error=Incorrect+username+or+password")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['userid'] = user_id
        session['first_name'] = first_name
        print(session)

        return redirect("/menu")

    return render_template("login.html", logged_in=is_logged_in())


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')

        if len(fname) < 2:
            return redirect("\signup?error=FirstName+must+be+at+least+2+charactes")

        if len(lname) < 2:
            return redirect("\signup?error=LastName+must+be+at+least+2+charactes")

        if password2 != password:
            return redirect("\signup?error=LastName+must+be+at+least+2+charactes")

        if len(password) < 8:
            return redirect("\signup?error=Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DATABASE)
        query = "INSERT INTO customer (first_name, surname, email, password) VALUES (?,?,?,?)"

        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()
        return redirect('/login')

    return render_template("signup.html")

    error = request.args.get('error')
    if error is None:
        error = ""

    return render_template('signup.html', error=error, logged_in=is_logged_in())


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+next+time!')


def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print("logged in")
        return True


@app.route('/addtocart/<productid>')
def addtocart(productid):
    try:
        productid = int(productid)
    except ValueError:
        print("{} is not an integer".format(productid))
        return redirect(request.referrer + "?error=Invalid+product+id")

    userid = session['userid']
    timestamp = datetime.now()
    print("user {} would like to add {} to the cart at {}".format(userid, productid, timestamp))

    query = "INSERT INTO cart(id,userid,productid,timestamp) VALUES (NULL,?,?,?)"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (userid, productid, timestamp))
    con.commit()
    con.close()
    return redirect(request.referrer)


@app.route('/cart')
def render_cart():
    userid = session['userid']
    query = "SELECT productid FROM cart WHERE userid=?;"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (userid,))
    product_ids = cur.fetchall()
    print(product_ids)

    for i in range(len(product_ids)):
        product_ids[i] = product_ids[i][0]
    print(product_ids)

    unique_product_ids = list(set(product_ids))
    print(unique_product_ids)

    for i in range(len(unique_product_ids)):
        product_count = product_ids.count(unique_product_ids[i])
        unique_product_ids[i] = [unique_product_ids[i], product_count]
    print(unique_product_ids)

    query = """SELECT name, price FROM product where id = ?;"""
    for item in unique_product_ids:
        cur.execute(query, (item[0],))
        item_details = cur.fetchall()
        print(item_details)
        item.append(item_details[0][1])
        item.append(item_details[0][1])

    con.close()
    print(unique_product_ids)

    return render_template('cart.html', cart_data=unique_product_ids, logged_in=is_logged_in())


@app.route('/removefromcart/<productid>')
def remove_from_cart(productid):
    print("Remove: {}".format(productid))
    return redirect('/cart')


@app.route('/removeonefromcart/<product_id>')
def render_from_cart(product_id):
    print("Remove: {}".format(product_id))
    customer_id = session['customerid']
    query = "DELETE FROM cart WHERE id =(SELECT MIN(id) FROM cart WHERE productid=? and customerid=?);"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (product_id, customer_id))
    con.commit()
    con.close()
    return redirect('/cart')


if __name__ == '__main__':
    app.run()
