# import tools
import sqlite3
from datetime import datetime
from sqlite3 import Error

from flask import Flask, render_template, request, session, redirect
from flask_bcrypt import Bcrypt


app = Flask(__name__)
bcrypt = Bcrypt(app)
DATABASE = "C:/Users/28014/OneDrive - Wellington College/13DTS/dictionary/Harry.db"
app.secret_key = "banana" # to sign session cookies for protection


# enable the foreign keys
def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)
    return None


# logging state of the user
def is_logged_in():
    # session are created after login
    if session.get("email") is None:  # if there is no email the user are not logged in
        print("not logged in")
        return False
    else:
        print("logged in")
        return True


# logging as a teacher or a student
def is_logged_in_teacher():
    # session are created after login
    if session.get("teacher") == "Y":  # if the user is the teacher
        print("logged in as teacher")
        return True
    else:
        print("logged in as student")
        return False


# creat function to pull categories into a list
def category_list():
    con = create_connection(DATABASE) # create connection to database
    query = "SELECT id, category FROM categories ORDER BY category ASC"  # select category fom
    cur = con.cursor()
    cur.execute(query) # execute the query
    category_list = cur.fetchall()
    cur.close()
    return category_list


# app route to the main page
@app.route('/', methods=['POST', 'GET'])
def home_page():
    english_words = []
    if request.method == 'POST':
        print(request.form)
        search_word = request.form.get('search').strip()  # gets the search from
        con = create_connection(DATABASE) # create connection to database
        query = "SELECT id,  maori, english, image FROM Words WHERE english = ? or maori = ? OR level=?" # get data from database
        cur = con.cursor()
        cur.execute(query, (search_word, search_word, search_word)) # execute the query
        english_words = cur.fetchall() # put words into a list
        cur.close()
    return render_template('home.html', categories=category_list(), logged_in=is_logged_in(),
                           logged_in_teacher=is_logged_in_teacher(), english_words=english_words)



# app route to the add category page
@app.route('/add_category', methods=['POST', 'GET'])
def add_category():
    if request.method == 'POST':
        print(request.form)
        category = request.form.get('category').title().strip()  # gets the category from
        # connect to database
        con = create_connection(DATABASE)
        query = "INSERT INTO categories (category) VALUES (?)"  # insert categories into my database
        cur = con.cursor()
        cur.execute(query, (category,))  # execute the query
        con.commit()
        con.close()
        return redirect('/')

    return render_template('add_category.html', categories=category_list(), logged_in=is_logged_in(),
                           logged_in_teacher=is_logged_in_teacher(), )


# app route to contact
@app.route('/contact')
def contact():
    return render_template("contact.html", categories=category_list(), logged_in=is_logged_in(),
                           logged_in_teacher=is_logged_in_teacher())


# app route to log in
@app.route('/login', methods=['POST', 'GET'])
def login():
    # if logged in user are not able to come back to login page
    if is_logged_in():
        return redirect('/')

    if request.method == 'POST':
        email = request.form.get('email').lower().strip()  # gets the email from the form
        password = request.form.get('password')  # gets the password from the form

        # creat connection to database
        con = create_connection(DATABASE)
        query = "SELECT id, fname, password, lname, teacher FROM User WHERE email=?"  # select user data from database
        cur = con.cursor()
        cur.execute(query, (email,))  # excute the query
        user_data = cur.fetchall() # put data into a list
        con.close()

        # check if userdata are same to the database
        if user_data:
            user_id = user_data[0][0]
            fname = user_data[0][1]
            db_password = user_data[0][2]
            lname = user_data[0][3]
            teacher = user_data[0][4]
            print(user_id, fname, lname, teacher)

        # if it is not equal return to the URl belwo
        else:
            return redirect("/login?error=Incorrect+username+or+password")

        # if password are not same
        if not bcrypt.check_password_hash(db_password, password):
            return redirect(request.referrer + "?error=Email+invalid+or+password+incorrect")

        # create session for user
        session['email'] = email
        session['userid'] = user_id
        session['first_name'] = fname
        session['last_name'] = lname
        session['teacher'] = teacher
        print(session)

        return redirect("/")

    return render_template("login.html", categories=category_list(), logged_in=is_logged_in(),
                           logged_in_teacher=is_logged_in_teacher())


