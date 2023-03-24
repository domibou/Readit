from flask import render_template, session, request, redirect, url_for, flash, jsonify
from mysql import connector
from app import app

# Utilisez vos informations de connexion à MySQL ici
db_user = 'root'
db_password = ''
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

        # Conserver ce format dans les requêtes où l'utilisateur envoie du texte (avec placeholder %s)
        # pour éviter les injections de code
        query = f"SELECT * FROM User WHERE username = %s"
        val = (f"{username}", )

        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()
        cursor.execute(query, val)
        result = cursor.fetchone()
    
        if result is not None and result[6] == password:
            session['user_id'] = result[0]
            session['user'] = result[1]
            cursor.close()
            cnx.close()
            return render_template('home.html', posts=loadposts())
        else:
            flash("Incorrect username or password")
            cursor.close()
            cnx.close()
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
    user_id = request.args.get('user_id')
    profile = []
    communities = []
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()

    # Informations sur le profil utilisateur
    query = f"SELECT * FROM User WHERE user_id = {user_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    profile.append({'user_id': result[0], 'username': result[1], 'creation_date': result[2], 
                    'rating': result[3], 'email': result[4], 'description': result[5]})

    # Communautés suivies par l'utilisateur
    query = f"SELECT * FROM Community WHERE community_id IN (SELECT community_id FROM Subscription WHERE user_id = {user_id})"
    cursor.execute(query)
    result = cursor.fetchall()
    for r in result:
        communities.append({'community_id': r[0], 'description': r[1], 'tag': r[2],
                      'name': r[3], 'creation_date': r[4]})

    # Nombre de posts faits par l'utilisateur
    query = f"SELECT COUNT(*) FROM MakesPost WHERE user_id = {user_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    posts = result[0]

    cursor.close()
    cnx.close()
    return render_template('profile.html', profile=profile, communities=communities, posts=posts)

@app.route('/post')
def post():
    post_id = request.args.get('post_id')

    return render_template('post.html')
    
@app.route('/community')
def community():
    community_id = request.args.get('community_id')
    community = []
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()

    # Informations sur la communauté
    query = f"SELECT * FROM Community WHERE community_id = {community_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    community.append({'community_id': result[0], 'description': result[1], 'tag': result[2],
                      'name': result[3], 'creation_date': result[4]})
    

    # Nombre d'abonnés
    query = f"SELECT COUNT(*) FROM Subscription WHERE community_id = {community[0]['community_id']}"
    cursor.execute(query)
    result = cursor.fetchone()
    followers = result[0]

    cursor.close()
    cnx.close()
    return render_template('community.html', community=community, 
                           followers=followers, posts=loadposts(community[0]['community_id']))

def loadposts(community_id=None):
    posts = []
    if 'user' in session:
        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()

        if community_id:
            # Pour les posts d'une communauté
            query = f"SELECT * FROM Post WHERE community_id = {community_id} LIMIT 20"
        else:
            # Pour des posts aléatoires des communautés suivies par l'utilisateur (pour la home page)
            query = f"CALL RandomPosts({session['user_id']})"

        # Informations sur les posts
        cursor.execute(query)
        result = cursor.fetchall()
        for r in result:
            posts.append({'post_id': r[0], 'user_id': r[1], 'community_id': r[2],
                          'creation_date': r[3], 'content': r[4], 'upvotes': r[5],
                          'title': r[6]})
            
        # Récupère les noms des auteurs et des communautés reliés aux posts. 
        # Vraiment pas efficace mais on a seulement les identifiants dans notre table Post 
        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()
        for p in posts:
            # Auteur
            query = f"SELECT username FROM User WHERE user_id = {p['user_id']}"
            cursor.execute(query)
            result = cursor.fetchone()
            p['username'] = result[0]

            # Communauté
            query = f"SELECT name FROM Community WHERE community_id = {p['community_id']}"
            cursor.execute(query)
            result = cursor.fetchone()
            p['name'] = result[0]

        cursor.close()
        cnx.close()
    return posts
    

