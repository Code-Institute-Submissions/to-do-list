import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from forms import RegisterForm, LoginForm
from bson.objectid import ObjectId
import bcrypt 
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route('/')
@app.route('/get_to_do')
def get_to_do():
    if session.get('logged_in'):
        if session['logged_in'] is True:
            who = session["username"]
            query = {"created_by": who}
            to_do = list(mongo.db.to_do.find(query))
            return render_template("to_do.html", to_do=to_do)
    to_do = list(mongo.db.to_do.find())
    return render_template("to_do.html", to_do=to_do)
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login handler"""
    if session.get('logged_in'):
        if session['logged_in'] is True:
            return redirect(url_for('get_to_do', title="Sign In"))

    form = LoginForm()

    if form.validate_on_submit():
        # get all users
        users = mongo.db.users
        # try and get one with same name as entered
        db_user = users.find_one({'name': request.form['username']})

        if db_user:
            # check password using hashing
            if bcrypt.hashpw(request.form['password'].encode('utf-8'),
                             db_user['password']) == db_user['password']:
                session['username'] = request.form['username']
                session['logged_in'] = True
                # successful redirect to home logged in
                return redirect(url_for('get_to_do', title="Logged In", form=form))
            # must have failed set flash message
            flash('Invalid username/password combination')
    return render_template("login.html", title="Sign In", form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handles registration functionality"""
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        # get all the users
        users = mongo.db.users
        # see if we already have the entered username
        existing_user = users.find_one({'name': request.form['username']})

        if existing_user is None:
            # hash the entered password
            hash_pass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            # insert the user to DB
            users.insert_one({'name': request.form['username'],
                          'password': hash_pass,
                          'email': request.form['email']})
            session['username'] = request.form['username']
            return redirect(url_for('get_to_do'))
        # duplicate username set flash message and reload page
        flash('Sorry, that username is already taken - use another')
        return redirect(url_for('register'))
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
def logout():
    session.clear()
    return redirect( url_for('login'))


@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        item = {
            "item_name": request.form.get("item_name"),
            "item_detail": request.form.get("item_detail"),
            "due_date": request.form.get("due_date"),
            "is_urgent": is_urgent,
            "created_by": session["username"]
        }
        mongo.db.to_do.insert_one(item)
        flash("Item Successfully Added")
        return redirect(url_for('get_to_do'))

    return render_template("add_item.html")


@app.route('/edit_item/<edit_item_id>', methods=['GET','POST'])
def edit_item(edit_item_id):
    edit_item = mongo.db.to_do.find_one({'_id': ObjectId(edit_item_id)})
    if request.method == "POST":
        is_urgent = "on" if request.form.get("is_urgent") else "off"
        to_do_db = mongo.db.to_do
        to_do_db.update_one({
            '_id': ObjectId(edit_item_id),
        }, 
        {
            '$set': {
                "item_name": request.form["item_name"],
                "item_detail": request.form.get("item_detail"),
                "due_date": request.form.get("due_date"),
                "is_urgent": is_urgent,
            } 
        })
        return redirect(url_for("get_to_do"))
    return render_template("edit_item.html", edit_item=edit_item)


@app.route('/delete_item/<delete_item_id>')
def delete_item(delete_item_id):
    to_do_db = mongo.db.to_do
    to_do_db.delete_one({
       '_id': ObjectId(delete_item_id),
     })
    return redirect(url_for('get_to_do'))


if __name__ == '__main__':
    app.run(host=os.environ.get('IP'),
            port=int(os.environ.get('PORT')),
            debug=True)
