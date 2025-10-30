import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from queries import TicketQueries
from config import COLORS, CLASIFICADORES_LIMIT


def render_states_distribution(metrics, estado_filtro):
    """Gráfico de distribución de estados"""
    st.subheader("📈 Distribución de Estados")

    if estado_filtro == "Todos":
        total = metrics["total"]
        pct_abiertos = (metrics["abiertos"] / total * 100) if total > 0 else 0
        pct_progreso = (metrics["en_progreso"] / total * 100) if total > 0 else 0
        pct_cerrados = (metrics["cerrados"] / total * 100) if total > 0 else 0

        estados_data = {
            "Estado": [
                f"Abiertos ({pct_abiertos:.1f}%)",
                f"En Progreso ({pct_progreso:.1f}%)",
                f"Cerrados ({pct_cerrados:.1f}%)",
            ],
            "Cantidad": [
                metrics["abiertos"],
                metrics["en_progreso"],
                metrics["cerrados"],
            ],
        }

        fig = px.pie(
            estados_data,
            values="Cantidad",
            names="Estado",
            hole=0.4,
            color_discrete_map={
                f"Abiertos ({pct_abiertos:.1f}%)": COLORS["abiertos"],
                f"En Progreso ({pct_progreso:.1f}%)": COLORS["en_progreso"],
                f"Cerrados ({pct_cerrados:.1f}%)": COLORS["cerrados"],
            },
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(height=400, hovermode="closest")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"📌 Mostrando solo tickets: **{estado_filtro}**")
        st.metric("Total", metrics["total"])


def render_classifiers_chart(db, start_date, end_date, estado, clasificador):
    """Gráfico de tickets por clasificador"""
    st.subheader("📊 Top 10 Clasificadores")

    queries = TicketQueries(db)
    data = queries.get_tickets_by_classifier(start_date, end_date, estado, clasificador)

    if data:
        df = pd.DataFrame(data)
        df.columns = ["Clasificador", "Cantidad"]

        fig = px.bar(
            df,
            x="Cantidad",
            y="Clasificador",
            orientation="h",
            color="Cantidad",
            color_continuous_scale="Viridis",
        )

        fig.update_layout(
            height=400,
            showlegend=False,
            hovermode="y unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 Sin datos disponibles")


def render_trend_chart(db, start_date, end_date, estado, clasificador):
    """Gráfico de tendencia temporal"""
    st.subheader("📅 Tendencia de Creación")

    queries = TicketQueries(db)
    data = queries.get_tickets_trend(start_date, end_date, estado, clasificador)

    if data:
        df = pd.DataFrame(data)
        df["fecha"] = pd.to_datetime(
            df["_id"].apply(lambda x: f"{x['year']}-{x['month']}-{x['day']}")
        )
        df = df.sort_values("fecha")

        fig = px.line(
            df,
            x="fecha",
            y="count",
            markers=True,
            title="",
            labels={"count": "Tickets", "fecha": "Fecha"},
        )

        fig.update_traces(
            line_color=COLORS["cerrados"],
            line_width=3,
            marker_size=8,
            hovertemplate="<b>%{x|%d/%m}</b><br>Tickets: %{y}<extra></extra>",
        )
        fig.update_layout(height=400, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📭 Sin datos de tendencia")


def render_reopenings_analysis(db, estado, clasificador):
    """Gráfico de análisis de reaperturas"""
    st.subheader("🔄 Análisis de Reaperturas")

    queries = TicketQueries(db)
    stats = queries.get_reopenings_stats(estado, clasificador)

    col1, col2 = st.columns([2, 1])

    with col1:
        data = {
            "Categoría": ["Con Reaperturas", "Sin Reaperturas"],
            "Cantidad": [stats["con_reaperturas"], stats["sin_reaperturas"]],
        }

        fig = px.bar(
            data,
            x="Categoría",
            y="Cantidad",
            color="Categoría",
            color_discrete_map={
                "Con Reaperturas": COLORS["con_reaperturas"],
                "Sin Reaperturas": COLORS["sin_reaperturas"],
            },
        )

        fig.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        tasa = (
            (stats["con_reaperturas"] / stats["total"] * 100)
            if stats["total"] > 0
            else 0
        )
        st.metric("Tasa %", f"{tasa:.1f}%", border=True)


def render_resolution_time(db, start_date, end_date, estado, clasificador):
    """Gráfico de tiempo de resolución"""
    st.subheader("⏱️ Tiempo de Resolución")

    queries = TicketQueries(db)
    stats = queries.get_resolution_time(start_date, end_date, estado, clasificador)

    col1, col2, col3 = st.columns(3)

    if stats:
        with col1:
            st.metric("Promedio", f"{stats['promedio']:.1f} días", border=True)
        with col2:
            st.metric("Mínimo", f"{stats['minimo']:.1f} días", border=True)
        with col3:
            st.metric("Máximo", f"{stats['maximo']:.1f} días", border=True)
    else:
        st.info("📭 Sin datos de resolución")
