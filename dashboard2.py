import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

# Configurar página
st.set_page_config(page_title="Dashboard Facturas", layout="wide", initial_sidebar_state="expanded")

# Cargar datos desde el archivo proporcionado
@st.cache_data
def load_data():
    # Leer el archivo Excel
    file_path = 'Copia de Facturas generales_compartir.xlsx'
    
    # Leer la hoja 'Facturas Generales'
    df = pd.read_excel(file_path, sheet_name='Facturas Generales')
    
    # Limpiar nombres de columnas
    df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
    
    # Renombrar columnas para mayor claridad
    column_mapping = {
        'Fecha': 'FECHA',
        'Factura': 'FACTURA',
        'Truck': 'CAMION_ID',
        'Broker': 'BROKER',
        'Camion': 'CAMION_NUM',
        'Ticket': 'TICKET',
        'Clientes': 'CLIENTE',
        'Proyecto': 'PROYECTO',
        'Proyecto OK': 'PROYECTO_OK',
        'Horas o Viaje': 'HORAS_VIAJE',
        'Costo unitario': 'COSTO_UNITARIO',
        'Total Cobrado': 'TOTAL_COBRADO',
        'Pago a Broker': 'PAGO_BROKER',
        'Unamed': 'ACUMULADO'  # Parece ser un acumulado
    }
    
    # Aplicar renombrado
    df = df.rename(columns=column_mapping)
    
    # Convertir tipos de datos
    df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
    
    # Convertir columnas numéricas
    numeric_cols = ['FACTURA', 'HORAS_VIAJE', 'COSTO_UNITARIO', 'TOTAL_COBRADO', 'PAGO_BROKER', 'ACUMULADO']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Crear columna de periodo (mes-año)
    df['PERIODO'] = df['FECHA'].dt.strftime('%Y-%m')
    
    # Calcular utilidad bruta
    df['UTILIDAD_BRUTA'] = df['TOTAL_COBRADO'] - df['PAGO_BROKER']
    
    # Calcular margen bruto (evitar división por cero)
    df['MARGEN_BRUTO'] = np.where(
        df['TOTAL_COBRADO'] > 0,
        (df['UTILIDAD_BRUTA'] / df['TOTAL_COBRADO']) * 100,
        0
    )
    
    return df

# Cargar datos
df = load_data()

# Crear resúmenes para los diferentes análisis
@st.cache_data
def create_summaries(df):
    # Resumen por cliente
    resumen_cliente = df.groupby('CLIENTE').agg({
        'FACTURA': 'nunique',
        'TOTAL_COBRADO': 'sum',
        'PAGO_BROKER': 'sum',
        'UTILIDAD_BRUTA': 'sum'
    }).reset_index()
    resumen_cliente = resumen_cliente.rename(columns={'FACTURA': 'NUM_FACTURAS'})
    resumen_cliente['MARGEN_PORCENTAJE'] = np.where(
        resumen_cliente['TOTAL_COBRADO'] > 0,
        (resumen_cliente['UTILIDAD_BRUTA'] / resumen_cliente['TOTAL_COBRADO']) * 100,
        0
    )
    
    # Resumen por proyecto
    resumen_proyecto = df.groupby(['CLIENTE', 'PROYECTO_OK']).agg({
        'FACTURA': 'nunique',
        'TOTAL_COBRADO': 'sum',
        'PAGO_BROKER': 'sum',
        'UTILIDAD_BRUTA': 'sum'
    }).reset_index()
    resumen_proyecto = resumen_proyecto.rename(columns={
        'PROYECTO_OK': 'PROYECTO',
        'FACTURA': 'NUM_FACTURAS'
    })
    resumen_proyecto['MARGEN_PORCENTAJE'] = np.where(
        resumen_proyecto['TOTAL_COBRADO'] > 0,
        (resumen_proyecto['UTILIDAD_BRUTA'] / resumen_proyecto['TOTAL_COBRADO']) * 100,
        0
    )
    
    # Resumen por período
    resumen_periodo = df.groupby('PERIODO').agg({
        'FACTURA': 'nunique',
        'TOTAL_COBRADO': 'sum',
        'PAGO_BROKER': 'sum',
        'UTILIDAD_BRUTA': 'sum'
    }).reset_index()
    resumen_periodo = resumen_periodo.rename(columns={'FACTURA': 'NUM_FACTURAS'})
    resumen_periodo['MARGEN_PORCENTAJE'] = np.where(
        resumen_periodo['TOTAL_COBRADO'] > 0,
        (resumen_periodo['UTILIDAD_BRUTA'] / resumen_periodo['TOTAL_COBRADO']) * 100,
        0
    )
    
    # Resumen por broker
    resumen_broker = df.groupby('BROKER').agg({
        'FACTURA': 'nunique',
        'PAGO_BROKER': 'sum',
        'TOTAL_COBRADO': 'sum'
    }).reset_index()
    resumen_broker = resumen_broker.rename(columns={
        'FACTURA': 'NUM_SERVICIOS',
        'PAGO_BROKER': 'TOTAL_PAGADO'
    })
    
    # Datos detallados para tabla principal
    datos_detallados = df[[
        'FECHA', 'FACTURA', 'CLIENTE', 'PROYECTO_OK',
        'HORAS_VIAJE', 'COSTO_UNITARIO', 'TOTAL_COBRADO',
        'PAGO_BROKER', 'UTILIDAD_BRUTA', 'MARGEN_BRUTO',
        'PERIODO', 'BROKER'
    ]].copy()
    
    return datos_detallados, resumen_cliente, resumen_proyecto, resumen_periodo, resumen_broker

