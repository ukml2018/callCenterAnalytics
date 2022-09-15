from flask import Flask, render_template
import pyodbc
from flask import request,redirect
import speech_recognition as sr

carsales = Flask(__name__)

def connection():
    s = 'ht-sqlserver22.database.windows.net' 
    d = 'callCenterdb' 
    u = 'adminuser' #Your login
    p = 'Passw0rd!' #Your login password
    cstr = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+s+';DATABASE='+d+';UID='+u+';PWD='+ p
    conn = pyodbc.connect(cstr)
    return conn

@carsales.route("/")
def main():
    cars = []
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT text_message,transaction_type, languag,agent_id FROM dbo.callSentiment")
    for row in cursor.fetchall():
        cars.append({"text_message": row[0], "transaction_type": row[1], "languag": row[2], "agent_id": row[3]})
    conn.close()
    return render_template("carslist.html", cars = cars)

@carsales.route("/add", methods = ['GET','POST'])
def addcar():
    if request.method == 'GET':
        return render_template("addcar.html")
    if request.method == 'POST':
        print("Amit")
        transaction_type = request.form["transaction_type"]
        print("Amit1")
        print(transaction_type)
        languag = request.form["languag"]
        print("Amit2")
        print(languag)
        text_message = request.form["text_message"]
        print("Amit3")
        print(text_message)
        agent_id = 'Clara'
        #print("Amit4")
        print(agent_id)

        conn = connection()
        #print("Amit1.1")
        cursor = conn.cursor()
        cursor.execute("SELECT max(user_id) as user_id FROM dbo.callSentiment")
        for row in cursor.fetchall():
            user_id = row[0] + 1
            print(user_id)
        #print("Amit1.1.2")
        #print("Connection Sucess")
        #print(First_name)
        cursor.execute("INSERT INTO dbo.callSentiment(user_id, transaction_type, languag, text_message,agent_id) VALUES (?, ?, ?, ?,?)", user_id, transaction_type, languag, text_message,agent_id)
        conn.commit()
        conn.close()
        return redirect('/')

if(__name__ == "__main__"):
    app.run(debug=True)
