from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename
import uuid
import stat
import sqlite3

app=Flask(__name__)
DATABASE = app.root_path+"/simple_crud_soft_delete.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    # conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
      CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        year_of_birth INTEGER,
        photo BLOB,
        photo_mime TEXT,
        photo_filename TEXT,
        photo_path TEXT,
        delete_at TIMESTAMP NULL DEFAULT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      );
    """)
    conn.commit()
    conn.close()

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/students')
def students():
  global students

  # from database
  cnx=get_db()
  cursor=cnx.cursor()
  sql='select * from students where delete_at is null;'
  cursor.execute(sql)
  students=cursor.fetchall()
  cursor.close()
  cnx.close()

  return render_template('students.html',students=students)

@app.route('/student_add')
def student_add():
  return render_template('student_add.html')

@app.route('/student_add_submit',methods=['post'])
def student_add_submit():
  # add form data to database
  cnx=get_db()
  cursor = cnx.cursor()

  photo = request.files.get('photo')
  photo_path = None
  if photo and photo.filename:
    ext = os.path.splitext(secure_filename(photo.filename))[1]
    new_filename = f"{uuid.uuid4().hex}{ext}"
    save_dir = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(save_dir, exist_ok=True)
    full_path = os.path.join(save_dir, new_filename)
    photo.save(full_path)
    os.chmod(full_path, stat.S_IRUSR | stat.S_IWUSR)
    photo_path = f"uploads/{new_filename}"

  sql = (
    'insert into students(name, photo_path) '
    'values (?, ?)'
  )

  print('name value in form:',request.form.get('student_name'))
  data=(request.form.get('student_name'), photo_path)
  cursor.execute(sql,data)
  cnx.commit()
  cursor.close()
  cnx.close()

  # from database
  cnx=get_db()
  cursor = cnx.cursor()
  sql = 'select * from students'
  cursor.execute(sql)
  students = cursor.fetchall()
  cursor.close()
  cnx.close()
  return render_template('students.html',students=students)

@app.route('/student_del')
def students_del(name=None):
    cnx = get_db()
    cursor = cnx.cursor()

    student_id = request.args.get('id')

    query = "select photo_path from students where id=?"
    cursor.execute(query, (student_id,))
    row = cursor.fetchone()

    if row and row[0]:
        photo_path = row[0]
        full_path = os.path.join(app.root_path, 'static', photo_path)

        if os.path.exists(full_path):
            os.remove(full_path)

    query = "UPDATE students SET delete_at = CURRENT_TIMESTAMP WHERE id = ?"
    cursor.execute(query, (student_id,))
    cnx.commit()

    cursor.close()
    cnx.close()
    return redirect(url_for('students'))

@app.route('/submit_student_upd', methods=["post"])
def submit_student_upd():
    cnx = get_db()
    cursor = cnx.cursor()

    photo = request.files.get('photo')

    photo_path = None
    if photo and photo.filename:
        # splittext: split extension from filename
        ext = os.path.splitext(secure_filename(photo.filename))[1]
        new_filename = f"{uuid.uuid4().hex}{ext}"
        save_dir = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(save_dir, exist_ok=True)
        full_path = os.path.join(save_dir, new_filename)
        photo.save(full_path)
        os.chmod(full_path, stat.S_IRUSR | stat.S_IWUSR)
        photo_path = f"uploads/{new_filename}"

        upd_stmt = (
            "update students "
            "set name=?, photo_path=? "
            "where id=?"
        )
        data = (
            request.form['name'],
            photo_path,
            request.form['id']
        )
    else:
        upd_stmt = (
            "update students "
            "SET name=?"
            "where id=?"
        )
        data = (request.form['name'], request.form['id'])
        print(data)
    cursor.execute(upd_stmt, data)
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for('students'))

@app.route('/student_upd')
def students_upd(name=None):
    cnx = get_db()
    cursor = cnx.cursor()

    query = "select * from students where id=?"
    cursor.execute(query, (request.args.get('id'),))

    student=cursor.fetchall()[0]

    cursor.close()
    cnx.close()
    return render_template('student_upd.html', id=student[0],name=student[1])

if __name__ == "__main__":
  init_db()  
  app.run(debug=True, host="0.0.0.0")
