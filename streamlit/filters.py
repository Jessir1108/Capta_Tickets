import streamlit as st
from datetime import datetime, timedelta
from config import DEFAULT_FILTERS, ESTADOS
from queries import TicketQueries


class FilterManager:
    """Gestor de filtros del dashboard"""

    def __init__(self, db):
        self.db = db
        self.queries = TicketQueries(db)

    def initialize_session_state(self):
        """Inicializa estado de sesión"""
        if "filtros_aplicados" not in st.session_state:
            st.session_state.filtros_aplicados = DEFAULT_FILTERS.copy()

    def render_filters_sidebar(self):
        """Renderiza panel de filtros en sidebar"""
        with st.sidebar:
            st.header("⚙️ Filtros Avanzados")

            # Rango de fechas
            col_fecha1, col_fecha2 = st.columns(2)
            with col_fecha1:
                fecha_inicio = st.date_input(
                    "📅 Desde",
                    value=st.session_state.filtros_aplicados["fecha_inicio"].date(),
                    max_value=datetime.now(),
                    key="fecha_inicio",
                )

            with col_fecha2:
                fecha_fin = st.date_input(
                    "📅 Hasta",
                    value=st.session_state.filtros_aplicados["fecha_fin"].date(),
                    max_value=datetime.now(),
                    key="fecha_fin",
                )

            # Estado
            estado = st.selectbox(
                "🔴 Estado",
                ESTADOS,
                index=ESTADOS.index(st.session_state.filtros_aplicados["estado"]),
                key="estado_select",
            )

            # Clasificador
            clasificadores = self.queries.get_all_classifiers()
            clasificador_actual = st.session_state.filtros_aplicados["clasificador"]
            clasificador_index = (
                clasificadores.index(clasificador_actual)
                if clasificador_actual in clasificadores
                else 0
            )

            clasificador = st.selectbox(
                "📂 Clasificador",
                clasificadores,
                index=clasificador_index,
                key="clasificador_select",
            )

            st.markdown("---")

            # Botones de acción
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "🔍 Aplicar Filtros", type="primary", use_container_width=True
                ):
                    st.session_state.filtros_aplicados = {
                        "fecha_inicio": datetime.combine(
                            fecha_inicio, datetime.min.time()
                        ),
                        "fecha_fin": datetime.combine(fecha_fin, datetime.max.time()),
                        "estado": estado,
                        "clasificador": clasificador,
                    }
                    st.rerun()

            with col2:
                if st.button("🔄 Resetear", use_container_width=True):
                    st.session_state.filtros_aplicados = DEFAULT_FILTERS.copy()
                    st.rerun()

            st.markdown("---")
            st.markdown("### 📊 Filtros Activos")
            self._display_active_filters()

    def _display_active_filters(self):
        """Muestra filtros activos"""
        filtros = st.session_state.filtros_aplicados
        st.info(
            f"""
        **📅 Período:** {filtros['fecha_inicio'].strftime('%d/%m/%Y')} 
        → {filtros['fecha_fin'].strftime('%d/%m/%Y')}
        
        **🔴 Estado:** {filtros['estado']}
        
        **📂 Clasificador:** {filtros['clasificador']}
        """
        )

    def get_current_filters(self) -> dict:
        """Obtiene filtros actuales"""
        return st.session_state.filtros_aplicados