# app route to signup
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    # if logged in, user shouldn't be able to sign up
    if is_logged_in():
        return redirect('/')
    # gets data from form
    if request.method == 'POST':
        print(request.form)
        fname = request.form.get('fname').title().strip()
        lname = request.form.get('lname').title().strip()
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        password2 = request.form.get('password2')
        role = request.form.get('role')

        if len(fname) < 2:  # first name has to be more than one character
            return redirect("\signup?error=FirstName+must+be+at+least+2+charactes")

        if len(lname) < 2:  # last name has to be more than one character
            return redirect("\signup?error=LastName+must+be+at+least+2+charactes")

        if password2 != password:  # check if the pass word are the same
            return redirect("\signup?error=Confirm+Password+are+not+same+as+password")

        if len(password) < 8:  # password have to be more than seven characters
            return redirect("\signup?error=Password+must+be+at+least+8+characters")

        hashed_password = bcrypt.generate_password_hash(password)  # hash the password, protects user password.

        con = create_connection(DATABASE)
        # insert user data to database
        query = "INSERT INTO User (fname, lname, email, password, teacher) VALUES (?,?,?,?,?)"

        cur = con.cursor()
        try:
            cur.execute(query, (fname, lname, email, hashed_password, role))  # execute the query
        # if the email is not unique it will have sqlite3 error
        except sqlite3.IntegrityError:
            return redirect('/signup?error=Email+is+already+used')
        con.commit()
        con.close()
        return redirect('/login')

    return render_template('signup.html', logged_in=is_logged_in(), categories=category_list(),
                           logged_in_teacher=is_logged_in_teacher())


# app route logout
@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]  # quit session
    print(list(session.keys()))
    return redirect(request.referrer + '?message=See+you+next+time!')


# app route category
@app.route('/category/<category_id>', methods=['POST', 'GET'])
def category(category_id):
    # get data from form
    if request.method == 'POST':
        print(request.form)
        maori = request.form.get('maori').lower().strip()
        english = request.form.get('english').lower().strip()
        level = request.form.get('level').lower().strip()
        definition = request.form.get('definition')
        timestamp = datetime.now()
        category = category_id
        user_id = session['userid']
        username = session['first_name'] + " " + session['last_name']
        noimage = "noimage"
        invalid_characters = "!@#$%^&*()<>?:{}_+|-=\][;'/.,"

        # check if there is any invalid characters in maori or english.
        for i in invalid_characters:
            if i in maori or i in english:
                # if is invalid characters in maori or english, the code below will return user to the url.
                return redirect(f"/category/{category_id}?error=invalid+characters+in+maori+or+english")

        con = create_connection(DATABASE)  # create connection to database
        query = "SELECT id FROM Words WHERE english = ? and maori = ?"  # get data from database
        cur = con.cursor()
        cur.execute(query, (maori, english,)) # execute the query
        try:
            cur.fetchall()[0][0] # if there is value in the fetchall it will return the following URl
            return redirect(f"/category/{category_id}?error=word+trying+to+add+is+already+in+the+dictionary")
        # if not it will insert the word to the database.
        except IndexError:

            # insert the word to the database
            query = "INSERT INTO Words (maori, english, level, definition, timestamp, category_id, user_id, username, " \
                "image) VALUES (?,?,?,?,?,?,?,?,?) "

            cur = con.cursor()
            # execute the query
            cur.execute(query, (maori, english, level, definition, timestamp, category, user_id, username, noimage))

        con.commit()
        con.close()

    # connect to database
    con = create_connection(DATABASE)
    query = "SELECT id, category FROM categories WHERE id = ?"  # select data from database
    cur = con.cursor()
    cur.execute(query, (category_id,))
    category = cur.fetchall()
    print(category_id, category)
    # Select the data from my database
    query = "SELECT id, maori, english, image FROM Words WHERE category_id=? ORDER BY maori ASC"
    cur = con.cursor()
    cur.execute(query, (category_id,))  # executes the query
    words_list = cur.fetchall()  # put result into a list
    con.close()

    return render_template('category.html', categories=category_list(), words_list=words_list, category=category[0],
                           logged_in=is_logged_in(), catID=category_id, logged_in_teacher=is_logged_in_teacher())


