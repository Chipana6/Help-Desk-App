import pymysql
pymysql.install_as_MySQLdb()

import logging
from flask import Flask
from flask_appbuilder import AppBuilder, SQLA

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")

db = SQLA(app)
appbuilder = AppBuilder(app, db.session)

# Solo importamos los archivos. Las vistas se registran dentro de views.py
from . import models
from . import views