# Crear resúmenes
datos_detallados, resumen_cliente, resumen_proyecto, resumen_periodo, resumen_broker = create_summaries(df)

# Título principal
st.title("📊 Dashboard de Facturas - Análisis Financiero")
st.markdown("---")

# KPIs generales en la barra lateral
st.sidebar.header("📈 KPIs Principales")

# Calcular KPIs
total_ingresos = datos_detallados['TOTAL_COBRADO'].sum()
total_pagos_broker = datos_detallados['PAGO_BROKER'].sum()
total_utilidad = datos_detallados['UTILIDAD_BRUTA'].sum()
total_facturas = datos_detallados['FACTURA'].nunique()
total_clientes = datos_detallados['CLIENTE'].nunique()

# Evitar división por cero
margen_promedio = (total_utilidad / total_ingresos * 100) if total_ingresos > 0 else 0

st.sidebar.metric("Total Ingresos", f"${total_ingresos:,.2f}")
st.sidebar.metric("Total Pagos Broker", f"${total_pagos_broker:,.2f}")
st.sidebar.metric("Utilidad Bruta", f"${total_utilidad:,.2f}")
st.sidebar.metric("Margen Promedio", f"{margen_promedio:.2f}%")
st.sidebar.metric("Número de Facturas", f"{total_facturas}")
st.sidebar.metric("Número de Clientes", f"{total_clientes}")

# Filtros en la barra lateral
st.sidebar.markdown("---")
st.sidebar.header("🔎 Filtros")

# Filtro por cliente
clientes = ['Todos'] + sorted(datos_detallados['CLIENTE'].dropna().unique().tolist())
cliente_seleccionado = st.sidebar.selectbox("Cliente", clientes)

# Filtro por período
periodos = ['Todos'] + sorted(datos_detallados['PERIODO'].dropna().unique().tolist(), reverse=True)
periodo_seleccionado = st.sidebar.selectbox("Período", periodos)

# Filtro por broker
brokers = ['Todos'] + sorted(datos_detallados['BROKER'].dropna().unique().tolist())
broker_seleccionado = st.sidebar.selectbox("Broker", brokers)

# Aplicar filtros
datos_filtrados = datos_detallados.copy()

if cliente_seleccionado != 'Todos':
    datos_filtrados = datos_filtrados[datos_filtrados['CLIENTE'] == cliente_seleccionado]

if periodo_seleccionado != 'Todos':
    datos_filtrados = datos_filtrados[datos_filtrados['PERIODO'] == periodo_seleccionado]

