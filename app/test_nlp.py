# from trankit import Pipeline
# from nlp import *

#import mysql.connector
import MySQLdb


db = MySQLdb.connect(
  host="172.23.233.167",
  user="root",
  password="root",
  database="gru-acb-stt"
)
cursor = db.cursor()
cursor.execute("SELECT * FROM stt_call")
calls = cursor.fetchall()
for row in calls:
    print(row['id'])
    
