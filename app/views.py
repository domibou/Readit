from flask import render_template, session, request, redirect, url_for, flash
import hashlib
from mysql import connector
from app import app
from datetime import datetime

#TODO ameliorer Search bar communities
#TODO Changer description
#TODO Placeholders dans toutes les requetes (securite)

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
    query = f"SELECT * FROM Post WHERE user_id = {user_id} ORDER BY creation_date DESC"
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


    postcount = len(posts)

    cursor.close()
    cnx.close()
    return render_template('profile.html', profile=profile, communities=communities, posts=posts,postcount=postcount)

@app.route('/post')
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
    insession = False; # il veut pas si jle fais dans le html-_-
    if 'user' in session:
        insession=True;
        query = f"SELECT COUNT(*) FROM Upvote WHERE user_id = {session['user_id']} AND post_id = {post_id}"
        cursor.execute(query)
        result = cursor.fetchone()
        canupvote = result[0]==0;

    return render_template('post.html', post=post, comments=loadreplies(post[0]['post_id']), canupvote=canupvote,insession=insession)

# form pour créer le post   
@app.route('/postcreation')
def postcreation():
    # community_id nécessaire pour plus tard, lorsque postcreation.html appellera /createpost
    # name est nécessaire pour postcreation.html directement
    community_id = request.args.get('community_id')
    name = request.args.get('name')
    return render_template('postcreation.html', community_id=community_id, name=name)

@app.route('/updateprofile', methods=["POST", "GET"])
def updateprofile():
    if request.method == "POST":
        user_id = request.args.get('user_id')
        text = request.form['text']
        print(text)
        cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
        cursor = cnx.cursor()
        query = f"UPDATE User SET description = '{text}' WHERE user_id = {user_id}"
        cursor.execute(query)
        cursor.close()
        cnx.commit()
        cnx.close()
    return profile()

# création du post à partir de la form
@app.route('/createpost', methods=["POST", "GET"])
def createpost():
    community_id = request.args.get('community_id')
    title = request.form['title']
    text = request.form['text']
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()
    query = f"INSERT INTO Post(user_id, community_id, creation_date, content, title) VALUES ({session['user_id']}, {community_id}, CURRENT_DATE(), '{text}', '{title}')"
    cursor.execute(query)
    cursor.close()
    cnx.commit()
    cnx.close()
    return redirect(url_for('community', community_id=community_id))

@app.route('/commentcreation')
def commentcreation():
    # community_id nécessaire pour plus tard, lorsque postcreation.html appellera /createpost
    post_id = request.args.get('post_id')
    title = request.args.get('title')
    return render_template('commentcreation.html', post_id=post_id, title=title)

@app.route('/createcomment', methods=["POST", "GET"])
def createcomment():
    post_id = request.args.get('post_id')
    text = request.form['text']
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()
    query = f"INSERT INTO Comment(post_id , user_id , content, creation_date ) VALUES ({post_id}, {session['user_id']}, '{text}', CURRENT_DATE())"
    cursor.execute(query)
    cursor.close()
    cnx.commit()
    cnx.close()
    return redirect(url_for('post', post_id=post_id))

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

    canfollow = False
    insession = False
    if 'user' in session:
        insession=True
        query = f"SELECT COUNT(*) FROM Subscription  WHERE user_id = {session['user_id']} AND community_id = {community_id}"
        cursor.execute(query)
        result = cursor.fetchone()
        canfollow = result[0]==0;

    cursor.close()
    cnx.close()
    return render_template('community.html', community=community, 
                           followers=followers, posts=loadposts(community[0]['community_id']),canfollow=canfollow,insession=insession)


@app.route('/communitysearch')
def communitysearch():
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()
    communities = [];

    query = f"SELECT * FROM Community"
    cursor.execute(query)
    result = cursor.fetchall()
    for r in result:
        communities.append({'community_id': r[0], 'description': r[1], 'tag': r[2],
                      'name': r[3], 'creation_date': r[4]})

    cursor.close()
    cnx.close()
    return render_template('communitysearch.html',communities=communities)
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
@app.route('/follow' )
def follow():
    community_id = request.args.get('community_id')
    cnx = connector.connect(user=db_user, password=db_password, host='localhost', database=db_name)
    cursor = cnx.cursor()

    #follow
    if 'user' in session:
        query = f"INSERT INTO Subscription (user_id,community_id,since) VALUES ('{session['user_id']}', '{community_id}',CURRENT_DATE())"
        cursor.execute(query)
        cursor.fetchall()
        cnx.commit()

    return community()
def loadposts(community_id=None):
    n_posts = 20
    posts = []
    query = ''

    if community_id:
        # Pour les posts d'une communauté
        query = f"SELECT * FROM Post WHERE community_id = {community_id} ORDER BY creation_date DESC LIMIT {n_posts};"
    else:
        if 'user' in session:
            # Pour des posts aléatoires des communautés suivies par l'utilisateur (pour la home page)
            query = f"CALL RandomPosts({session['user_id']}, {n_posts})"
        else:
            # Posts aléatoires dans le tableau au complet lorsqu'on n'est pas logged in
            query = f"CALL RandomPostsNotLoggedIn({n_posts})"

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
    # Vraiment pas efficace mais on a seulement les identifiants dans notre relation Post
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

        # Récupère les noms des auteurs des comments
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