from datetime import datetime, timedelta
import streamlit as st
import os


def get_mongo_uri():
    """
    Obtiene el MONGO_URI de forma segura:
    1. Primero intenta leer de Streamlit Secrets (producción)
    2. Luego intenta leer de variables de entorno
    3. Finalmente usa localhost (desarrollo local)
    """
    if hasattr(st, "secrets") and "MONGO_URI" in st.secrets:
        return st.secrets["MONGO_URI"]
    elif "MONGO_URI" in os.environ:
        return os.environ["MONGO_URI"]
    else:
        return "mongodb://admin:captaPassword123@localhost:27017/"


MONGO_URI = get_mongo_uri()
DB_NAME = "capta_tickets"

PAGE_CONFIG = {
    "page_title": "Capta Tickets Dashboard",
    "page_icon": "🎫",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

ESTADOS = ["Todos", "open", "in_progress", "closed", "pending", "cancelled"]

COLORS = {
    "abiertos": "#FF6B6B",
    "en_progreso": "#FFA500",
    "cerrados": "#4ECDC4",
    "con_reaperturas": "#FF6B6B",
    "sin_reaperturas": "#4ECDC4",
}

DEFAULT_FILTERS = {
    "fecha_inicio": datetime.now() - timedelta(days=60),
    "fecha_fin": datetime.now(),
    "estado": "Todos",
    "clasificador": "Todos",
    "include_reopened": True,
}

TICKETS_LIMIT = 50
ACCIONES_LIMIT = 100
CLASIFICADORES_LIMIT = 10
