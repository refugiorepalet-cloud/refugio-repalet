import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Configuración panorámica estable de la interfaz
st.set_page_config(page_title="Refugio Repalet", layout="wide")

# =========================================================================
# --- CONTROL DE VISTAS (PÚBLICA VS ADMINISTRATIVA) Y SEGURIDAD ---
# =========================================================================

# 1. Detectar si el usuario ingresa mediante el enlace de la versión pública
query_params = st.query_params
es_version_publica = query_params.get("view") == "public"

# Contraseña del panel administrativo (puedes cambiar 'Repalet2026' por la que gustes)
CONTRASEÑA_CORRECTA = "Repalet2026"

# Inicializar estados de la sesión
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "registros" not in st.session_state:
    st.session_state.registros = []

# Función auxiliar para calcular ocupación de un mes determinado
def obtener_ocupacion_mes(mes, anio):
    ocupacion = {d: {"Cabaña 1": False, "Cabaña 2": False} for d in range(1, 33)}
    for r in st.session_state.registros:
        if r["estado"] == "Activo":
            curr = r["ingreso"]
            while curr < r["salida"]:
                if curr.month == mes and curr.year == anio:
                    ocupacion[curr.day][r["Cabaña"]] = True
                curr += timedelta(days=1)
    return ocupacion

