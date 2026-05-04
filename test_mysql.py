import MySQLdb

try:
    conn = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd="",
        db="finex_db"
    )
    print("CONEXIÓN OK")
except Exception as e:
    print("ERROR:", e)