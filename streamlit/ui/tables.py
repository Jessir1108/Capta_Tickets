import streamlit as st
import pandas as pd
from queries import TicketQueries
from config import TICKETS_LIMIT, ACCIONES_LIMIT
import plotly.express as px



def render_tickets_table(db, start_date, end_date, estado, clasificador):
    """Tabla de tickets con búsqueda"""
    st.subheader("🔍 Lista de Tickets")

    queries = TicketQueries(db)
    tickets = queries.get_tickets_list(
        start_date, end_date, estado, clasificador, TICKETS_LIMIT
    )

    if tickets:
        df = pd.DataFrame(
            [
                {
                    "ID": t["_id"][:8] + "...",
                    "Título": (
                        t["title"][:40] + "..." if len(t["title"]) > 40 else t["title"]
                    ),
                    "Estado": t["currentState"],
                    "Clasificador": t["currentClassifications"].get(
                        "tipo_solicitud", "N/A"
                    ),
                    "Creado": t["createdAt"].strftime("%d/%m/%Y %H:%M"),
                    "Reaperturas": t.get("reopenCount", 0),
                }
                for t in tickets
            ]
        )

        st.dataframe(df, use_container_width=True, height=400)
        st.caption(f"✅ {len(df)} tickets (máx: {TICKETS_LIMIT})")
    else:
        st.warning("⚠️ Sin tickets con los filtros aplicados")


def render_actions_table(db, start_date, end_date, clasificador):
    """Tabla de acciones recientes"""
    st.subheader("📜 Acciones Recientes")

    queries = TicketQueries(db)
    acciones = queries.get_recent_actions(
        start_date, end_date, clasificador, ACCIONES_LIMIT
    )

    if acciones:
        df = pd.DataFrame(
            [
                {
                    "Fecha": a["timestamp"].strftime("%d/%m/%Y %H:%M"),
                    "Ticket": a["ticketId"][:8] + "...",
                    "Acción": a["accion"],
                    "Usuario": a["usuario"],
                    "Cambio": (
                        f"{a.get('desde', '')} → {a.get('hacia', '')}"
                        if a["accion"] == "state_change"
                        else "-"
                    ),
                }
                for a in acciones
            ]
        )

        # Filtro de acciones
        tipo_acciones = sorted(df["Acción"].unique())
        filtro_acciones = st.multiselect(
            "Filtrar por tipo:",
            tipo_acciones,
            default=tipo_acciones,
            key="filtro_acciones",
        )

        df_filtrado = df[df["Acción"].isin(filtro_acciones)]

        st.dataframe(df_filtrado, use_container_width=True, height=400)
        st.caption(f"✅ {len(df_filtrado)} acciones de {len(acciones)} totales")

        # Distribución de acciones
        st.markdown("**Distribución de Acciones**")
        acciones_count = df["Acción"].value_counts()
        col_chart, col_stats = st.columns([2, 1])

        with col_chart:
            fig = px.bar(
                x=acciones_count.index,
                y=acciones_count.values,
                labels={"x": "Acción", "y": "Cantidad"},
                color=acciones_count.values,
                color_continuous_scale="Blues",
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col_stats:
            for accion, count in acciones_count.items():
                st.metric(accion, count, border=True)

    else:
        st.warning("⚠️ Sin acciones en el período")
