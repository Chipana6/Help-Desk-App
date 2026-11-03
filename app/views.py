from flask_appbuilder import ModelView, BaseView, expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import has_access
from flask_appbuilder.actions import action
from flask import render_template, flash, redirect
from sqlalchemy import text

from .models import Categoria, Prioridad, Ticket, Comentario, HistorialEstado, Etiqueta
from . import appbuilder, db

# --- VISTAS CRUD ---

class CategoriaView(ModelView):
    datamodel = SQLAInterface(Categoria)
    list_columns = ['nombre', 'descripcion']
    add_columns = ['nombre', 'descripcion']
    edit_columns = ['nombre', 'descripcion']

class PrioridadView(ModelView):
    datamodel = SQLAInterface(Prioridad)
    list_columns = ['nombre', 'nivel']
    add_columns = ['nombre', 'nivel']
    edit_columns = ['nombre', 'nivel']

class TicketView(ModelView):
    datamodel = SQLAInterface(Ticket)
    list_columns = ['asunto', 'estado', 'categoria', 'prioridad', 'cliente', 'fecha_creacion']
    add_columns = ['asunto', 'descripcion', 'categoria', 'prioridad', 'cliente', 'tecnico']
    edit_columns = ['asunto', 'descripcion', 'estado', 'categoria', 'prioridad', 'tecnico']

    @action("sugerir_prioridad", "Sugerir con IA", "¿Clasificar con IA?", "fa-magic")
    def sugerir_prioridad(self, items):
        from .models import Categoria, Prioridad
        from flask import flash
        
        for item in items:
            # 1. Llamamos a la IA
            resultado = item.clasificar_con_ia()
            
            # 2. Analizamos qué respondió la IA (buscando las palabras clave)
            cat_texto = "Hardware" # Por defecto
            prio_texto = "Alta"    # Por defecto
            
            if "Software" in resultado: cat_texto = "Software"
            if "Red" in resultado: cat_texto = "Red"
            
            if "Media" in resultado: prio_texto = "Media"
            if "Baja" in resultado: prio_texto = "Baja"
            
            # 3. Buscamos esas categorías en la base de datos
            cat_db = db.session.query(Categoria).filter_by(nombre=cat_texto).first()
            prio_db = db.session.query(Prioridad).filter_by(nombre=prio_texto).first()
            
            # 4. Actualizamos el ticket si las encontramos
            if cat_db and prio_db:
                item.categoria_id = cat_db.id
                item.prioridad_id = prio_db.id
                db.session.commit()
                flash(f"Ticket #{item.id} clasificado por IA: {cat_texto} - {prio_texto}", "info")
            else:
                flash(f"IA sugirió {cat_texto} y {prio_texto}, pero no están en la BD.", "warning")
                
        # Redirigimos a la lista normal
        return redirect(self.get_redirect())

class ComentarioView(ModelView):
    datamodel = SQLAInterface(Comentario)
    list_columns = ['ticket', 'autor', 'texto', 'fecha_creacion']
    add_columns = ['ticket', 'autor', 'texto']

class HistorialEstadoView(ModelView):
    datamodel = SQLAInterface(HistorialEstado)
    list_columns = ['ticket', 'estado_anterior', 'estado_nuevo', 'fecha_cambio']

class EtiquetaView(ModelView):
    datamodel = SQLAInterface(Etiqueta)
    list_columns = ['nombre']

# Registramos las vistas CRUD en el menú
appbuilder.add_view(CategoriaView, "Categorías", icon="fa-folder-open", category="Soporte")
appbuilder.add_view(PrioridadView, "Prioridades", icon="fa-exclamation-circle", category="Soporte")
appbuilder.add_view(TicketView, "Tickets", icon="fa-ticket", category="Soporte")
appbuilder.add_view(ComentarioView, "Comentarios", icon="fa-comments", category="Soporte")
appbuilder.add_view(HistorialEstadoView, "Historial de Estados", icon="fa-history", category="Soporte")
appbuilder.add_view(EtiquetaView, "Etiquetas", icon="fa-tags", category="Soporte")


# --- VISTA DE REPORTES ---

class ReportesView(BaseView):
    route_base = "/reportes"
    
    @expose("/")
    @has_access
    def index(self):
        # 1. Reporte: Tickets por Categoría
        sql_categorias = text("""
            SELECT c.nombre as categoria, COUNT(t.id) as cantidad 
            FROM categoria c 
            LEFT JOIN ticket t ON c.id = t.categoria_id 
            GROUP BY c.nombre
        """)
        res_categorias = db.session.execute(sql_categorias).fetchall()
        
        # 2. Reporte: Tickets por Prioridad
        sql_prioridades = text("""
            SELECT p.nombre as prioridad, COUNT(t.id) as cantidad 
            FROM prioridad p 
            LEFT JOIN ticket t ON p.id = t.prioridad_id 
            GROUP BY p.nombre
        """)
        res_prioridades = db.session.execute(sql_prioridades).fetchall()
        
        # 3. Reporte: Tickets sin asignar (Pendientes)
        sql_pendientes = text("""
            SELECT t.id, t.asunto, t.fecha_creacion 
            FROM ticket t 
            WHERE t.tecnico_id IS NULL
        """)
        res_pendientes = db.session.execute(sql_pendientes).fetchall()
        
        # Usamos render_template para cargar el archivo HTML
        return render_template(
            "reportes.html",
            categorias=res_categorias,
            prioridades=res_prioridades,
            pendientes=res_pendientes
        )

# Registramos el enlace en el menú y forzamos la ruta
appbuilder.add_link("Reportes", href="/reportes/", icon="fa-chart-bar", category="Soporte")
appbuilder.add_view_no_menu(ReportesView)
from flask import request, jsonify

class ChatIAView(BaseView):
    route_base = "/chat"

    @expose("/")
    @has_access
    def index(self):
        return render_template("chat.html")

    @expose("/preguntar", methods=["POST"])
    @has_access
    def preguntar(self):
        from groq import Groq
        from flask import current_app
        
        data = request.get_json()
        pregunta = data.get("pregunta", "")
        
        try:
            
            client = Groq(api_key="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") 
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres un asistente técnico experto. Responde de forma breve y útil."},
                    {"role": "user", "content": pregunta}
                ],
                model="openai/gpt-oss-20b",
            )
            respuesta = chat_completion.choices[0].message.content
            return jsonify({"respuesta": respuesta})
        except Exception as e:
            return jsonify({"respuesta": f"Error: {str(e)}"})

# Registrar el chat en el menú
appbuilder.add_link("Chat con IA", href="/chat/", icon="fa-comments", category="Soporte")
appbuilder.add_view_no_menu(ChatIAView)