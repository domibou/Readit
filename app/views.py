from flask import render_template, session, request, redirect, url_for, flash
import hashlib
from mysql import connector
from app import app
from datetime import datetime

# Utilisez vos informations de connexion à MySQL ici
db_user = 'root'
db_password = 'po1iuytr'
db_name = 'redditclone'

@app.route('/')
def main():
    return render_template('home.html', posts=loadposts(), communities=loadUserCommunities())

@app.route('/home')
def home():
    return render_template('home.html', posts=loadposts(), communities=loadUserCommunities())

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        # Exemple de la DB pour tester le login sur le site:
        # username: WebDeveloper_
        # password: ia
        username = request.form['username']
        password = request.form['encryptedPassword']

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
            return render_template('home.html', posts=loadposts(), communities=loadUserCommunities())
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

@app.route('/signup', methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        email = request.form['email']
        username = request.form['username']
        password = request.form['encryptedPassword']

        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)

        current_time = datetime.today()
        formatted_date = current_time.strftime('%Y-%m-%d')

        cursor = cnx.cursor()
        query = f"INSERT INTO User(username, creation_date, email, password) VALUES ('{username}', '{formatted_date}', '{email}', '{password}')"
        cursor.execute(query)
        cursor.fetchall()
        cnx.commit()

        cursor.close()
        cnx.close()
        return render_template('login.html')
    else:

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

    # # Nombre de posts faits par l'utilisateur
    # query = f"SELECT COUNT(*) FROM MakesPost WHERE user_id = {user_id}"
    # cursor.execute(query)
    # result = cursor.fetchone()
    # posts = result[0]

    #posts de l'utilisateur
    posts =[]
    query = f"SELECT * FROM Post WHERE user_id = {user_id} "
    cursor.execute(query)
    result = cursor.fetchall()
    for r in result:
        posts.append({'post_id': r[0], 'user_id': r[1], 'community_id': r[2],
                     'creation_date': r[3], 'content': r[4], 'title': r[5]})

    # Récupère les noms des auteurs des comments.
    for p in posts:
        # Auteur
        query = f"SELECT name FROM Community WHERE community_id = {p['community_id']}"
        cursor.execute(query)
        result = cursor.fetchone()
        p['community'] = result[0]
    # #commentaires de l'utilisateur
    # comments =[]
    # query = f"SELECT * FROM Comment WHERE user_id = {user_id} "
    # cursor.execute(query)
    # result = cursor.fetchall()
    # for r in result:
    #     comments.append({'comment_id': r[0], 'post_id': r[1], 'user_id': r[2],
    #                      'content': r[3], 'creation_date': r[4]})

    postcount = len(posts)
    # commentcount = len(comments)

    cursor.close()
    cnx.close()
    return render_template('profile.html', profile=profile, communities=communities, posts=posts,postcount=postcount)

@app.route('/post' )
def post():
    post_id = request.args.get('post_id')
    post = []
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()

    # Informations sur le post
    query = f"SELECT * FROM Post WHERE post_id = {post_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    post.append({'post_id': result[0], 'user_id': result[1], 'community_id': result[2],
                      'creation_date': result[3], 'content': result[4], 'title': result[5]})

    fillpost(post[0],cursor)
    canupvote = False
    if 'user' in session:
        query = f"SELECT COUNT(*) FROM Upvote WHERE user_id = {session['user_id']} AND post_id = {post_id}"
        cursor.execute(query)
        result = cursor.fetchone()
        canupvote =result[0]==0;


    return render_template('post.html', post=post, comments=loadreplies(post[0]['post_id']),canupvote=canupvote)
    
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

def loadUserCommunities():
    communities = []

    if 'user' in session:
        user_id = session['user_id']
        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()
        query = f"SELECT * FROM Community WHERE community_id IN (SELECT community_id FROM Subscription WHERE user_id = {user_id})"
        cursor.execute(query)
        result = cursor.fetchall()
        for r in result:
            communities.append({'community_id': r[0], 'description': r[1], 'tag': r[2],
                                'name': r[3], 'creation_date': r[4]})
        cursor.close()
        cnx.close()
    return communities
@app.route('/upvote' )
def upvote():
    post_id = request.args.get('post_id')
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()

    #upvote
    if 'user' in session:
        query = f"INSERT INTO Upvote(post_id,user_id) VALUES ('{post_id}', '{session['user_id']}')"
        cursor.execute(query)
        cursor.fetchall()
        cnx.commit()

    return post()

def loadposts(community_id=None):
    posts = []
    query = ''
    if 'user' in session:
        if community_id:
            # Pour les posts d'une communauté
            query = f"SELECT * FROM Post WHERE community_id = {community_id} LIMIT 20"
        else:
            # Pour des posts aléatoires des communautés suivies par l'utilisateur (pour la home page)
            query = f"CALL RandomPosts({session['user_id']},5)"
    else:
        # Posts aléatoires dans le tableau au complet lorsqu'on n'est pas logged in
        query = f"CALL RandomPostsNotLoggedIn(10)"

    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()
    # Informations sur les posts
    cursor.execute(query)
    result = cursor.fetchall()
    for r in result:
        posts.append({'post_id': r[0], 'user_id': r[1], 'community_id': r[2],
                      'creation_date': r[3], 'content': r[4],
                      'title': r[5]})

    # Récupère les noms des auteurs et des communautés reliés aux posts.
    # Vraiment pas efficace mais on a seulement les identifiants dans notre table Post
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()
    for p in posts:
        fillpost(p,cursor)


    cursor.close()
    cnx.close()

    return posts
    

def loadreplies(post_id):#contains comment
    comments = []
    if 'user' in session:
        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()

        query = f"SELECT * FROM Comment WHERE post_id = {post_id} "
        # Informations sur les posts
        cursor.execute(query)
        result = cursor.fetchall()
        for r in result:
            comments.append({'comment_id': r[0], 'post_id': r[1], 'user_id': r[2],
                          'content': r[3], 'creation_date': r[4]})

        # Récupère les noms des auteurs des comments.
        for c in comments:
            # Auteur
            query = f"SELECT username FROM User WHERE user_id = {c['user_id']}"
            cursor.execute(query)
            result = cursor.fetchone()
            c['username'] = result[0]


        cursor.close()
        cnx.close()
    return comments

def fillpost(post, cursor):

    # Auteur
    query = f"SELECT username FROM User WHERE user_id = {post['user_id']}"
    cursor.execute(query)
    result = cursor.fetchone()
    post['username'] = result[0]

    # Nom communaute
    query = f"SELECT name FROM Community WHERE community_id = {post['community_id']}"
    cursor.execute(query)
    result = cursor.fetchone()
    post['community'] = result[0]

    # Nombre d'upvotes
    query = f"SELECT COUNT(*) FROM Upvote WHERE post_id  = {post['post_id']}"
    cursor.execute(query)
    result = cursor.fetchone()
    post['upvotes'] = result[0]

    # Nombre de replies
    query = f"SELECT COUNT(*) FROM Comment WHERE post_id  = {post['post_id']}"
    cursor.execute(query)
    result = cursor.fetchone()
    post['replies'] = result[0]