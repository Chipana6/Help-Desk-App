from flask_appbuilder import Model
from flask_appbuilder.security.sqla.models import User
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Categoria(Model):
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(200))
    def __repr__(self): return self.nombre

class Prioridad(Model):
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    nivel = Column(Integer, nullable=False)
    def __repr__(self): return self.nombre

class Ticket(Model):
    id = Column(Integer, primary_key=True)
    asunto = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    estado = Column(String(50), default='Abierto')
    
    categoria_id = Column(Integer, ForeignKey('categoria.id'), nullable=False)
    prioridad_id = Column(Integer, ForeignKey('prioridad.id'), nullable=False)
    cliente_id = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    tecnico_id = Column(Integer, ForeignKey('ab_user.id'), nullable=True)
    
    categoria = relationship("Categoria")
    prioridad = relationship("Prioridad")
    cliente = relationship(User, foreign_keys=[cliente_id], lazy='select')
    tecnico = relationship(User, foreign_keys=[tecnico_id], lazy='select')
    
    def clasificar_con_ia(self):
        from groq import Groq
        
        
        client = Groq(api_key="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")
        
        prompt = f"""
        Eres un asistente de soporte técnico. Analiza la siguiente descripción de un ticket:
        "{self.descripcion}"
        
        Devuelve SOLO un texto con este formato exacto (sin explicaciones extra):
        Categoria: [Elige entre Hardware, Software o Red]
        Prioridad: [Elige entre Alta, Media o Baja]
        """
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="openai/gpt-oss-20b",
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            return f"Error al contactar a la IA: {e}"

    def __repr__(self): return self.asunto

class Comentario(Model):
    id = Column(Integer, primary_key=True)
    texto = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    ticket_id = Column(Integer, ForeignKey('ticket.id'), nullable=False)
    autor_id = Column(Integer, ForeignKey('ab_user.id'), nullable=False)
    ticket = relationship("Ticket")
    autor = relationship(User, lazy='select')
    def __repr__(self): return f"Comentario de {self.autor}"

class HistorialEstado(Model):
    id = Column(Integer, primary_key=True)
    estado_anterior = Column(String(50))
    estado_nuevo = Column(String(50), nullable=False)
    fecha_cambio = Column(DateTime, default=datetime.utcnow)
    ticket_id = Column(Integer, ForeignKey('ticket.id'), nullable=False)
    ticket = relationship("Ticket")
    def __repr__(self): return f"{self.estado_anterior} -> {self.estado_nuevo}"

class Etiqueta(Model):
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    def __repr__(self): return self.nombre