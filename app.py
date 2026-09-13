import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

# Configuración de página
st.set_page_config(page_title="Refugio Repalet - Gestión y Reservas", page_icon="🏡", layout="wide")

# ---------------------------------------------------------
# CONFIGURACIÓN Y SEGURIDAD
# ---------------------------------------------------------
# Reemplaza 'repalet2026' por la contraseña que tú desees usar
ADMIN_PASSWORD = "crog@6375" 

# Verificar parámetro de URL
query_params = st.query_params
modo_publico = (query_params.get("view") == "public") or (query_params.get("modo") == "publico")

# ---------------------------------------------------------
# BASE DE DATOS EN MEMORIA / SESIÓN
# ---------------------------------------------------------
if "reservas" not in st.session_state:
    st.session_state.reservas = []

# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
def obtener_fechas_ocupadas():
    fechas = set()
    for r in st.session_state.reservas:
        inicio = r["checkin"]
        fin = r["checkout"]
        curr = inicio
        while curr < fin:
            fechas.add(curr)
            curr += timedelta(days=1)
    return fechas

def generar_calendario(año, mes):
    import calendar
    cal = calendar.monthcalendar(año, mes)
    fechas_ocupadas = obtener_fechas_ocupadas()
    
    nombres_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    st.markdown(f"### 📅 {nombres_meses[mes - 1]} {año}")
    
    # Encabezado días de la semana
    cols = st.columns(7)
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    for i, d in enumerate(dias):
        cols[i].markdown(f"**{d}**")
        
    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            if dia == 0:
                cols[i].write("")
            else:
                fecha_actual = date(año, mes, dia)
                if fecha_actual in fechas_ocupadas:
                    cols[i].markdown(f"🔴 **{dia}** *(Ocupado)*")
                else:
                    cols[i].markdown(f"🟢 **{dia}** *(Disponible)*")

# ---------------------------------------------------------
# VISTA PÚBLICA (CLIENTES)
# ---------------------------------------------------------
if modo_publico:
    st.title("🏡 Refugio Repalet - Disponibilidad")
    st.markdown("Consulta la disponibilidad de nuestras cabañas en tiempo real:")
    
    hoy = date.today()
    mes_opciones = []
    for i in range(4):
        m = (hoy.month - 1 + i) % 12 + 1
        y = hoy.year + ((hoy.month - 1 + i) // 12)
        mes_opciones.append((y, m))
        
    nombres_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                     "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    opcion_sel = st.selectbox(
        "Selecciona el mes a consultar:",
        options=range(len(mes_opciones)),
        format_func=lambda idx: f"{nombres_meses[mes_opciones[idx][1]-1]} {mes_opciones[idx][0]}"
    )
    
    año_sel, mes_sel = mes_opciones[opcion_sel]
    st.write("---")
    generar_calendario(año_sel, mes_sel)
    st.write("---")
    
    # Botón WhatsApp
    msg_wa = f"Hola! Quisiera consultar disponibilidad para Refugio Repalet en el mes de {nombres_meses[mes_sel-1]} {año_sel}."
    url_wa = f"https://wa.me/56912345678?text={msg_wa.replace(' ', '%20')}" # Cambia por tu teléfono real
    st.markdown(f'<a href="{url_wa}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:10px 20px; font-size:16px; border-radius:5px; cursor:pointer;">📲 Consultar Reserva por WhatsApp</button></a>', unsafe_allow_html=True)

# ---------------------------------------------------------
# VISTA PRIVADA (ADMINISTRACIÓN CON CONTRASEÑA)
# ---------------------------------------------------------
else:
    # Verificación de contraseña
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.title("🔒 Acceso Restringido - Refugio Repalet")
        clave_ingresada = st.text_input("Ingresa la contraseña de administrador:", type="password")
        
        if st.button("Ingresar"):
            if clave_ingresada == ADMIN_PASSWORD:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Acceso denegado.")
    else:
        # Panel de administración completo
        st.sidebar.title("Menú Administrador")
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.autenticado = False
            st.rerun()
            
        st.title("📊 Panel de Control y Administración - Refugio Repalet")
        
        tab1, tab2, tab3 = st.tabs(["📝 Nueva Reserva", "📈 Finanzas e Impuestos", "📅 Calendario Interno"])
        
        with tab1:
            st.header("Ingresar Nueva Reserva")
            with st.form("form_reserva"):
                cliente = st.text_input("Nombre del Huésped")
                col1, col2 = st.columns(2)
                checkin = col1.date_input("Fecha Check-in", value=date.today())
                checkout = col2.date_input("Fecha Check-out", value=date.today() + timedelta(days=1))
                monto = st.number_input("Monto Total ($)", min_value=0, step=5000)
                plataforma = st.selectbox("Plataforma de Origen", ["Directo", "Airbnb", "Booking"])
                
                submitted = st.form_submit_button("Guardar Reserva")
                if submitted:
                    st.session_state.reservas.append({
                        "cliente": cliente,
                        "checkin": checkin,
                        "checkout": checkout,
                        "monto": monto,
                        "plataforma": plataforma
                    })
                    st.success(f"Reserva de {cliente} guardada con éxito.")

        with tab2:
            st.header("Resumen Financiero")
            if st.session_state.reservas:
                df = pd.DataFrame(st.session_state.reservas)
                st.dataframe(df)
                total_ingresos = df["monto"].sum()
                st.metric("Ingresos Totales", f"${total_ingresos:,.0f}")
            else:
                st.info("No hay reservas registradas aún.")

        with tab3:
            st.header("Calendario Interno")
            hoy = date.today()
            generar_calendario(hoy.year, hoy.month)
