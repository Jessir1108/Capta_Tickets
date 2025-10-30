import streamlit as st
from queries import TicketQueries


def render_metrics(db, start_date, end_date, estado, clasificador):
    """Renderiza métricas principales"""
    queries = TicketQueries(db)
    metrics = queries.get_metrics(start_date, end_date, estado, clasificador)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            label="📊 Total",
            value=metrics["total"],
            delta="tickets",
            border=True,
        )

    with col2:
        pct_abiertos = (
            f"{(metrics['abiertos']/metrics['total']*100):.1f}%"
            if metrics["total"] > 0
            else "0%"
        )
        st.metric(
            label="🟢 Abiertos",
            value=metrics["abiertos"],
            delta=pct_abiertos,
            border=True,
        )

    with col3:
        pct_progreso = (
            f"{(metrics['en_progreso']/metrics['total']*100):.1f}%"
            if metrics["total"] > 0
            else "0%"
        )
        st.metric(
            label="🟡 En Progreso",
            value=metrics["en_progreso"],
            delta=pct_progreso,
            border=True,
        )

    with col4:
        pct_cerrados = (
            f"{(metrics['cerrados']/metrics['total']*100):.1f}%"
            if metrics["total"] > 0
            else "0%"
        )
        st.metric(
            label="🔴 Cerrados",
            value=metrics["cerrados"],
            delta=pct_cerrados,
            border=True,
        )

    with col5:
        st.metric(
            label="🔄 Reaperturas",
            value=metrics["reaperturas"],
            delta="total",
            border=True,
        )

    return metrics
