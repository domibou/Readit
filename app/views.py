from flask import render_template, session, request, redirect, url_for, flash, jsonify
from mysql import connector
from app import app

# Utilisez vos informations de connexion à MySQL ici
db_user = 'root'
db_password = '954Bibafou'
db_name = 'redditclone'

@app.route('/')
def main():
    return render_template('home.html', posts=loadposts())

@app.route('/home')
def home():
    return render_template('home.html', posts=loadposts())

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        # Exemple de la DB pour tester le login sur le site:
        # username: WebDeveloper_
        # password: ia
        username = request.form['username']
        password = request.form['password']

        # Conserver ce format dans les requêtes susceptibles aux injections SQL (avec placeholder %s)
        query = f"SELECT * FROM User WHERE username = %s"
        val = (f"{username}", )

        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()
        cursor.execute(query, val)
        result = cursor.fetchone()
    
        if result is not None and result[6] == password:
            session['user_id'] = result[0]
            session['user'] = result[1]
            return render_template('home.html', posts=loadposts())
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

@app.route('/profile')
def profile():
    profile = []
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()
    query = f"SELECT * FROM User WHERE user_id = {session['user_id']}"
    cursor.execute(query)
    result = cursor.fetchone()
    print(result)
    return render_template('profile.html', profile=profile)
    
#@app.route('/loadposts')
def loadposts(community_id=None):
    posts = []
    if 'user' in session:
        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()

        if community_id:
            # TODO
            pass
        else:
            query = f"CALL RandomPosts({session['user_id']})"

        # put n arg. Quand scroll, reload page with bigger n
        # Necessaire de changer fonction RandomPosts

        cursor.execute(query)
        results = cursor.fetchall()
        for r in results:
            posts.append({'author': 'AAAAAA', 'community_name': 'AAAAAAAAAAAA', 'upvotes': r[5],
                        'content': r[4], 'title': r[6], 'creation': r[3]})
        cursor.close()
        cnx.close()
    return posts
    

