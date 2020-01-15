@app.route("/upload", methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']

        # Get filename and folders
        file_name = secure_filename(file.filename)
        directory = UPLOADS_DEFAULT_URL
        upload_folder = app.config['UPLOAD_FOLDER']

        if file.filename == '':
            flash('No file part', 'warning')
            return redirect(request.url)
        if file and allowed_file(file.filename):

            save_dir = os.path.join(upload_folder, directory)

            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            complete_path = os.path.join(save_dir, file_name)
            file.save(complete_path)
            size = os.stat(complete_path).st_size

            # create our file from the model and add it to the database
            dbfile = File(file_name, directory, size, file.mimetype)

            g.user.uploads.append(dbfile)
            db.session().add(dbfile)
            db.session().commit()

            if "image" in dbfile.mimetype:
                get_thumbnail(complete_path, "100")
                thumbnail_url = request.host_url + 'thumbs/' + directory
            else:
                thumbnail_url = ""

            url = request.host_url + 'uploads/' + directory
            delete_url = url
            delete_type = "DELETE"

            file = {"name": file_name, "url": url, "thumbnailUrl": thumbnail_url, "deleteUrl": delete_url,
                    "deleteType": delete_type}
            return jsonify(files=[file])

        else:
            return jsonify(files=[{"name": file_name, "error": responds['FILETYPE_NOT_ALLOWED']}])


@myapp.route('/delete')
@is_logged_in
def delete_file():
    uniqueid = request.args.get("docId")

    if session['username']:
        upload_folder = app.config['UPLOAD_FOLDER']
        try:
            folder = os.path.join(upload_folder, file.unique_id)
            complete_path = os.path.join(folder, file.name)

            cur.execute("DELETE FROM repo.documents WHERE docName = 'uniqueid'")
            conn.commit()
            flash("File deleted successfully!", 'success')
            return redirect(url_for('index'))
        except:
            flash("An unexpected error occured!",'warning')
            conn.rollback()
    else:
        flash("Access denied!",'danger')