if broker_seleccionado != 'Todos':
    datos_filtrados = datos_filtrados[datos_filtrados['BROKER'] == broker_seleccionado]

# Tabs principales
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Resumen General", 
    "🎯 Clientes", 
    "🏗️ Proyectos", 
    "📅 Períodos", 
    "💼 Brokers",
    "📄 Detalle"
])

# Tab 1: Resumen General
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pastel: Distribución de ingresos por cliente
        if cliente_seleccionado == 'Todos':
            top_clientes = resumen_cliente.nlargest(10, 'TOTAL_COBRADO')
            fig_pie = px.pie(top_clientes, values='TOTAL_COBRADO', names='CLIENTE', 
                             title='Top 10 Clientes por Ingresos',
                             hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            # Para un cliente específico, mostrar distribución por proyecto
            cliente_data = resumen_proyecto[resumen_proyecto['CLIENTE'] == cliente_seleccionado]
            if not cliente_data.empty:
                fig_pie = px.pie(cliente_data, values='TOTAL_COBRADO', names='PROYECTO',
                                 title=f'Distribución de Ingresos por Proyecto - {cliente_seleccionado}',
                                 hole=0.3)
                st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Gráfico de barras: Margen por cliente
        margen_data = resumen_cliente[resumen_cliente['TOTAL_COBRADO'] > 0].nlargest(15, 'MARGEN_PORCENTAJE')
        fig_margen = px.bar(margen_data, 
                           x='MARGEN_PORCENTAJE', y='CLIENTE', orientation='h',
                           title='Top 15 Clientes por Margen (%)',
                           labels={'MARGEN_PORCENTAJE': 'Margen (%)'},
                           color='MARGEN_PORCENTAJE',
                           color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_margen, use_container_width=True)
    
    # Evolución temporal de ingresos y pagos
    fig_evolucion = px.line(resumen_periodo, x='PERIODO', y=['TOTAL_COBRADO', 'PAGO_BROKER'],
                           title='Evolución de Ingresos y Pagos a Brokers por Período',
                           markers=True)
    fig_evolucion.update_layout(xaxis_title="Período", yaxis_title="Monto ($)")
    st.plotly_chart(fig_evolucion, use_container_width=True)

# Tab 2: Análisis por Cliente
with tab2:
    st.header("Análisis Detallado por Cliente")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Tabla interactiva de clientes
        display_clients = resumen_cliente[['CLIENTE', 'NUM_FACTURAS', 'TOTAL_COBRADO', 
                                          'PAGO_BROKER', 'UTILIDAD_BRUTA', 'MARGEN_PORCENTAJE']].copy()
        display_clients = display_clients.sort_values('UTILIDAD_BRUTA', ascending=False)
        display_clients['TOTAL_COBRADO'] = display_clients['TOTAL_COBRADO'].map('${:,.2f}'.format)
        display_clients['PAGO_BROKER'] = display_clients['PAGO_BROKER'].map('${:,.2f}'.format)
        display_clients['UTILIDAD_BRUTA'] = display_clients['UTILIDAD_BRUTA'].map('${:,.2f}'.format)
        display_clients['MARGEN_PORCENTAJE'] = display_clients['MARGEN_PORCENTAJE'].map('{:.2f}%'.format)
        
        st.dataframe(display_clients, 
                     height=400, 
                     use_container_width=True,
                     column_config={
                         "CLIENTE": "Cliente",
                         "NUM_FACTURAS": "# Facturas",
                         "TOTAL_COBRADO": "Total Cobrado",
                         "PAGO_BROKER": "Pago Broker",
                         "UTILIDAD_BRUTA": "Utilidad Bruta",
                         "MARGEN_PORCENTAJE": "Margen %"
                     })
    
    with col2:
        # Gráfico de barras de ingresos por cliente
        fig_ingresos = px.bar(resumen_cliente.nlargest(10, 'TOTAL_COBRADO'), 
                             x='TOTAL_COBRADO', y='CLIENTE', orientation='h',
                             title='Top 10 Ingresos por Cliente',
                             color='TOTAL_COBRADO',
                             color_continuous_scale='Blues')
        st.plotly_chart(fig_ingresos, use_container_width=True)
    
    # Scatter plot: Ingresos vs Margen
    fig_scatter = px.scatter(resumen_cliente, 
                            x='TOTAL_COBRADO', 
                            y='MARGEN_PORCENTAJE',
                            size='NUM_FACTURAS', 
                            color='CLIENTE',
                            title='Ingresos vs Margen por Cliente',
                            hover_name='CLIENTE',
                            hover_data=['NUM_FACTURAS', 'UTILIDAD_BRUTA'])
    fig_scatter.update_layout(xaxis_title="Total Cobrado ($)", yaxis_title="Margen (%)")
    st.plotly_chart(fig_scatter, use_container_width=True)

# Tab 3: Análisis por Proyecto
with tab3:
    st.header("Análisis por Proyecto")
    
    # Filtro adicional por cliente para proyectos
    cliente_proyecto = st.selectbox("Filtrar por Cliente (opcional)", 
                                   ['Todos'] + sorted(resumen_proyecto['CLIENTE'].unique().tolist()),
                                   key="cliente_proyecto")
    
    if cliente_proyecto != 'Todos':
        proyectos_data = resumen_proyecto[resumen_proyecto['CLIENTE'] == cliente_proyecto]
    else:
        proyectos_data = resumen_proyecto
    
    # Top proyectos más rentables
    col1, col2 = st.columns(2)
    
    with col1:
        top_proyectos_utilidad = proyectos_data.nlargest(10, 'UTILIDAD_BRUTA')
        if not top_proyectos_utilidad.empty:
            fig_proy_utilidad = px.bar(top_proyectos_utilidad, 
                                      x='UTILIDAD_BRUTA', y='PROYECTO', orientation='h',
                                      title='Top 10 Proyectos por Utilidad Bruta',
                                      color='UTILIDAD_BRUTA',
                                      color_continuous_scale='Greens')
            st.plotly_chart(fig_proy_utilidad, use_container_width=True)
    
    with col2:
        top_proyectos_margen = proyectos_data.nlargest(10, 'MARGEN_PORCENTAJE')
        if not top_proyectos_margen.empty:
            fig_proy_margen = px.bar(top_proyectos_margen, 
                                    x='MARGEN_PORCENTAJE', y='PROYECTO', orientation='h',
                                    title='Top 10 Proyectos por Margen (%)',
                                    color='MARGEN_PORCENTAJE',
                                    color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_proy_margen, use_container_width=True)
    
    # Tabla filtrable de proyectos
    st.subheader("Detalle de Proyectos")
    display_proyectos = proyectos_data[['CLIENTE', 'PROYECTO', 'NUM_FACTURAS', 
                                       'TOTAL_COBRADO', 'PAGO_BROKER', 
                                       'UTILIDAD_BRUTA', 'MARGEN_PORCENTAJE']].copy()
    display_proyectos = display_proyectos.sort_values('UTILIDAD_BRUTA', ascending=False)
    
    # Formatear valores
    display_proyectos['TOTAL_COBRADO'] = display_proyectos['TOTAL_COBRADO'].map('${:,.2f}'.format)
    display_proyectos['PAGO_BROKER'] = display_proyectos['PAGO_BROKER'].map('${:,.2f}'.format)
    display_proyectos['UTILIDAD_BRUTA'] = display_proyectos['UTILIDAD_BRUTA'].map('${:,.2f}'.format)
    display_proyectos['MARGEN_PORCENTAJE'] = display_proyectos['MARGEN_PORCENTAJE'].map('{:.2f}%'.format)
    
    st.dataframe(display_proyectos, 
                 height=300, 
                 use_container_width=True,
                 column_config={
                     "CLIENTE": "Cliente",
                     "PROYECTO": "Proyecto",
                     "NUM_FACTURAS": "# Facturas",
                     "TOTAL_COBRADO": "Total Cobrado",
                     "PAGO_BROKER": "Pago Broker",
                     "UTILIDAD_BRUTA": "Utilidad Bruta",
                     "MARGEN_PORCENTAJE": "Margen %"
                 })

# Tab 4: Análisis por Período
with tab4:
    st.header("Análisis Temporal por Período")
    
    # Métricas por período
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_periodo_ingresos = px.bar(resumen_periodo, x='PERIODO', y='TOTAL_COBRADO',
                                     title='Ingresos por Período',
                                     color='TOTAL_COBRADO',
                                     color_continuous_scale='Blues')
        st.plotly_chart(fig_periodo_ingresos, use_container_width=True)
    
    with col2:
        fig_periodo_utilidad = px.bar(resumen_periodo, x='PERIODO', y='UTILIDAD_BRUTA',
                                     title='Utilidad Bruta por Período',
                                     color='UTILIDAD_BRUTA',
                                     color_continuous_scale='Greens')
        st.plotly_chart(fig_periodo_utilidad, use_container_width=True)
    
    with col3:
        fig_periodo_margen = px.line(resumen_periodo, x='PERIODO', y='MARGEN_PORCENTAJE',
                                    title='Margen % por Período',
                                    markers=True)
        fig_periodo_margen.update_traces(line=dict(color='orange', width=3))
        st.plotly_chart(fig_periodo_margen, use_container_width=True)
    
    # Análisis de tendencia
    resumen_periodo_sorted = resumen_periodo.sort_values('PERIODO')
    resumen_periodo_sorted['TENDENCIA_INGRESOS'] = resumen_periodo_sorted['TOTAL_COBRADO'].pct_change() * 100
    resumen_periodo_sorted['TENDENCIA_UTILIDAD'] = resumen_periodo_sorted['UTILIDAD_BRUTA'].pct_change() * 100
    
    fig_tendencia = make_subplots(rows=2, cols=1, 
                                  subplot_titles=('Tendencia de Crecimiento de Ingresos (%)', 
                                                  'Tendencia de Crecimiento de Utilidad (%)'))
    
    fig_tendencia.add_trace(
        go.Scatter(x=resumen_periodo_sorted['PERIODO'], 
                  y=resumen_periodo_sorted['TENDENCIA_INGRESOS'],
                  name='Ingresos',
                  line=dict(color='blue', width=2)),
        row=1, col=1
    )
    
    fig_tendencia.add_trace(
        go.Scatter(x=resumen_periodo_sorted['PERIODO'], 
                  y=resumen_periodo_sorted['TENDENCIA_UTILIDAD'],
                  name='Utilidad',
                  line=dict(color='green', width=2)),
        row=2, col=1
    )
    
    fig_tendencia.update_layout(height=600, showlegend=True)
    fig_tendencia.update_xaxes(title_text="Período", row=2, col=1)
    fig_tendencia.update_yaxes(title_text="Crecimiento (%)", row=1, col=1)
    fig_tendencia.update_yaxes(title_text="Crecimiento (%)", row=2, col=1)
    
    st.plotly_chart(fig_tendencia, use_container_width=True)

# Tab 5: Análisis por Broker
with tab5:
    st.header("Análisis de Pagos por Broker")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Top brokers por pago
        top_brokers = resumen_broker.nlargest(15, 'TOTAL_PAGADO')
        fig_broker = px.bar(top_brokers, x='TOTAL_PAGADO', y='BROKER', orientation='h',
                           title='Top 15 Brokers por Total Pagado',
                           color='TOTAL_PAGADO',
                           color_continuous_scale='Purples')
        fig_broker.update_layout(xaxis_title="Total Pagado ($)", yaxis_title="Broker")
        st.plotly_chart(fig_broker, use_container_width=True)
    
    with col2:
        # Distribución de brokers
        top_10_brokers = resumen_broker.nlargest(10, 'TOTAL_PAGADO')
        fig_broker_pie = px.pie(top_10_brokers, 
                               values='TOTAL_PAGADO', names='BROKER',
                               title='Distribución Top 10 Brokers',
                               hole=0.4)
        st.plotly_chart(fig_broker_pie, use_container_width=True)
    
    # Tabla de brokers
    st.subheader("Detalle de Brokers")
    display_brokers = resumen_broker[['BROKER', 'NUM_SERVICIOS', 'TOTAL_PAGADO', 'TOTAL_COBRADO']].copy()
    display_brokers = display_brokers.sort_values('TOTAL_PAGADO', ascending=False)
    
    # Formatear valores
    display_brokers['TOTAL_PAGADO'] = display_brokers['TOTAL_PAGADO'].map('${:,.2f}'.format)
    display_brokers['TOTAL_COBRADO'] = display_brokers['TOTAL_COBRADO'].map('${:,.2f}'.format)
    
    st.dataframe(display_brokers, 
                 height=400, 
                 use_container_width=True,
                 column_config={
                     "BROKER": "Broker",
                     "NUM_SERVICIOS": "# Servicios",
                     "TOTAL_PAGADO": "Total Pagado",
                     "TOTAL_COBRADO": "Total Cobrado"
                 })

# Tab 6: Detalle de Facturas
with tab6:
    st.header("📄 Detalle de Facturas")
    
    # Mostrar métricas del período seleccionado
    if periodo_seleccionado != 'Todos':
        periodo_data = datos_filtrados[datos_filtrados['PERIODO'] == periodo_seleccionado]
        if not periodo_data.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(f"Ingresos {periodo_seleccionado}", 
                         f"${periodo_data['TOTAL_COBRADO'].sum():,.2f}")
            with col2:
                st.metric(f"Pagos Broker {periodo_seleccionado}", 
                         f"${periodo_data['PAGO_BROKER'].sum():,.2f}")
            with col3:
                st.metric(f"Utilidad {periodo_seleccionado}", 
                         f"${periodo_data['UTILIDAD_BRUTA'].sum():,.2f}")
            with col4:
                margen = (periodo_data['UTILIDAD_BRUTA'].sum() / periodo_data['TOTAL_COBRADO'].sum() * 100) if periodo_data['TOTAL_COBRADO'].sum() > 0 else 0
                st.metric(f"Margen {periodo_seleccionado}", 
                         f"{margen:.2f}%")
    
    # Tabla detallada
    display_detalle = datos_filtrados[[
        'FECHA', 'FACTURA', 'CLIENTE', 'PROYECTO_OK',
        'HORAS_VIAJE', 'COSTO_UNITARIO', 'TOTAL_COBRADO',
        'PAGO_BROKER', 'UTILIDAD_BRUTA', 'MARGEN_BRUTO', 'BROKER'
    ]].copy()
    
    # Formatear valores
    display_detalle['COSTO_UNITARIO'] = display_detalle['COSTO_UNITARIO'].map('${:,.2f}'.format)
    display_detalle['TOTAL_COBRADO'] = display_detalle['TOTAL_COBRADO'].map('${:,.2f}'.format)
    display_detalle['PAGO_BROKER'] = display_detalle['PAGO_BROKER'].map('${:,.2f}'.format)
    display_detalle['UTILIDAD_BRUTA'] = display_detalle['UTILIDAD_BRUTA'].map('${:,.2f}'.format)
    display_detalle['MARGEN_BRUTO'] = display_detalle['MARGEN_BRUTO'].map('{:.2f}%'.format)
    
    st.dataframe(display_detalle.sort_values('FECHA', ascending=False), 
                 height=500, 
                 use_container_width=True,
                 column_config={
                     "FECHA": "Fecha",
                     "FACTURA": "Factura",
                     "CLIENTE": "Cliente",
                     "PROYECTO_OK": "Proyecto",
                     "HORAS_VIAJE": "Horas/Viaje",
                     "COSTO_UNITARIO": "Costo Unitario",
                     "TOTAL_COBRADO": "Total Cobrado",
                     "PAGO_BROKER": "Pago Broker",
                     "UTILIDAD_BRUTA": "Utilidad Bruta",
                     "MARGEN_BRUTO": "Margen %",
                     "BROKER": "Broker"
                 })
    
    # Opción para descargar datos filtrados
    csv = datos_filtrados.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos filtrados como CSV",
        data=csv,
        file_name=f"facturas_filtradas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

# Footer
st.markdown("---")
st.markdown("**Dashboard de Facturas** | Generado con Streamlit | Datos actualizados")