# app route to words
@app.route('/word/<wordid>', methods=['POST', 'GET'])
def word(wordid):
    # get data from form
    if request.method == 'POST':
        print(request.form)
        maori = request.form.get('maori').lower().strip()
        english = request.form.get('english').lower().strip()
        level = request.form.get('level').lower().strip()
        definition = request.form.get('definition')
        timestamp = datetime.now()
        user_id = session['userid']
        username = session['first_name'] + " " + session['last_name']
        word_id = wordid
        invalid_characters = "!@#$%^&*()<>?:{}_+|-=\][;'/.,"

        # check if there is any invalid characters in maori or english.
        for i in invalid_characters:
            if i in maori or i in english:
                # if is invalid characters in maori or english, the code below will return user to the url.
                return redirect(f"/word/{wordid}?error=invalid+characters+in+maori+or+english")
        con = create_connection(DATABASE)  # create connection to database
        query = "SELECT id FROM Words WHERE english = ? and maori = ?"  # get data from database
        cur = con.cursor()
        cur.execute(query, (maori, english,))  # execute the query
        try:
            cur.fetchall()[0][0]  # if there is value in the fetchall it will return the following URl
            return redirect(f"/word/{wordid}?error=word+trying+to+edit+is+already+in+the+dictionary")
        # if not it will insert the word to the database.
        except IndexError:
            # replace the word in the database
            query = "UPDATE Words SET maori = ?, english =?, level= ?, definition = ?, timestamp = ?, user_id = ?, " \
                    "username = ? WHERE id = ? "
            cur = con.cursor()
            cur.execute(query,
                        (maori, english, level, definition, timestamp, user_id, username, word_id))  # execute the query
            con.commit()
            con.close()

    # create connection to database
    con = create_connection(DATABASE)
    query = "SELECT id, maori, english, definition, level, timestamp, user_id, image, username FROM Words WHERE id = ?" # get the data from database
    cur = con.cursor()
    cur.execute(query, (wordid,)) # execute query
    words = cur.fetchall() # put words into a list
    con.close()

    return render_template('word.html', logged_in=is_logged_in(), categories=category_list(), words=words,
                           logged_in_teacher=is_logged_in_teacher())


# app route for deleting worlds
@app.route('/deleteword/<word_id>/<maori>')
def delete_word_confirmation(word_id, maori):
    # connect database
    con = create_connection(DATABASE)
    # select data from words
    query = "SELECT id, maori, english, definition, level, timestamp, user_id, image, username FROM Words WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (word_id,))
    words = cur.fetchall()  # put data into a list
    con.close()

    return render_template("deleteword.html", categories=category_list(), logged_in=is_logged_in(), words=words,
                           logged_in_teacher=is_logged_in_teacher())


# app route for the delete button
@app.route('/deleteword/<word_id>')
def delete_word(word_id):
    print("Remove: {}".format(word_id))
    query = "DELETE FROM Words WHERE id =? ;"  # delete the data in the database
    con = create_connection(DATABASE)  # creat connection to the database
    cur = con.cursor()
    cur.execute(query, (word_id,))  # execute the query
    con.commit()
    con.close()
    return redirect("/")


# app route to delete category
@app.route('/deletecategory/<category_id>/<category>')
def delete_category_confirmation(category_id, category):
    con = create_connection(DATABASE)  # connect to the database
    cur = con.cursor()
    query = "SELECT id, category FROM categories WHERE id = ?"  # select data from categories
    cur.execute(query, (category_id,))  # execute the query
    Categories = cur.fetchall()  # put result into a list

    # Select the data from my database
    query = "SELECT id, maori, english, image FROM Words WHERE category_id=? ORDER BY maori ASC"

    cur = con.cursor()
    cur.execute(query, (category_id,))  # executes the query
    words_list = cur.fetchall()  # put result into a list
    con.close()

    return render_template("deletecategory.html", categories=category_list(), logged_in=is_logged_in(),
                           Categories=Categories, words_list=words_list, logged_in_teacher=is_logged_in_teacher())


# app route for the delete category button
@app.route('/deletecategory/<category_id>')
def delete_category(category_id):
    print("Remove: {}".format(category_id))
    query = "DELETE FROM Words WHERE category_id =? ;"  # delete all the words
    con = create_connection(DATABASE)  # connect to the database
    cur = con.cursor()
    cur.execute(query, (category_id,))  # execute the query
    con.commit()
    query = "DELETE FROM categories WHERE id =? ;"  # delete the categories
    cur = con.cursor()
    cur.execute(query, (category_id,))  # execute the query
    con.commit()
    con.close()
    return redirect('/')



# run the website
if __name__ == '__main__':
    app.run()
