import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Configuración panorámica estable de la interfaz
st.set_page_config(page_title="Gestión de Cabañas", layout="wide")

# =========================================================================
# --- CONFIGURACIÓN DE SEGURIDAD Y FILTRO DE RUTA (PÚBLICA / ADMINISTRATIVA) ---
# =========================================================================
query_params = st.query_params
es_version_publica = query_params.get("view") == "public"
CONTRASEÑA_CORRECTA = "Repalet2026"

# Inicializar almacenamiento local persistente en memoria de sesión
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if "registros" not in st.session_state:
    st.session_state.registros = []

# Título dinámico adaptado según las indicaciones iniciales
if es_version_publica:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Disponibilidad</h2>", unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Control Financiero</h2>", unsafe_allow_html=True)

# Lógica del Login para proteger el Panel Administrativo
if not es_version_publica and not st.session_state.autenticado:
    st.markdown("### 🔐 Ingreso al Panel Administrativo")
    with st.form("form_seguridad_repalet"):
        clave_ingresada = st.text_input("Contraseña de Acceso:", type="password")
        btn_acceder = st.form_submit_button("Ingresar al Panel")
        if btn_acceder:
            if clave_ingresada == CONTRASEÑA_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Por favor reintente.")
    st.stop()

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

# EL CANDADO: Sistema de bloqueo activo por defecto en la barra superior solicitado
bloquear = st.checkbox("🔒 Bloquear tarifas fijas para evitar errores de digitación", value=True, key="ctrl_lock_check_final")

with col_air:
    val_airbnb = st.number_input("Tarifa Airbnb por Noche ($):", value=76855, disabled=bloquear, key="ctrl_val_air_final")

with col_dir:
    val_directo = st.number_input("Tarifa Directo por Noche ($):", value=60000, disabled=bloquear, key="ctrl_val_dir_final")

st.markdown("---")

# =========================================================================
# --- PROCESAMIENTO PREVIO DE RESERVAS (ESTRUCTURA DE DATOS UNIFICADA) ---
# =========================================================================
registros_filtrados = [r for r in st.session_state.registros if r["mes"] == mes_num and r["anio"] == anio_sel]

acum_iva = 0
acum_neto = 0

# Diccionario base mensual mapeado para el control diario de ocupación
ocupacion_calendario = {d: {"Cabaña 1": False, "Cabaña 2": False} for d in range(1, 33)}

# Alimentar matriz de ocupación basándose únicamente en reservas "Activas"
for r in st.session_state.registros:
    if r["estado"] == "Activo":
        curr = r["ingreso"]
        while curr < r["salida"]:
            if curr.month == mes_num and curr.year == anio_sel:
                if curr.day in ocupacion_calendario:
                    ocupacion_calendario[curr.day][r["Cabaña"]] = True
            curr += timedelta(days=1)

# =========================================================================
# --- PANEL INFERIOR: FORMULARIO Y PLANILLA ---
# =========================================================================
col_izq, col_der = st.columns(2)

# SINCRONIZACIÓN AUTOMÁTICA: La fecha base del formulario se amolda al mes superior seleccionado
fecha_base = datetime(anio_sel, mes_num, 1).date()

