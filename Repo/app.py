from flask import Flask, render_template, session, redirect, flash, request, url_for
from functools import wraps
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
import os

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
# conn = mysql.connector.connect(host = '127.0.0.1', user = 'root', passwd = '', database = '')
# cur = conn.cursor(dictionary = True)


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
    return render_template("dashboard.html", title = "Dashboard")


# Registration form decorator
@app.route('/register', methods = ['GET', 'POST'])
def register():
	return render_template('signup.html')    


# Login form decorator
@app.route('/login', methods = ['GET', 'POST'])
def login():
	return render_template('login.html')

 # Function to check for allowed files to upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

 # Upload decorator
@app.route('/upload', methods=['GET', 'POST'])
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


if __name__ == '__main__':
    app.run(debug = True)