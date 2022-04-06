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


@app.route('/', methods=['POST', 'GET'])
def hello_world():
    if request.method == 'POST':
        print(request.form)
        category = request.form.get('category').title().strip()

        con = create_connection(DATABASE)
        query = "INSERT INTO dictionary (category) VALUES (?)"
        cur = con.cursor()
        cur.execute(query, (category, ))
        con.commit()
        con.close()
        return redirect('/')

    return render_template("home.html")

    error = request.args.get('error')
    if error is None:
        error = ""

    return render_template('home.html', error=error, logged_in=is_logged_in())


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
        query = "SELECT id, fname, password FROM user WHERE email=?"
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

        return redirect("/")

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
        query = "INSERT INTO customer (fname, lname, email, password) VALUES (?,?,?,?)"

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


@app.route('/category/<category_id>')
def addtocategory(category_id):
    userid = session['userid']
    timestamp = datetime.now()
    print("user {} would like to add {} to the dictionary at {}".format(userid, category_id, timestamp))

    query = "INSERT INTO Dictionary(id,userid,category_id,timestamp) VALUES (NULL,?,?,?)"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (userid, category_id, timestamp))
    con.commit()
    con.close()
    return redirect(request.referrer)


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


if __name__ == '__main__':
    app.run()
