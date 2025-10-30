import streamlit as st
from config import PAGE_CONFIG
from database import get_db
from filters import FilterManager
from queries import TicketQueries
from ui.metrics import render_metrics
from ui.charts import (
    render_states_distribution,
    render_classifiers_chart,
    render_trend_chart,
    render_reopenings_analysis,
    render_resolution_time,
)
from ui.tables import render_tickets_table, render_actions_table

# Configuración de página
st.set_page_config(**PAGE_CONFIG)

# Conexión a BD
db = get_db()

# Inicialización de filtros
filter_manager = FilterManager(db)
filter_manager.initialize_session_state()
filter_manager.render_filters_sidebar()

# Header
st.title("🎫 Capta Tickets - Dashboard")
st.markdown("---")

# Obtener filtros actuales
filtros = filter_manager.get_current_filters()
start_date = filtros["fecha_inicio"]
end_date = filtros["fecha_fin"]
estado = filtros["estado"]
clasificador = filtros["clasificador"]

# Mostrar período
col_info, _ = st.columns([3, 1])
with col_info:
    st.caption(
        f"📊 Dashboard de {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
    )

# SECCIÓN 1: Métricas
st.markdown("### 📊 Métricas Principales")
metrics = render_metrics(db, start_date, end_date, estado, clasificador)
st.markdown("---")

# SECCIÓN 2: Gráficos principales
st.markdown("### 📈 Análisis Visual")
col1, col2 = st.columns(2)

with col1:
    render_states_distribution(metrics, estado)

with col2:
    render_classifiers_chart(db, start_date, end_date, estado, clasificador)

st.markdown("---")

# SECCIÓN 3: Tendencias
render_trend_chart(db, start_date, end_date, estado, clasificador)
st.markdown("---")

# SECCIÓN 4: Análisis de reaperturas
col3, col4 = st.columns(2)

with col3:
    render_reopenings_analysis(db, estado, clasificador)

with col4:
    render_resolution_time(db, start_date, end_date, estado, clasificador)

st.markdown("---")

# SECCIÓN 5: Consultas adicionales
st.markdown("### 📊 Consultas Principales")

col_a, col_b, col_c = st.columns(3)

with col_a:
    queries = TicketQueries(db)
    total_ingresos = queries.db.tickets.count_documents(
        {
            "createdAt": {"$gte": start_date, "$lte": end_date},
            **({"currentState": estado} if estado != "Todos" else {}),
        }
    )
    st.metric("📥 Ingresos", total_ingresos, delta="en período")

with col_b:
    queries = TicketQueries(db)
    cierres = queries.get_closures_in_period(start_date, end_date, clasificador)
    st.metric("🔒 Cierres", cierres, delta="transiciones")

with col_c:
    queries = TicketQueries(db)
    reaperturas_periodo = queries.get_reopenings_in_period(
        start_date, end_date, clasificador
    )
    st.metric("🔄 Reaperturas", reaperturas_periodo, delta="en período")

st.markdown("---")

# SECCIÓN 6: Tablas
st.markdown("### 📋 Datos Detallados")

tab1, tab2 = st.tabs(["🔍 Lista de Tickets", "📜 Acciones Recientes"])

with tab1:
    render_tickets_table(db, start_date, end_date, estado, clasificador)

with tab2:
    render_actions_table(db, start_date, end_date, clasificador)

st.markdown("---")

# Footer
st.markdown("### 💡 Información")
st.info(
    """
✅ **5 Consultas Implementadas:**
1. Lista de Casos (Tickets filtrados)
2. Cantidad de Reaperturas (Estadísticas)
3. Cantidad de Ingresos (Tickets creados)
4. Cantidad de Cierres (Transiciones)
5. Lista de Acciones (Histórico)

🛠 **Tecnologías:** Streamlit + MongoDB + Plotly + Pandas
"""
)
