from flask import Flask

app = Flask(__name__)
app.secret_key = 'secret'

# Other initialization code, such as configuring the database, can go here

from app import views