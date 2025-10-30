import streamlit as st
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME


@st.cache_resource
def get_mongo_connection():
    """Obtiene conexión cached a MongoDB"""
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


def get_db():
    """Obtiene la base de datos"""
    return get_mongo_connection()