# Función para dibujar el diseño del calendario adaptativo en HTML
def renderizar_calendario_html(anio, mes, ocupacion, titulo_mes):
    cal_matriz = calendar.monthcalendar(anio, mes)
    
    # Cabecera solicitada: Lu-Ma-Mi-Ju-Vi-Sa-Do
    html_tabla = f"""
    <div style="background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 10px;">
        <h3 style="text-align: center; color: #1E3A8A; font-family: Arial, sans-serif; margin-bottom: 15px;">📅 Calendario de Ocupación - {titulo_mes} {anio}</h3>
        <table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif; text-align: center; background-color: #ffffff;">
            <thead>
                <tr style="background-color: #f3f4f6; color: #4b5563; font-weight: bold; border-bottom: 2px solid #e5e7eb;">
                    <th style="padding: 12px; border: 1px solid #e5e7eb; width: 14.28%;">Lu</th>
                    <th style="padding: 12px; border: 1px solid #e5e7eb; width: 14.28%;">Ma</th>
                    <th style="padding: 12px; border: 1px solid #e5e7eb; width: 14.28%;">Mi</th>
                    <th style="padding: 12px; border: 1px solid #e5e7eb; width: 14.28%;">Ju</th>
                    <th style="padding: 12px; border: 1px solid #e5e7eb; width: 14.28%;">Vi</th>
                    <th style="padding: 12px; border: 1px solid #e5e7eb; width: 14.28%;">Sa</th>
                    <th style="padding: 12px; border: 1px solid #e5e7eb; width: 14.28%;">Do</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for semana in cal_matriz:
        html_tabla += "<tr style='height: 75px;'>"
        for dia in Array := semana:
            if dia == 0:
                html_tabla += "<td style='border: 1px solid #e5e7eb; background-color: #fafafa;'></td>"
            else:
                c1 = ocupacion[dia]["Cabaña 1"]
                c2 = ocupacion[dia]["Cabaña 2"]
                
                # Definición del estilo de fondo según la ocupación (Colores y División de Módulos)
                if c1 and c2:
                    # Ambas cabañas coinciden: dividimos el módulo en dos mitades perfectas con CSS lineal
                    estilo_fondo = "background: linear-gradient(135deg, #DEF7EC 50%, #EBF5FF 50%);"
                elif c1:
                    # Cabaña 1 activa (Fondo Verde Suave)
                    estilo_fondo = "background-color: #DEF7EC;" 
                elif c2:
                    # Cabaña 2 activa (Fondo Azul Suave)
                    estilo_fondo = "background-color: #EBF5FF;"
                else:
                    # Sin ocupación
                    estilo_fondo = "background-color: #ffffff;"
                
                # Círculos indicadores internos
                indicadores = ""
                if c1 and c2:
                    indicadores = '<span style="display:inline-block; width:10px; height:10px; background-color:#31C48D; border-radius:50%; margin: 2px;"></span><span style="display:inline-block; width:10px; height:10px; background-color:#3F83F8; border-radius:50%; margin: 2px;"></span>'
                elif c1:
                    indicadores = '<span style="display:inline-block; width:12px; height:12px; background-color:#31C48D; border-radius:50%;"></span>'
                elif c2:
                    indicadores = '<span style="display:inline-block; width:12px; height:12px; background-color:#3F83F8; border-radius:50%;"></span>'
                else:
                    indicadores = '<span style="display:inline-block; width:12px; height:12px; background-color:#e5e7eb; border-radius:50%;"></span>'

                html_tabla += f"""
                <td style="border: 1px solid #e5e7eb; {estilo_fondo} vertical-align: middle; padding: 5px;">
                    <div style="font-size: 16px; font-weight: 600; color: #9ca3af; margin-bottom: 4px;">{dia}</div>
                    <div style="height: 15px; display: flex; justify-content: center; align-items: center;">{indicadores}</div>
                </td>
                """
        html_tabla += "</tr>"
        
    html_tabla += """
            </tbody>
        </table>
    </div>
    """
    return html_tabla


# =========================================================================
# --- RENDERIZADO CONDICIONAL DE LAS VISTAS ---
# =========================================================================

if es_version_publica:
    # ---------------------------------------------------------------------
    # VERSION PÚBLICA: Solo lectura, sin datos privados ni formularios
    # ---------------------------------------------------------------------
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Disponibilidad</h2>", unsafe_allow_html=True)
    st.write("Bienvenido al calendario general de disponibilidad de nuestras cabañas. Esta sección es puramente informativa.")
    
    # Controles simplificados de fecha para el público
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    col_m_pub, col_a_pub = st.columns(2)
    with col_m_pub:
        mes_sel_pub = st.selectbox("Mes:", meses, index=datetime.now().month - 1, key="pub_mes")
    with col_a_pub:
        anio_sel_pub = st.selectbox("Año:", [2025, 2026, 2027], index=1, key="pub_anio")
        
    mes_num_pub = meses.index(mes_sel_pub) + 1
    ocupacion_pub = obtener_ocupacion_mes(mes_num_pub, anio_sel_pub)
    
    # Dibujar el calendario en la versión pública
    st.markdown(renderizar_calendario_html(anio_sel_pub, mes_num_pub, ocupacion_pub, mes_sel_pub), unsafe_allow_html=True)
    
    # Simbologías informativas explicativas
    st.markdown("""
    <div style="margin-top:20px; padding:15px; background-color:#f9fafb; border-radius:8px; border: 1px solid #e5e7eb;">
        <h4 style="margin-top:0; color:#374151;">ℹ️ Simbología del Calendario</h4>
        <p style="margin: 5px 0;"><span style="display:inline-block; width:20px; height:12px; background-color:#DEF7EC; border:1px solid #31C48D; margin-right:8px;"></span> <b>Fondo Verde / Círculo Verde:</b> Cabaña 1 Ocupada</p>
        <p style="margin: 5px 0;"><span style="display:inline-block; width:20px; height:12px; background-color:#EBF5FF; border:1px solid #3F83F8; margin-right:8px;"></span> <b>Fondo Azul / Círculo Azul:</b> Cabaña 2 Ocupada</p>
        <p style="margin: 5px 0;"><span style="display:inline-block; width:20px; height:12px; background: linear-gradient(135deg, #DEF7EC 50%, #EBF5FF 50%); border:1px solid #9ca3af; margin-right:8px;"></span> <b>Módulo Dividido Dual:</b> Ambas Cabañas Ocupadas el mismo día</p>
        <p style="margin: 5px 0; color:#6b7280; font-size:12px;"><i>*Nota: Este panel está protegido contra modificaciones externas.</i></p>
    </div>
    """, unsafe_allow_html=True)

else:
    # ---------------------------------------------------------------------
    # PANEL ADMINISTRATIVO: Requiere contraseña para proteger la información
    # ---------------------------------------------------------------------
    if not st.session_state.autenticado:
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔐 Acceso al Panel Administrativo</h2>", unsafe_allow_html=True)
        
        with st.form("Formulario de Autenticación"):
            password_input = st.text_input("Ingresa la contraseña de administrador:", type="password")
            submit_auth = st.form_submit_button("Ingresar al Panel")
            
            if submit_auth:
                if password_input == CONTRASEÑA_CORRECTA:
                    st.session_state.autenticado = True
                    st.success("Acceso concedido correctamente.")
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta. Por favor intente nuevamente.")
        st.stop() # Frena la ejecución del resto de la página si no está validado

    # Si pasa el bloqueo de contraseña, se despliega el panel administrativo original refinado
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Control Financiero</h2>", unsafe_allow_html=True)

    # --- PANEL SUPERIOR: CONFIGURACIÓN DE TARIFAS Y FILTROS ---
    st.markdown("### ⚙️ Panel de Control")
    col_mes, col_anio, col_air, col_dir = st.columns(4)

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
