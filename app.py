import sqlite3
from datetime import datetime
from sqlite3 import Error

from flask import Flask, render_template, request, session, redirect
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
DATABASE = "C:/Users/18052/OneDrive - Wellington College/13DTS/dictionary/Harry.db"
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
        query = "INSERT INTO categories (category) VALUES (?)"
        cur = con.cursor()
        cur.execute(query, (category,))
        con.commit()
        con.close()
        return redirect('/')

    error = request.args.get('error')
    if error is None:
        error = ""

    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)

    category_list = cur.fetchall()
    cur.close()

    return render_template('home.html', error=error, categories=category_list, logged_in=is_logged_in(), logged_in_teacher=is_logged_in_teacher())


@app.route('/contact')
def contact():
    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)

    category_list = cur.fetchall()
    cur.close()
    return render_template("contact.html", categories=category_list, logged_in=is_logged_in(), logged_in_teacher=is_logged_in_teacher())


@app.route('/login', methods=['POST', 'GET'])
def login():
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')

        con = create_connection(DATABASE)
        query = "SELECT id, fname, password, lname, teacher FROM User WHERE email=?"
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        if user_data:
            user_id = user_data[0][0]
            fname = user_data[0][1]
            db_password = user_data[0][2]
            lname = user_data[0][3]
            teacher = user_data[0][4]
            print(user_id, fname, lname, teacher)

        else:
            return redirect("/login?error=Incorrect+username+or+password")

        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        session['email'] = email
        session['userid'] = user_id
        session['first_name'] = fname
        session['last_name'] = lname
        session['teacher'] = teacher
        print(session)

        return redirect("/")

    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)

    category_list = cur.fetchall()
    cur.close()

    return render_template("login.html", categories=category_list, logged_in=is_logged_in(), logged_in_teacher=is_logged_in_teacher())


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
        query = "INSERT INTO User (fname, lname, email, password) VALUES (?,?,?,?)"

        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password))
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()
        return redirect('/login')

        return render_template("signup.html")

    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)

    category_list = cur.fetchall()
    cur.close()
    return render_template('signup.html', logged_in=is_logged_in(), categories=category_list, logged_in_teacher=is_logged_in_teacher())


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+next+time!')


@app.route('/category/<category_id>', methods=['POST', 'GET'])
def category(category_id):
    if request.method == 'POST':
        print(request.form)
        maori = request.form.get('maori').title().strip()
        english = request.form.get('english').title().strip()
        level = request.form.get('level').lower().strip()
        definition = request.form.get('definition')
        timestamp = datetime.now()
        category =category_id
        user_id = session['userid']
        username = session['first_name'] + " " +session['last_name']
        noimage = "noimage"

        con = create_connection(DATABASE)
        query = "INSERT INTO Words (maori, english, level, definition, timestamp, category_id, user_id, username, image) VALUES (?,?,?,?,?,?,?,?,?)"

        cur = con.cursor()

        cur.execute(query, (maori, english, level, definition, timestamp, category, user_id, username, noimage))

        con.commit()
        con.close()

    # connect to database
    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    query = "SELECT id, category FROM categories WHERE id = ?"
    cur.execute(query, (category_id,))
    category = cur.fetchall()
    print(category_id, category)

    # Select the data from my database
    query = "SELECT id, maori, english, image FROM Words WHERE category_id=? ORDER BY maori ASC"

    cur = con.cursor()
    cur.execute(query, (category_id,))  # executes the query
    words_list = cur.fetchall()  # put result into a list
    con.close

    return render_template('category.html', categories=category_list, words_list=words_list, category=category[0],
                           logged_in=is_logged_in(), catID=category_id, logged_in_teacher=is_logged_in_teacher())


@app.route('/word/<wordid>', methods=['POST', 'GET'])
def word(wordid):
    if request.method == 'POST':
        print(request.form)
        maori = request.form.get('maori').title().strip()
        english = request.form.get('english').title().strip()
        level = request.form.get('level').lower().strip()
        definition = request.form.get('definition')
        timestamp = datetime.now()
        user_id = session['userid']
        username = session['first_name'] + " " + session['last_name']
        word_id = wordid

        con = create_connection(DATABASE)
        query = "UPDATE Words SET maori = ?, english =?, level= ?, definition = ?, timestamp = ?, user_id = ?, " \
                "username = ? WHERE id = ? "
        cur = con.cursor()
        cur.execute(query, (maori, english, level, definition, timestamp, user_id, username, word_id))
        con.commit()
        con.close()


    con = create_connection(DATABASE)
    query = "SELECT id, maori, english, definition, level, timestamp, user_id, image, username FROM Words WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (wordid,))
    words = cur.fetchall()
    con.close

    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)

    category_list = cur.fetchall()
    cur.close()
    return render_template('word.html', logged_in=is_logged_in(), categories=category_list, words=words, logged_in_teacher=is_logged_in_teacher())

@app.route('/deleteword/<word_id>/<maori>')
def delete_word(word_id, maori):


    con = create_connection(DATABASE)
    query = "SELECT id, maori, english, definition, level, timestamp, user_id, image, username FROM Words WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (word_id,))
    words = cur.fetchall()
    con.close

    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)

    category_list = cur.fetchall()
    cur.close()
    return render_template("deleteword.html", categories=category_list, logged_in=is_logged_in(), words=words, logged_in_teacher=is_logged_in_teacher())

@app.route('/deleteword/<word_id>')
def deleteword(word_id):
    print("Remove: {}".format(word_id))
    query = "DELETE FROM Words WHERE id =? ;"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (word_id,))
    con.commit()
    con.close()
    return redirect('/')

@app.route('/deletecategory/<category_id>/<category>')
def delete_category(category_id, category):
    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories ORDER BY category ASC"
    cur = con.cursor()
    cur.execute(query)
    category_list = cur.fetchall()
    query = "SELECT id, category FROM categories WHERE id = ?"
    cur.execute(query, (category_id,))
    Categories = cur.fetchall()

    # Select the data from my database
    query = "SELECT id, maori, english, image FROM Words WHERE category_id=? ORDER BY maori ASC"

    cur = con.cursor()
    cur.execute(query, (category_id,))  # executes the query
    words_list = cur.fetchall()  # put result into a list
    con.close

    return render_template("deletecategory.html", categories=category_list, logged_in=is_logged_in(), Categories=Categories, words_list=words_list, logged_in_teacher=is_logged_in_teacher())

@app.route('/deletecategory/<category_id>')
def deletecategory(category_id):
    print("Remove: {}".format(category_id))
    query = "DELETE FROM Words WHERE category_id =? ;"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (category_id,))
    con.commit()
    query = "DELETE FROM categories WHERE id =? ;"
    con = create_connection(DATABASE)
    cur = con.cursor()
    cur.execute(query, (category_id,))
    con.commit()
    con.close()
    return redirect('/')

def is_logged_in():
    if session.get("email") is None:
        print("not logged in")
        return False
    else:
        print("logged in")
        return True
def is_logged_in_teacher():
    if session.get("teacher") == "Y":
        print("logged in as teacher")
        return True
    else:
        print("logged in as student")
        return False

if __name__ == '__main__':
    app.run()
