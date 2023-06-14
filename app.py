import sqlite3
from datetime import datetime
from hashids import Hashids
from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inavihsdottech'


connection = sqlite3.connect('database.db')

c = connection.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS urls(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            original_url TEXT NOT NULL,
            clicks INTEGER NOT NULL DEFAULT 0
        )''')

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


hashids = Hashids(min_length=4, salt=app.config['SECRET_KEY'])


@app.route('/', methods=('GET', 'POST'))
def index():
    conn = get_db_connection()
    short_url = None
    if request.method == 'POST':
        url = request.form['url']
        if not url:
            flash('URL Required!!!')
            return redirect(url_for('index'))

        created = str(datetime.now()).split(".")[0]
        obj = conn.execute('INSERT INTO urls (original_url, created, updated_at) VALUES (?, ?, ?)', (url, created, created))
        conn.commit()
        conn.close()

        url_id = obj.lastrowid
        short_url = request.host_url + hashids.encode(url_id)
    return render_template('index.html', short_url=short_url)


@app.route('/<id>')
def url_redirect(id):
    conn = get_db_connection()

    original_id = hashids.decode(id)
    if original_id:
        original_id = original_id[0]
        query = 'SELECT original_url, clicks FROM urls WHERE id = ?'
        url_data = conn.execute(query, (original_id,)).fetchone()
        if url_data:
            original_url, clicks = url_data['original_url'], url_data['clicks'] + 1
            updated_at = str(datetime.now()).split(".")[0]
            conn.execute('UPDATE urls SET clicks = ?, updated_at = ? WHERE id = ?', (clicks, updated_at, original_id))
            conn.commit()
            conn.close()
            return redirect(original_url)
    flash('Invalid URL')
    return redirect(url_for('index'))


@app.route('/track')
def track():
    conn = get_db_connection()
    db_urls = conn.execute('SELECT id, created, updated_at, original_url, clicks FROM urls').fetchall()
    conn.close()
    urls = [dict(url, short_url=request.host_url + hashids.encode(url['id'])) for url in db_urls]
    return render_template('analytics.html', urls=urls)
