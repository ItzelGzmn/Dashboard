import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configurar página
st.set_page_config(page_title="Dashboard Financiero", layout="wide", initial_sidebar_state="expanded")

# Cargar datos
@st.cache_data
def load_data():
    # Asegúrate de que el archivo Excel esté en la misma carpeta
    file_path = 'dashboard_data_combined.xlsx'
    
    # Leer todas las hojas
    ingresos_costos = pd.read_excel(file_path, sheet_name='Ingresos_vs_Costos')
    resumen_cliente = pd.read_excel(file_path, sheet_name='Resumen_Cliente')
    resumen_proyecto = pd.read_excel(file_path, sheet_name='Resumen_Proyecto')
    resumen_periodo = pd.read_excel(file_path, sheet_name='Resumen_Periodo')
    resumen_broker = pd.read_excel(file_path, sheet_name='Resumen_Broker')
    detalle_pagos = pd.read_excel(file_path, sheet_name='Detalle_Pagos_Por_Factura')
    
    # Limpiar datos (eliminar filas vacías o de encabezado duplicado)
    ingresos_costos = ingresos_costos[ingresos_costos['FACTURA'] != 'FACTURA']
    resumen_cliente = resumen_cliente[resumen_cliente['CLIENTE'] != 'CLIENTE']
    resumen_proyecto = resumen_proyecto[resumen_proyecto['CLIENTE'] != 'CLIENTE']
    resumen_periodo = resumen_periodo[resumen_periodo['PERIODO'] != 'PERIODO']
    resumen_broker = resumen_broker[resumen_broker['BROKER'] != 'BROKER']
    detalle_pagos = detalle_pagos[detalle_pagos['FACTURA'] != 'FACTURA']
    
    # Convertir tipos numéricos
    numeric_cols = ['TOTAL_INGRESOS', 'TOTAL_COSTOS', 'UTILIDAD_BRUTA', 'MARGEN_BRUTO']
    for col in numeric_cols:
        if col in ingresos_costos.columns:
            ingresos_costos[col] = pd.to_numeric(ingresos_costos[col], errors='coerce')
    
    return ingresos_costos, resumen_cliente, resumen_proyecto, resumen_periodo, resumen_broker, detalle_pagos

# Cargar datos
ingresos_costos, resumen_cliente, resumen_proyecto, resumen_periodo, resumen_broker, detalle_pagos = load_data()

# Título principal
st.title("📊 Dashboard Financiero - Análisis de Ingresos y Costos")
st.markdown("---")

# KPIs generales en la barra lateral
st.sidebar.header("📈 KPIs Principales")
total_ingresos = resumen_cliente['TOTAL_INGRESOS'].sum()
total_costos = resumen_cliente['TOTAL_COSTOS'].sum()
total_utilidad = resumen_cliente['UTILIDAD_BRUTA'].sum()
margen_promedio = (total_utilidad / total_ingresos) * 100

st.sidebar.metric("Total Ingresos", f"${total_ingresos:,.2f}")
st.sidebar.metric("Total Costos", f"${total_costos:,.2f}")
st.sidebar.metric("Utilidad Bruta", f"${total_utilidad:,.2f}")
st.sidebar.metric("Margen Promedio", f"{margen_promedio:.2f}%")

# Filtros en la barra lateral
st.sidebar.markdown("---")
st.sidebar.header("🔎 Filtros")

# Filtro por cliente
clientes = ['Todos'] + sorted(resumen_cliente['CLIENTE'].unique())
cliente_seleccionado = st.sidebar.selectbox("Cliente", clientes)

# Filtro por período
periodos = ['Todos'] + sorted(resumen_periodo['PERIODO'].unique(), reverse=True)
periodo_seleccionado = st.sidebar.selectbox("Período", periodos)

# Filtrar datos según selección
if cliente_seleccionado != 'Todos':
    ingresos_costos = ingresos_costos[ingresos_costos['CLIENTE'] == cliente_seleccionado]
    resumen_proyecto = resumen_proyecto[resumen_proyecto['CLIENTE'] == cliente_seleccionado]

if periodo_seleccionado != 'Todos':
    ingresos_costos = ingresos_costos[ingresos_costos['PERIODO'] == periodo_seleccionado]

# Tabs principales
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Resumen", "🎯 Clientes", "🏗️ Proyectos", "📅 Períodos", "💼 Brokers"])

# Tab 1: Resumen General
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pastel: Distribución de ingresos por cliente
        top_clientes = resumen_cliente.nlargest(10, 'TOTAL_INGRESOS')
        fig_pie = px.pie(top_clientes, values='TOTAL_INGRESOS', names='CLIENTE', 
                         title='Top 10 Clientes por Ingresos')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Gráfico de barras: Margen por cliente
        fig_margen = px.bar(resumen_cliente.nlargest(15, 'MARGEN_PORCENTAJE'), 
                           x='MARGEN_PORCENTAJE', y='CLIENTE', orientation='h',
                           title='Top 15 Clientes por Margen (%)',
                           labels={'MARGEN_PORCENTAJE': 'Margen (%)'})
        st.plotly_chart(fig_margen, use_container_width=True)
    
    # Evolución temporal
    fig_evolucion = px.line(resumen_periodo, x='PERIODO', y=['TOTAL_INGRESOS', 'TOTAL_COSTOS'],
                           title='Evolución de Ingresos y Costos por Período')
    fig_evolucion.update_layout(xaxis_title="Período", yaxis_title="Monto ($)")
    st.plotly_chart(fig_evolucion, use_container_width=True)

