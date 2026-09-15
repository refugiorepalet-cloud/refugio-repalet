import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Configuración panorámica estable de la interfaz
st.set_page_config(page_title="Gestión de Cabañas", layout="wide")

# =========================================================================
# --- CONTROL DE VISTAS (PÚBLICA VS ADMINISTRATIVA) Y SEGURIDAD ---
# =========================================================================

# Detectar si el usuario ingresa mediante el enlace de la versión pública
query_params = st.query_params
es_version_publica = query_params.get("view") == "public"

# Contraseña del panel administrativo
CONTRASEÑA_CORRECTA = "Repalet2026"

# Inicializar estados de autenticación y registros si no existen
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "registros" not in st.session_state:
    st.session_state.registros = []

# Función auxiliar para recolectar la ocupación de las cabañas
def obtener_ocupacion_mes(mes, anio):
    ocupacion = {d: {"Cabaña 1": False, "Cabaña 2": False} for d in range(1, 33)}
    for r in st.session_state.registros:
        if r["estado"] == "Activo":
            curr = r["ingreso"]
            while curr < r["salida"]:
                if curr.month == mes and curr.year == anio:
                    if curr.day in ocupacion:
                        ocupacion[curr.day][r["Cabaña"]] = True
                curr += timedelta(days=1)
    return ocupacion

