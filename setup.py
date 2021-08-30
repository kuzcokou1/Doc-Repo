# Imports
from flask import Flask, render_template, session, redirect, flash, request, url_for
from functools import wraps
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
import os, sys, string, random
import mysql.connector
import subprocess
import psycopg2

# App instance
app = Flask(__name__)


# uploads configuration
UPLOAD_FOLDER = '/static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}
UPLOADS_DEFAULT_URL = '/'


# App configurations
app.config['SECRET_KEY'] = b'da72b3628c9b68a709b2'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


# Databse connection
conn = mysql.connector.connect(host = 'localhost', user = 'root', passwd = '', database = '')
cur = conn.cursor()


# Check if a user is logged in
# Prevents unwanted access to a given page
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			return render_template('403.html')
	return wrap


# Login form decorator
@app.route('/')
@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
	    username = request.form['username']
	    password = request.form['password']

	    cur.execute("SELECT * FROM repo.users WHERE users.username = '%s'" % (username))
	    data = cur.fetchall()
	    for row in data:
	    	if sha256_crypt.verify(password, row['pwd']) == False:
	    		flash('Passwords do not match, please try again!', 'danger') 
		    	return redirect(url_for('login'))  
	    	else:
	    		session['logged_in'] = True
	    		session['username'] = username
	    		flash('You are now logged in', 'success')
	    		return redirect(url_for('dashboard'))
	    flash('Login credentials do not match, please try again!', 'warning')
	return render_template('login.html', title = 'Login to your account')


# Dashboard decorator
@app.route('/dashboard')
@is_logged_in
def dashboard():
	session['logged_in'] = True
	cur.execute("SELECT users.username, documents.username, documents.docId, documents.new_name, documents.docName FROM users INNER JOIN documents ON users.username = documents.username WHERE users.username = '%s' ORDER BY docName DESC LIMIT 6" %session['username'])
	docs = cur.fetchall()
	return render_template("dashboard.html", title = "Dashboard", docs = docs)


# All the documents available 
@app.route('/view_all')
@is_logged_in
def view_all():
	cur.execute("SELECT users.username, documents.username, documents.docId, documents.new_name, documents.docName FROM users INNER JOIN documents ON users.username = documents.username WHERE users.username = '%s' ORDER BY docName DESC" %session['username'])
	results = cur.fetchall()
	return render_template("view_all.html", title = "All documents", results = results)



# Registration form decorator
@app.route('/register', methods = ['GET', 'POST'])
def register():
	if request.method == 'POST':
		first = request.form['first']
		last = request.form['last']
		username = request.form['username']
		email = request.form['email']
		pwd = sha256_crypt.hash(str(request.form['password']))
		
		cur.execute("INSERT INTO repo.users(fname, lname, username, email, pwd) VALUES(%s, %s, %s, %s, %s)", (first, last, username, email, pwd))
		conn.commit()
		flash("Account created for %s!" %username, 'success')
		return redirect(url_for('login'))
	return render_template('signup.html', title = 'Register')    



# Logout decorator
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out!', 'success')
	return redirect(url_for('login'))


 # Function to check for allowed files to upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_extention(filename):
	total = len(filename.split("."))
	return filename.split(".")[total-1]

def randomString(length=10):
	letters = string.ascii_lowercase
	return ''.join(random.choice(letters) for i in range(length))


# Upload decorator
@app.route("/upload", methods=['GET', 'POST'])
@is_logged_in
def upload():
    if request.method == 'POST':
        file = request.files['file']

        # Get filename and folders
        file_name = secure_filename(file.filename).lower()
        directory = UPLOADS_DEFAULT_URL
        upload_folder = app.config['UPLOAD_FOLDER']
        username = session['username']

        if file.filename == '':
            flash('Select a file please!', 'warning')
            return redirect(url_for('dashboard'))

        if file and allowed_file(file.filename):
            save_dir = os.path.join(upload_folder, directory)
            # if not os.path.exists(save_dir):
            #     os.makedirs(save_dir)
            new_name = randomString(16) + '.' + get_extention(file_name)
            complete_path = os.path.join(upload_folder, new_name)
            file.save(complete_path)
            size = os.stat(complete_path).st_size

            # create our file from the model and add it to the database
            cur.execute("INSERT INTO repo.documents (docName, new_name, dir_path, size, username, status) VALUES (%s, %s, %s, %s, %s, %s)", (file_name, new_name, complete_path, size, username, 1))
            conn.commit()
            flash("Uploaded successfully!","success")
            return redirect(url_for('dashboard'))
        else:
        	return redirect(url_for('dashboard'))


def delete_file(id):
	cur.execute("SELECT * FROM repo.documents WHERE documents.docId = '%s'" %id)
	result = cur.fetchone()
	new_name = result['new_name']
	folder = os.path.join(UPLOAD_FOLDER, new_name)
	complete_path = os.path.join(folder, new_name)
	abs_path = UPLOAD_FOLDER + "/" + new_name
	print(abs_path)
	print(complete_path)
	subprocess.call("rm " + abs_path, shell = True)
	return True


# Delete decorator
@app.route('/delete/<int:docId>')
@is_logged_in
def remove_file(docId):
    if session['username']:
    	delete_file(docId)
    	cur.execute("DELETE FROM repo.documents WHERE documents.docId = '%s'" % docId)
    	conn.commit()
    	flash("Deleted file successfully","success")
    	return redirect(url_for('dashboard'))
    	

# Search content
@app.route("/search", methods = ['GET', 'POST'])
def search():
	if request.method == 'POST':
		search = request.form['search']
		cur.execute("SELECT users.username, documents.username, documents.docName, documents.new_name \
			FROM users INNER JOIN documents ON users.username = documents.username \
			WHERE users.username = '%s' \
			OR documents.docName LIKE '%s'" %(session['username'], search))
		results = cur.fetchall()
		if not results:
			flash('No results were found', 'warning')
			return redirect(url_for('dashboard'))
		else:
			if len(results) > 1:
				flash('Found ' + str(len(results)) + ' matching results', 'success')
				return render_template('search.html', title = "Search", results = results)
			else:
				flash('Found ' + str(len(results)) + ' matching result', 'success')
				return render_template('search.html', title = "Search", results = results)
			return redirect(url_for('dashboard'))			




if __name__ == '__main__':
    app.run(debug = True, port = '5432')
