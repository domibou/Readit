from flask import render_template, session, request, redirect, url_for, flash
from mysql import connector
from app import app

# Utilisez vos informations de connexion à MySQL ici
db_user = 'root'
db_password = ''
db_name = 'redditclone'


@app.route('/')
def main():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        # Exemple de la DB pour tester le login sur le site:
        # username: WebDeveloper_
        # password: ia
        username = request.form['username']
        password = request.form['password']

        # Conserver ce format dans toutes les requêtes pour éviter les injections SQL (avec placeholder %s)
        # La query va toujours retourner 1 ou 0 tuple pcq username est unique
        query = f"SELECT * FROM User WHERE username = %s"
        val = (f"{username}", )

        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()
        cursor.execute(query, val)
        result = cursor.fetchone()

        if result is None:
            flash("Incorrect username or password")
            return render_template('login.html')
        elif result[6] == password:
            session['user'] = result[1]
            return render_template('home.html')
        else:
            flash("Incorrect username or password")
            return render_template('login.html')
    else:
        return render_template('login.html')
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/signup')
def signup():
    return render_template('signup.html')

