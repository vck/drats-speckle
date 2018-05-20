import sqlite3 as sql

db = sql.connect('drats.db')
cur = db.cursor()
data = ['a.jpg', 0, 10.00, 543.1, 541.1, 121]
cur.execute('INSERT INTO drats_data(filename, min, max, std, mean, blob_count) values (?, ?, ?, ?, ?, ?)', data)
db.commit()
