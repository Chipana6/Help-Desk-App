import pymysql
pymysql.install_as_MySQLdb()

from app import app, db
from app import models # Importante para que detecte los modelos

with app.app_context():
    db.create_all()
    print("¡Tablas de Soporte creadas exitosamente en MySQL!")