with col_izq:
    if es_version_publica:
        st.markdown("### 📝 Información del Sistema")
        st.info("Estás visualizando la versión pública en modo de solo lectura. Los formularios de registro y herramientas contables están deshabilitados por protección.")
    else:
        st.markdown("### 📝 Nueva Reserva")
        cliente = st.text_input("Nombre Completo del Huésped:", key="form_cliente_final")
        cabana = st.selectbox("Asignar Cabaña:", ["Cabaña 1", "Cabaña 2"], key="form_cabana_final")
        canal = st.selectbox("Canal de Distribución:", ["Cliente Directo", "Airbnb"], key="form_canal_final")
        
        # Fecha de ingreso y salida sincronizadas automáticamente con el mes superior
        f_ingreso = st.date_input("Fecha de Ingreso:", value=fecha_base, format="DD/MM/YYYY", key="ingreso_sync_final")
        f_salida = st.date_input("Fecha de Salida:", value=fecha_base + timedelta(days=2), format="DD/MM/YYYY", key="salida_sync_final")
        
        if st.button("🚀 Procesar y Registrar Reserva", type="primary", use_container_width=True, key="form_btn_submit_final"):
            noches = (f_salida - f_ingreso).days
            
            if noches < 2:
                st.error("❌ Restricción contable: Se exige un mínimo obligatorio de 2 noches para agendar.")
            elif not cliente:
                st.error("❌ Campos vacíos: Debes ingresar el nombre del cliente.")
            else:
                if canal == "Cliente Directo":
                    bruto_total = val_directo * noches
                    monto_base_iva = bruto_total
                else:
                    bruto_total = val_airbnb * noches
                    monto_base_iva = bruto_total * (1 - 0.155)
                    
                neto_total = monto_base_iva / 1.19
                iva_total = monto_base_iva - neto_total
                id_unico = int(datetime.now().timestamp() * 1000)
                
                st.session_state.registros.append({
                    "id": id_unico,
                    "Cliente": cliente, "Cabaña": cabana, "Canal": canal, "Noches": noches,
                    "Ing. Bruto": bruto_total, "Base IVA": monto_base_iva, "IVA 19%": iva_total, "Neto Real": neto_total,
                    "ingreso": f_ingreso, "salida": f_salida,
                    "mes": f_ingreso.month, "anio": f_ingreso.year,
                    "estado": "Activo"
                })
                st.success(f"✔️ Registro de {cliente} completado.")
                st.rerun()

with col_der:
    st.markdown("### 📊 Planilla Mensual de Movimientos")
    
    if registros_filtrados and not es_version_publica:
        tabla_datos = []
        for r in registros_filtrados:
            check_in_str = r["ingreso"].strftime("%d/%m/%Y")
            check_out_str = r["salida"].strftime("%d/%m/%Y")
            
            if r["estado"] == "Anulado":
                marca_estado = "❌ (ANULADO) "
                row_cliente = f"~~{r['Cliente']}~~"
                v_bruto, v_base, v_iva, v_neto = 0, 0, 0, 0
            else:
                marca_estado = "🟢 " if r["Cabaña"] == "Cabaña 1" else "🔵 "
                row_cliente = r["Cliente"]
                v_bruto, v_base, v_iva, v_neto = r["Ing. Bruto"], r["Base IVA"], r["IVA 19%"], r["Neto Real"]
                
                acum_iva += v_iva
                acum_neto += v_neto
            
            tabla_datos.append({
                "ID Interno": r["id"],
                "Huésped": row_cliente,
                "Alojamiento": marca_estado + r["Cabaña"],
                "Canal": r["Canal"],
                "Noches": r["Noches"],
                "Ingreso": check_in_str,
                "Salida": check_out_str,
                "Bruto ($)": f"${v_bruto:,.0f}" if r["estado"] == "Activo" else "$0",
                "Base IVA ($)": f"${v_base:,.0f}" if r["estado"] == "Activo" else "$0",
                "IVA 19% ($)": f"${v_iva:,.0f}" if r["estado"] == "Activo" else "$0",
                "Neto ($)": f"${v_neto:,.0f}" if r["estado"] == "Activo" else "$0"
            })
            
        df = pd.DataFrame(tabla_datos)
        st.dataframe(df, use_container_width=True, hide_index=True, key="planilla_data_view_final")
        
        # --- SECCIÓN GESTIÓN CONTABLE (ANULAR / ELIMINAR PERMANENTE) ---
        st.markdown("#### ⚙️ Gestión de Estado Contable")
        opciones_id = [f"{r['id']} | {r['Cliente']} ({r['Cabaña']})" for r in registros_filtrados]
        id_seleccionado = st.selectbox("Seleccionar Reserva para Modificar:", opciones_id, key="mgmt_select_reserva_final")
        
        if id_seleccionado:
            id_real = int(id_seleccionado.split(" | ")[0])
            reserva_objeto = next(r for r in st.session_state.registros if r["id"] == id_real)
            
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("❌ Anular Reserva", use_container_width=True, key="btn_anular_final"):
                    reserva_objeto["estado"] = "Anulado"
                    st.rerun()
            with col_b2:
                if st.button("🔄 Reactivar Reserva", use_container_width=True, key="btn_reactivar_final"):
                    reserva_objeto["estado"] = "Activo"
                    st.rerun()
            with col_b3:
                if st.button("🗑️ Eliminar Permanente", use_container_width=True, type="secondary", key="btn_delete_final"):