# Función para estructurar el calendario HTML único solicitado
def renderizar_calendario_html(anio, mes, ocupacion, titulo_mes):
    cal_matriz = calendar.monthcalendar(anio, mes)
    
    # Cabecera con los días abreviados solicitados: Lu-Ma-Mi-Ju-Vi-Sa-Do
    html_tabla = f"""
    <table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif; text-align: center; background-color: #ffffff;">
        <thead>
            <tr style="background-color: #f3f4f6; color: #4b5563; font-weight: bold; border-bottom: 2px solid #e5e7eb;">
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Lu</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Ma</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Mi</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Ju</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Vi</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Sa</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Do</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for semana in cal_matriz:
        html_tabla += "<tr style='height: 65px;'>"
        for dia in semana:
            if dia == 0:
                html_tabla += "<td style='border: 1px solid #e5e7eb; background-color: #fafafa;'></td>"
            else:
                c1 = ocupacion[dia]["Cabaña 1"]
                c2 = ocupacion[dia]["Cabaña 2"]
                
                # División del módulo mediante degradado CSS si coinciden en el día
                if c1 and c2:
                    estilo_fondo = "background: linear-gradient(135deg, #DEF7EC 50%, #EBF5FF 50%);"
                elif c1:
                    estilo_fondo = "background-color: #DEF7EC;" # Cabaña 1 (Verde)
                elif c2:
                    estilo_fondo = "background-color: #EBF5FF;" # Cabaña 2 (Azul)
                else:
                    estilo_fondo = "background-color: #ffffff;"
                
                # Círculos indicadores estéticos
                if c1 and c2:
                    indicadores = '<span style="display:inline-block; width:8px; height:8px; background-color:#31C48D; border-radius:50%; margin:1px;"></span><span style="display:inline-block; width:8px; height:8px; background-color:#3F83F8; border-radius:50%; margin:1px;"></span>'
                elif c1:
                    indicadores = '<span style="display:inline-block; width:10px; height:10px; background-color:#31C48D; border-radius:50%;"></span>'
                elif c2:
                    indicadores = '<span style="display:inline-block; width:10px; height:10px; background-color:#3F83F8; border-radius:50%;"></span>'
                else:
                    indicadores = '<span style="display:inline-block; width:10px; height:10px; background-color:#e5e7eb; border-radius:50%;"></span>'

                # Números de días renderizados en gris suave (#9ca3af)
                html_tabla += f"""
                <td style="border: 1px solid #e5e7eb; {estilo_fondo} vertical-align: middle; padding: 5px;">
                    <div style="font-size: 14px; font-weight: bold; color: #9ca3af; margin-bottom: 2px;">{dia}</div>
                    <div style="display: flex; justify-content: center; align-items: center;">{indicadores}</div>
                </td>
                """
        html_tabla += "</tr>"
        
    html_tabla += """
        </tbody>
    </table>
    """
    return html_tabla


# =========================================================================
# --- MANEJO DE VISTAS (PÚBLICA O PANEL ADMINISTRATIVO) ---
# =========================================================================

if es_version_publica:
    # ---------------------------------------------------------------------
    # VISTA PÚBLICA: Calendario limpio y aislado (Sin opción de edición)
    # ---------------------------------------------------------------------
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Disponibilidad</h2>", unsafe_allow_html=True)
    
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    col_m_pub, col_a_pub = st.columns(2)
    with col_m_pub:
        mes_sel_pub = st.selectbox("Seleccionar Mes:", meses, index=datetime.now().month - 1, key="pub_mes_sel")
    with col_a_pub:
        anio_sel_pub = st.selectbox("Seleccionar Año:", [2025, 2026, 2027], index=1, key="pub_anio_sel")
        
    mes_num_pub = meses.index(mes_sel_pub) + 1
    ocupacion_pub = obtener_ocupacion_mes(mes_num_pub, r := anio_sel_pub)
    
    st.markdown(f"### 📅 Calendario de Disponibilidad - {mes_sel_pub} {anio_sel_pub}")
    st.markdown(renderizar_calendario_html(anio_sel_pub, mes_num_pub, ocupacion_pub, r := mes_sel_pub), unsafe_allow_html=True)
    
    # Reseñas informativas y de simbología solicitadas
    st.markdown("""
    <div style="margin-top:20px; padding:15px; background-color:#f9fafb; border-radius:8px; border: 1px solid #e5e7eb;">
        <h4 style="margin-top:0; color:#374151;">ℹ️ Simbología del Calendario</h4>
        <p style="margin: 5px 0;"><span style="display:inline-block; width:20px; height:12px; background-color:#DEF7EC; border:1px solid #31C48D; margin-right:8px;"></span> <b>Fondo Verde / Círculo Verde:</b> Cabaña 1 Ocupada</p>
        <p style="margin: 5px 0;"><span style="display:inline-block; width:20px; height:12px; background-color:#EBF5FF; border:1px solid #3F83F8; margin-right:8px;"></span> <b>Fondo Azul / Círculo Azul:</b> Cabaña 2 Ocupada</p>
        <p style="margin: 5px 0;"><span style="display:inline-block; width:20px; height:12px; background: linear-gradient(135deg, #DEF7EC 50%, #EBF5FF 50%); border:1px solid #9ca3af; margin-right:8px;"></span> <b>Módulo Dividido Dual:</b> Ambas Cabañas Ocupadas el mismo día</p>
        <p style="margin: 5px 0; color:#6b7280; font-size:12px;"><i>*Nota: Este enlace es de acceso público y de solo lectura. No puede ser editado ni intervenido.</i></p>
    </div>
    """, unsafe_allow_html=True)

else:
    # ---------------------------------------------------------------------
    # PANEL ADMINISTRATIVO: Requiere inicio de sesión
    # ---------------------------------------------------------------------
    if not st.session_state.autenticado:
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔐 Ingreso al Panel Administrativo</h2>", unsafe_allow_html=True)
        with st.form("Login Form"):
            clave_usuario = st.text_input("Contraseña de Acceso:", type="password")
            btn_login = st.form_submit_button("Ingresar")
            if btn_login:
                if clave_usuario == CONTRASEÑA_CORRECTA:
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta. Por favor, reintente.")
        st.stop()

    # Cambio de nombre oficial solicitado
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Control Financiero</h2>", unsafe_allow_html=True)

    # =========================================================================
    # --- PANEL SUPERIOR: CONFIGURACIÓN DE TARIFAS Y FILTROS ---
    # =========================================================================
    st.markdown("### ⚙️ Panel de Control")
    col_mes, col_anio, col_air, col_dir = st.columns(4)

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    meses_dict = {m: i+1 for i, m in enumerate(meses)}

    with col_mes:
        mes_sel = st.selectbox("Seleccionar Mes:", meses, index=datetime.now().month - 1, key="ctrl_mes_select_final")

    with col_anio:
        lista_anios = [2025, 2026, 2027]
        anio_sel = st.selectbox("Seleccionar Año:", lista_anios, index=1, key="ctrl_anio_select_final")

    mes_num = meses_dict[mes_sel]

    # Mantenemos el sistema de candado intacto
    bloquear = st.checkbox("🔒 Bloquear tarifas fijas para evitar errores de digitación", value=True, key="ctrl_lock_check_final")

    with col_air:
        val_airbnb = st.number_input("Tarifa Airbnb por Noche ($):", value=76855, disabled=bloquear, key="ctrl_val_air_final")

