#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 20:00:58 2024

Reporte de gastos de viajes

@author: marcorustrian
"""

# Instalamos librerias necesarias
#!pip install streamlit pandas plotly openpyxl
#!pip install streamlit folium geopy streamlit-folium
#! pip install geopandas plotly pandas
#!pip install pyinstaller



import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re
import folium
from streamlit_folium import st_folium  # Para integrar mapas Folium en Streamlit



# Funciones necesarias del codigo
# Función para extraer información del campo "Concepto"
def extraer_info_viaje(concepto):
    if isinstance(concepto, str) and "Viaje del" in concepto:
        fecha_inicio = re.search(r"Viaje del (\d{2}\.\d{2}\.\d{2})", concepto)
        fecha_fin = re.search(r"a\s+(\d{2}\.\d{2}\.\d{2})", concepto)
        destino = re.search(r"A .. ([A-Za-z0-9]+)", concepto)
        return {
            "fecha_inicio": fecha_inicio.group(1) if fecha_inicio else None,
            "fecha_fin": fecha_fin.group(1) if fecha_fin else None,
            "destino": destino.group(1)[:-1] if destino else None  # Quitamos el dígito final
        }
    return {"fecha_inicio": None, "fecha_fin": None, "destino": None}




# ----------------------------------

# Configurar el título del dashboard
st.title("Dashboard Interactivo - Gastos de Viajes")



# Verificar si el archivo existe automáticamente
file_path = "ArchivoViajes.xlsx"

# Cargar datos procesados automáticamente en Streamlit
if os.path.exists(file_path):
    ArchivoViajes = pd.read_excel(file_path)
    # Procesar columna "Concepto"
    ArchivoViajes["info_viaje"] = ArchivoViajes["Concepto"].apply(extraer_info_viaje)
    ArchivoViajes["Fecha_Inicio"] = ArchivoViajes["info_viaje"].apply(lambda x: x["fecha_inicio"])
    ArchivoViajes["Fecha_Fin"] = ArchivoViajes["info_viaje"].apply(lambda x: x["fecha_fin"])
    ArchivoViajes["Destino_Extraido"] = ArchivoViajes["info_viaje"].apply(lambda x: x["destino"])
    ArchivoViajes["Destino_final"] = ArchivoViajes.apply(
        lambda row: row["Poblacion"] if pd.notna(row["Poblacion"]) else row["Destino_Extraido"], axis=1
    )
    ArchivoViajes.drop(columns=["info_viaje"], inplace=True)
else:
    st.error("El archivo ArchivoViajes.xlsx no está disponible en el directorio.")
if file_path:
    # Cargar los datos
    data = ArchivoViajes.copy()

    # Filtros interactivos
    st.sidebar.header("Filtros")
    tipo_servicio = st.sidebar.multiselect("Selecciona Tipo de Servicio", options=data["Tipo de Servicio"].unique())
    mes = st.sidebar.multiselect("Selecciona Mes", options=data["Mes"].unique())
    posicion = st.sidebar.multiselect("Selecciona Posición", options=data["Posición"].unique())
    colaborador = st.sidebar.multiselect("Selecciona Colaborador", options=data["Colaborador"].unique())
    area = st.sidebar.multiselect("Selecciona Área", options=data["Área"].unique())
    subdireccion = st.sidebar.multiselect("Selecciona Subdirección", options=data["Subdirección"].unique())

    # Aplicar los filtros
    filtered_data = data.copy()
    if tipo_servicio:
        filtered_data = filtered_data[filtered_data["Tipo de Servicio"].isin(tipo_servicio)]
    if mes:
        filtered_data = filtered_data[filtered_data["Mes"].isin(mes)]
    if posicion:
        filtered_data = filtered_data[filtered_data["Posición"].isin(posicion)]
    if colaborador:
        filtered_data = filtered_data[filtered_data["Colaborador"].isin(colaborador)]
    if area:
        filtered_data = filtered_data[filtered_data["Área"].isin(area)]
    if subdireccion:
        filtered_data = filtered_data[filtered_data["Subdirección"].isin(subdireccion)]
        
    
    # Agregar una sección de instrucciones para usar el dashboard
    st.sidebar.title("Instrucciones de Uso")
    st.sidebar.info("""
    1. **Selecciona los Filtros**:
        - Usa los menús desplegables en la barra lateral para aplicar los filtros deseados.
        - Puedes filtrar por **Tipo de Servicio**, **Mes**, **Posición**, **Colaborador**, **Área**, y **Subdirección**.
        - Al aplicar un filtro, los datos en todas las tablas y gráficos del dashboard se actualizarán automáticamente para reflejar la información filtrada.

    2. **Interpreta los Gráficos**:
        - El gráfico **Gasto Total por Tipo de Servicio** muestra cuánto se ha gastado en cada tipo de servicio seleccionado.
        - El gráfico **Gasto Mensual por Tipo de Servicio** apilado permite observar los gastos por mes y por tipo de servicio.

    3. **Consulta las Tablas**:
        - La **Tabla de Totales y Porcentajes** muestra un resumen del gasto total y su porcentaje respecto al total general.
        - La **Tabla de Gastos por Lugar y Tipo de Servicio** agrupa los gastos por el lugar de destino (columna `Destino_final`) y los divide por tipo de servicio.
        - La **Tabla de Gastos por Concepto y Tipo de Servicio** organiza los gastos por cada concepto del viaje y está ordenada de mayor a menor gasto total.

    4. **Información General**:
        - Todas las tablas incluyen totales para cada fila y columna.
        - Los valores monetarios están formateados en **MXN** para facilitar su interpretación.

    5. **Actualización Automática**:
        - Una vez que subas un archivo nuevo en el formato adecuado, el dashboard procesará y actualizará la información automáticamente.
    """)
        


    # Tabla de totales
    st.header("Tabla de Totales y Porcentajes")
    if not filtered_data.empty:
        total_importe = filtered_data["Importe"].sum()
        resumen = (
            filtered_data.groupby("Tipo de Servicio")["Importe"]
            .sum()
            .reset_index()
            .rename(columns={"Importe": "Total Gasto"})
        )
        resumen["% del Total"] = (resumen["Total Gasto"] / total_importe) * 100
        st.dataframe(resumen.style.format({"Total Gasto": "${:,.2f}", "% del Total": "{:.2f}%"}))
    else:
        st.warning("No hay datos para mostrar en esta tabla.")
    


    # Gráfico 1: Gasto total por Tipo de Servicio
    st.header("Gráfico: Gasto total por Tipo de Servicio")
    if not filtered_data.empty:
        # Agrupar los datos por "Tipo de Servicio" para calcular el total por cada tipo
        grouped_data = filtered_data.groupby("Tipo de Servicio", as_index=False)["Importe"].sum()
        fig1 = px.bar(
            grouped_data,
            x="Tipo de Servicio",
            y="Importe",
            color="Tipo de Servicio",
            title="Gasto por Tipo de Servicio",
            labels={"Importe": "Total Gasto"},
            text="Importe"  # Mostrar el total directamente en las barras
        )
        fig1.update_traces(
            texttemplate='%{text:.2s}', 
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Total Gasto: $%{y:,.2f} MXN<br>'
        )  # Formato del tooltip
        fig1.update_layout(hovermode="x unified")  # Mostrar valores unificados al pasar el mouse
        st.plotly_chart(fig1)
    else:
        st.warning("No hay datos para mostrar en este gráfico.")


    # Gráfico 2: Gasto por mes con barras apiladas
    st.header("Gráfico: Gasto Mensual por Tipo de Servicio (Apiladas)")
    if not filtered_data.empty:
        # Asegurar el orden correcto de los meses
        meses_ordenados = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        filtered_data["Mes"] = pd.Categorical(filtered_data["Mes"], categories=meses_ordenados, ordered=True)
        
        # Agrupar los datos por "Mes" y "Tipo de Servicio"
        grouped_data_month = filtered_data.groupby(["Mes", "Tipo de Servicio"], as_index=False)["Importe"].sum()
    
        fig2 = px.bar(
            grouped_data_month,
            x="Mes",
            y="Importe",
            color="Tipo de Servicio",
            title="Gasto Mensual por Tipo de Servicio (Apiladas)",
            barmode="stack",  # Cambiado a 'stack' para barras apiladas
            labels={"Importe": "Total Gasto"},
        )
        
        # Personalizar los tooltips y mostrar toda la información
        fig2.update_traces(
            hovertemplate="<b>Mes: %{x}</b><br>Tipo de Servicio: %{customdata[0]}<br>Total Gasto: $%{y:,.0f} MXN",
            customdata=grouped_data_month[["Tipo de Servicio"]].to_numpy(),
        )
        
        # Ajustes de diseño
        fig2.update_layout(
            xaxis={"categoryorder": "array", "categoryarray": meses_ordenados},  # Asegurar el orden cronológico
            yaxis_title="Total Gasto",
            xaxis_title="Mes",
            hoverlabel=dict(font_size=12),
        )
        st.plotly_chart(fig2)
    else:
        st.warning("No hay datos para mostrar en este gráfico.")

    
    # Tabla de gastos por colaborador y tipo de servicio
    st.header("Tabla de Gastos por Colaborador y Tipo de Servicio")
    if not filtered_data.empty:
        # Agrupar los datos por Colaborador y Tipo de Servicio
        gastos_colaborador = (
            filtered_data.groupby(["Colaborador", "Tipo de Servicio"])["Importe"]
            .sum()
            .reset_index()
            .pivot(index="Colaborador", columns="Tipo de Servicio", values="Importe")
            .fillna(0)  # Rellenar valores nulos con 0
        )
        
        # Agregar una columna de total por colaborador
        gastos_colaborador["Total Gasto"] = gastos_colaborador.sum(axis=1)
        
        # Agregar una fila de totales para cada tipo de servicio
        total_column = gastos_colaborador.sum(axis=0).to_frame().T
        total_column.index = ["Total"]
        gastos_colaborador = pd.concat([gastos_colaborador, total_column])
    
        # Formatear los datos como tabla
        st.dataframe(
            gastos_colaborador.style.format("${:,.2f}")  # Formatear como moneda
        )
    else:
        st.warning("No hay datos para mostrar en esta tabla.")
        
    # Tabla de gastos por concepto y tipo de servicio
    st.header("Tabla de Gastos por Concepto y Tipo de Servicio")
    if not filtered_data.empty:
        # Agrupar los datos por 'Concepto' y 'Tipo de Servicio' y sumar 'Importe'
        gastos_concepto = (
            filtered_data.groupby(["Concepto", "Tipo de Servicio"])["Importe"]
            .sum()
            .reset_index()
            .pivot(index="Concepto", columns="Tipo de Servicio", values="Importe")
            .fillna(0)
        )
        
        # Agregar columna de Total Gasto por 'Concepto'
        gastos_concepto["Total Gasto"] = gastos_concepto.sum(axis=1)
        
        # Ordenar la tabla de mayor a menor según 'Total Gasto'
        gastos_concepto = gastos_concepto.sort_values(by="Total Gasto", ascending=False)
        
        # Agregar fila de Totales por 'Tipo de Servicio' y 'Total Gasto'
        total_column = gastos_concepto.sum(axis=0).to_frame().T
        total_column.index = ["Total"]
        gastos_concepto = pd.concat([gastos_concepto, total_column])
        
        # Formatear los datos como tabla
        st.dataframe(
            gastos_concepto.style.format("${:,.2f}")
        )
    else:
        st.warning("No hay datos para mostrar en esta tabla.")

    
    
    # Tabla de gastos por lugar y tipo de servicio
    st.header("Tabla de Gastos por Lugar y Tipo de Servicio")
    if not filtered_data.empty:
        # Agrupar los datos por Lugar y Tipo de Servicio
        gastos_lugar = (
            filtered_data.groupby(["Destino_final", "Tipo de Servicio"])["Importe"]
            .sum()
            .reset_index()
            .pivot(index="Destino_final", columns="Tipo de Servicio", values="Importe")
            .fillna(0)  # Rellenar valores nulos con 0
        )
        
        # Agregar una columna de total por lugar
        gastos_lugar["Total Gasto"] = gastos_lugar.sum(axis=1)
        
        # Formatear los datos como tabla
        st.dataframe(
            gastos_lugar.style.format("${:,.2f}")  # Formatear como moneda
        )
    else:
        st.warning("No hay datos para mostrar en esta tabla.")
        
        
    # Mostrar datos filtrados
    st.write("Datos filtrados:")
    st.dataframe(filtered_data)


   

# Mensaje inicial
else:
    st.write("Sube un archivo Excel para empezar.")
