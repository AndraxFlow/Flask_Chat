import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'ASDFGHJKL'
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:2661@localhost/chat_app"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
