# 🎫 Capta Tickets Dashboard

Dashboard interactivo para análisis y visualización de tickets de soporte. Implementa las 5 consultas principales de la prueba técnica con visualizaciones en tiempo real.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.31.0-red.svg)
![MongoDB](https://img.shields.io/badge/mongodb-7.0+-green.svg)

## ✨ Características

- **📊 Dashboard Interactivo**: Métricas en tiempo real, gráficos dinámicos con Plotly
- **🔍 5 Consultas Principales**: Lista de casos, reaperturas, ingresos, cierres, acciones
- **⚡ Filtros Avanzados**: Por fecha, estado y clasificador jerárquico
- **📈 Visualizaciones**: Pie charts, bar charts, line charts, métricas

## 🏗️ Arquitectura

```
Streamlit Frontend → MongoDB Atlas (Cloud)
  - Dashboard + Filtros         - capta_tickets
  - Gráficos + Tablas           - 100 tickets
```

## 🚀 Instalación

### Prerequisitos
- Python 3.8+
- MongoDB Atlas (cuenta gratuita)

### Setup Local

```bash
# Clonar repositorio
git clone https://github.com/Jessir1108/capta-dashboard.git
cd capta-dashboard

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar secrets
mkdir -p .streamlit
echo 'MONGO_URI = "mongodb+srv://user:pass@cluster.mongodb.net/"' > .streamlit/secrets.toml

# Ejecutar
streamlit run app.py
```

## ⚙️ Configuración

### Variables de Entorno

```bash
# Opción 1: Archivo .streamlit/secrets.toml
MONGO_URI = "mongodb+srv://user:password@cluster.mongodb.net/"

# Opción 2: Variable de entorno
export MONGO_URI="mongodb+srv://user:password@cluster.mongodb.net/"
```

## 💾 Modelo de Datos

### Colección: `tickets`

```javascript
{
  _id: "ticket_001",
  title: "Sin suministro de agua",
  currentState: "in_progress",
  currentClassifications: {
    tipo_solicitud: "altos_palmas_torre1"
  },
  createdAt: ISODate("2025-10-15T10:00:00Z"),
  closedAt: ISODate("2025-10-20T16:00:00Z"),
  reopenCount: 1,
  stateChangeCount: 4,
  history: [...]
}
```

### Índices Principales

- `idx_complex_filter`: Fecha + estado + clasificador
- `idx_history_action_timestamp`: Búsqueda en histórico
- `idx_createdAt`: Filtro por fecha de creación

## 🔍 Consultas Principales

| Consulta | Descripción | Complejidad |
|----------|-------------|-------------|
| 1. Lista de Casos | Tickets activos con filtros | O(log n) |
| 2. Reaperturas | Transiciones closed → activo | O(n) |
| 3. Ingresos | Tickets creados en período | O(log n) |
| 4. Cierres | Transiciones → closed | O(k × m) |
| 5. Acciones | Histórico de actividad | O(k × m) |

## 🚀 Deploy en Streamlit Cloud

1. **Push a GitHub**
```bash
git add .
git commit -m "Ready for deploy"
git push origin main
```

2. **Deploy en Streamlit Cloud**
   - Ve a https://share.streamlit.io
   - Click "New app"
   - Selecciona tu repositorio
   - Main file: `app.py`

3. **Configura Secrets**
```toml
MONGO_URI = "mongodb+srv://user:password@cluster.mongodb.net/"
```

4. **Deploy** 🚀

URL: `https://tu-usuario-capta-dashboard.streamlit.app`

## 🛠️ Tecnologías

- **Backend**: Python 3.8+, Streamlit 1.31.0, PyMongo 4.6.1
- **Visualización**: Plotly 5.18.0, Pandas 2.1.4
- **Base de Datos**: MongoDB 7.0+ (Atlas)
- **Deploy**: Streamlit Cloud

## 📊 Scripts Útiles

```bash
# Generar 100 tickets de prueba
python scripts/generate_data.py

# Actualizar campos desnormalizados
python scripts/update_tickets.py

# Crear índices en MongoDB
docker exec -it capta-mongodb mongosh -u admin -p pass --file scripts/indexes.js

# Ejecutar consultas de prueba
docker exec -it capta-mongodb mongosh -u admin -p pass --file scripts/queries.js
```

## 📖 Uso

1. Abre el **sidebar** izquierdo
2. Selecciona **filtros** (fecha, estado, clasificador)
3. Click en **"🔍 Aplicar Filtros"**
4. Explora las **visualizaciones y tablas**

## 👤 Autor

**Jessir Florez**
- LinkedIn: [Jessir Daniel Florez Hamburger](https://www.linkedin.com/in/jessflorez)

## ❓ FAQ

**¿Cómo cambio la conexión de MongoDB?**  
Edita `.streamlit/secrets.toml` o la variable `MONGO_URI`

**¿Los filtros no funcionan?**  
Haz click en "🔍 Aplicar Filtros" después de seleccionarlos

**¿Cómo agrego más datos?**  
Ejecuta `python scripts/generate_data.py`