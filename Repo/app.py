from flask import Flask, render_template, session, redirect, flash, request, url_for
from functools import wraps
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
import os
import mysql.connector

app = Flask(__name__)

# uploads configuration
UPLOAD_FOLDER = '/home/kuzco/Desktop/Projects/Doc-Repo/Repo/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'xlsx', 'pptx'}

# App configurations
app.config['SECRET_KEY'] = b'da72b3628c9b68a709b2'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'


# Databse connection
conn = mysql.connector.connect(host = '127.0.0.1', user = 'root', passwd = '', database = 'repo')
cur = conn.cursor(dictionary = True)


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

# Main view decorator
@app.route('/home')
def index():
	cur.execute("SELECT * FROM repo.documents")
	docs = cur.fetchall()
	return render_template("dashboard.html", title = "Dashboard", docs = docs)


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
		return redirect(url_for('index'))
	return render_template('signup.html', title = 'Register')    



# Login form decorator
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
	    		return redirect(url_for('index'))
	    flash('Login credentials do not match, please try again!', 'warning')
	return render_template('login.html', title = 'Login to your account')



# Logout decorator
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out!', 'success')
	return redirect(url_for('index'))


 # Function to check for allowed files to upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



 # Upload decorator
@app.route('/upload', methods=['GET', 'POST'])
@is_logged_in
def upload_file():
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part', 'warning')
			return redirect(request.url)
		file = request.files['file']
		if file.filename == '':
			flash('No selected file', 'warning')
			return redirect(request.url)
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			flash('Uploaded successfully', 'success')
			return redirect(url_for("index"))


# Search content
@app.route("/search", methods = ['GET', 'POST'])
def search():
	if request.method == 'POST':
		search = request.form['search']
		cur.execute("SELECT * FROM repo.documents WHERE docName LIKE '%s' " % search)
		results = cur.fetchall()
		if not results:
			flash('No results were found', 'warning')
			return redirect(url_for('index'))
		else:
			if len(results) > 1:
				flash('Found ' + str(len(results)) + ' matching results', 'success')
			else:
				flash('Found ' + str(len(results)) + ' matching result', 'success')
			return redirect(url_for('index'))			



if __name__ == '__main__':
    app.run(debug = True)