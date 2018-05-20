import sqlite3 as sql 

# fields --> filename, created at, min, max, std, mean, blob

db = sql.connect('drats.db')
cur = db.cursor()

CREATE_TABLE = """CREATE TABLE drats_data(id integer primary key autoincrement, filename varchar(20), min REAL, max REAL, std REAL, mean REAL, blob_count INTEGER, time varchar(20))"""

cur.execute(CREATE_TABLE)
db.commit()	
db.close()