# Tab 2: Análisis por Cliente
with tab2:
    st.header("Análisis Detallado por Cliente")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Tabla interactiva
        st.dataframe(resumen_cliente.sort_values('UTILIDAD_BRUTA', ascending=False), 
                     height=400, use_container_width=True)
    
    with col2:
        # Gráfico de barras de ingresos
        fig_ingresos = px.bar(resumen_cliente.nlargest(10, 'TOTAL_INGRESOS'), 
                             x='TOTAL_INGRESOS', y='CLIENTE', orientation='h',
                             title='Top 10 Ingresos por Cliente')
        st.plotly_chart(fig_ingresos, use_container_width=True)
    
    # Scatter plot: Ingresos vs Margen
    fig_scatter = px.scatter(resumen_cliente, x='TOTAL_INGRESOS', y='MARGEN_PORCENTAJE',
                            size='NUM_FACTURAS', color='CLIENTE',
                            title='Ingresos vs Margen por Cliente',
                            hover_name='CLIENTE')
    st.plotly_chart(fig_scatter, use_container_width=True)

# Tab 3: Análisis por Proyecto
with tab3:
    st.header("Análisis por Proyecto")
    
    # Top proyectos más rentables
    col1, col2 = st.columns(2)
    
    with col1:
        top_proyectos_utilidad = resumen_proyecto.nlargest(10, 'UTILIDAD_BRUTA')
        fig_proy_utilidad = px.bar(top_proyectos_utilidad, 
                                  x='UTILIDAD_BRUTA', y='PROYECTO', orientation='h',
                                  title='Top 10 Proyectos por Utilidad Bruta')
        st.plotly_chart(fig_proy_utilidad, use_container_width=True)
    
    with col2:
        top_proyectos_margen = resumen_proyecto.nlargest(10, 'MARGEN_PORCENTAJE')
        fig_proy_margen = px.bar(top_proyectos_margen, 
                                x='MARGEN_PORCENTAJE', y='PROYECTO', orientation='h',
                                title='Top 10 Proyectos por Margen (%)')
        st.plotly_chart(fig_proy_margen, use_container_width=True)
    
    # Tabla filtrable de proyectos
    st.subheader("Todos los Proyectos")
    st.dataframe(resumen_proyecto.sort_values('UTILIDAD_BRUTA', ascending=False), 
                 height=300, use_container_width=True)

# Tab 4: Análisis por Período
with tab4:
    st.header("Análisis Temporal")
    
    # Métricas por período
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_periodo_ingresos = px.bar(resumen_periodo, x='PERIODO', y='TOTAL_INGRESOS',
                                     title='Ingresos por Período')
        st.plotly_chart(fig_periodo_ingresos, use_container_width=True)
    
    with col2:
        fig_periodo_utilidad = px.bar(resumen_periodo, x='PERIODO', y='UTILIDAD_BRUTA',
                                     title='Utilidad Bruta por Período')
        st.plotly_chart(fig_periodo_utilidad, use_container_width=True)
    
    with col3:
        fig_periodo_margen = px.line(resumen_periodo, x='PERIODO', y='MARGEN_PORCENTAJE',
                                    title='Margen % por Período')
        st.plotly_chart(fig_periodo_margen, use_container_width=True)
    
    # Análisis de tendencia
    resumen_periodo['TENDENCIA'] = resumen_periodo['UTILIDAD_BRUTA'].pct_change() * 100
    fig_tendencia = px.area(resumen_periodo, x='PERIODO', y='TENDENCIA',
                           title='Tendencia de Crecimiento de Utilidad (%)')
    st.plotly_chart(fig_tendencia, use_container_width=True)

# Tab 5: Análisis por Broker
with tab5:
    st.header("Análisis de Pagos por Broker")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Top brokers por pago
        top_brokers = resumen_broker.nlargest(15, 'TOTAL_PAGADO')
        fig_broker = px.bar(top_brokers, x='TOTAL_PAGADO', y='BROKER', orientation='h',
                           title='Top 15 Brokers por Total Pagado')
        st.plotly_chart(fig_broker, use_container_width=True)
    
    with col2:
        # Distribución de brokers
        fig_broker_pie = px.pie(resumen_broker.nlargest(10, 'TOTAL_PAGADO'), 
                               values='TOTAL_PAGADO', names='BROKER',
                               title='Distribución Top 10 Brokers')
        st.plotly_chart(fig_broker_pie, use_container_width=True)
    
    # Tabla de brokers
    st.dataframe(resumen_broker.sort_values('TOTAL_PAGADO', ascending=False), 
                 height=400, use_container_width=True)

# Sección de detalle de facturas
st.markdown("---")
st.header("📄 Detalle de Facturas")
st.dataframe(ingresos_costos.sort_values('FECHA_FACTURA', ascending=False), 
             height=300, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Dashboard generado con Streamlit | Datos actualizados hasta el último período")