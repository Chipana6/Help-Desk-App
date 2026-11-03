from app import app
from app.models import Ticket

with app.app_context():
    t = Ticket(descripcion="Mi laptop no enciende, la pantalla se queda negra y hace un pitido.")
    print("Consultando a la IA...")
    print(t.clasificar_con_ia())