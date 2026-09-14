import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Configuración panorámica estable de la interfaz
st.set_page_config(page_title="Gestión de Cabañas", layout="wide")

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Control Financiero Local</h2>", unsafe_allow_html=True)

# Inicializar base de datos local persistente en memoria de sesión
if "registros" not in st.session_state:
    st.session_state.registros = []

# =========================================================================
# --- PANEL SUPERIOR: CONFIGURACIÓN DE TARIFAS Y PANEL DE CONTROL ---
# =========================================================================
st.markdown("### ⚙️ Panel de Control")
col_mes, col_anio, col_air, col_dir = st.columns(4)

# Lista de meses corregida con "Mayo" en su forma correcta
meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
meses_dict = {m: i+1 for i, m in enumerate(meses)}

with col_mes:
    mes_sel = st.selectbox("Seleccionar Mes:", meses, index=datetime.now().month - 1, key="ctrl_mes_select_final")

with col_anio:
    lista_anios = [2025, 2026, 2027]
    anio_sel = st.selectbox("Seleccionar Año:", lista_anios, index=1, key="ctrl_anio_select_final")

mes_num = meses_dict[mes_sel]
bloquear = st.checkbox("🔒 Bloquear tarifas fijas para evitar errores de digitación", value=True, key="ctrl_lock_check_final")

with col_air:
    val_airbnb = st.number_input("Tarifa Airbnb por Noche ($):", value=76855, disabled=bloquear, key="ctrl_val_air_final")

with col_dir:
    val_directo = st.number_input("Tarifa Directo por Noche ($):", value=60000, disabled=bloquear, key="ctrl_val_dir_final")

st.markdown("---")

# =========================================================================
# --- PANEL INFERIOR: FORMULARIO Y PLANILLA ---
# =========================================================================
col_izq, col_der = st.columns(2)

fecha_base = datetime(anio_sel, mes_num, 1).date()

with col_izq:
    st.markdown("### 📝 Nueva Reserva")
    cliente = st.text_input("Nombre Completo del Huésped:", key="form_cliente_final")
    cabana = st.selectbox("Asignar Cabaña:", ["Cabaña 1", "Cabaña 2"], key="form_cabana_final")
    canal = st.selectbox("Canal de Distribución:", ["Cliente Directo", "Airbnb"], key="form_canal_final")
    
    # Formato día/mes/año (DD/MM/YYYY)
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
    
    registros_filtrados = [r for r in st.session_state.registros if r["mes"] == mes_num and r["anio"] == anio_sel]
    
    acum_iva = 0
    acum_neto = 0
    
    ocupacion_calendario = {d: {"Cabaña 1": False, "Cabaña 2": False} for d in range(1, 33)}
    
    if registros_filtrados:
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
                
                curr = r["ingreso"]
                while curr < r["salida"]:
                    if curr.month == mes_num and curr.year == anio_sel:
                        ocupacion_calendario[curr.day][r["Cabaña"]] = True
                    curr += timedelta(days=1)
            
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
            
            acum_iva += v_iva
            acum_neto += v_neto
            
        df = pd.DataFrame(tabla_datos)
        st.dataframe(df, use_container_width=True, hide_index=True, key="planilla_data_view_final")
        
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
                    st.toast(f"Reserva de {reserva_objeto['Cliente']} anulada.")
                    st.rerun()
            with col_b2:
                if st.button("🔄 Reactivar Reserva", use_container_width=True, key="btn_reactivar_final"):
                    reserva_objeto["estado"] = "Activo"
                    st.toast(f"Reserva de {reserva_objeto['Cliente']} reactivada.")
                    st.rerun()
            with col_b3:
                if st.button("🗑️ Eliminar Permanente", use_container_width=True, type="secondary", key="btn_delete_final"):
                    st.session_state.registros = [r for r in st.session_state.registros if r["id"] != id_real]
                    st.toast("Reserva eliminada de la memoria.")
                    st.rerun()
    else:
        st.info("Sin registros contables indexados en el periodo seleccionado.")
        
    st.markdown("#### 💰 Balances Consolidados del Periodo")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total IVA Mensual a Declarar:", f"${acum_iva:,.0f}")
    with col_m2:
        st.metric("Total Ganancia Neta Real (Caja):", f"${acum_neto:,.0f}")

    # =========================================================================
    # --- SECCIÓN CALENDARIO EN TABLA HTML ÚNICA ---
    # =========================================================================
    st.markdown(f"### 📅 Calendario - {mes_sel} {anio_sel}")
    
    cal_matriz = calendar.monthcalendar(anio_sel, mes_num)
    
    html_tabla = """
    <table style="width:100%; border-collapse: collapse; font-family: Arial, sans-serif; text-align: center; background-color: #ffffff;">
        <thead>
            <tr style="background-color: #f3f4f6; color: #4b5563; font-weight: bold; border-bottom: 2px solid #e5e7eb;">
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Lun</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Mar</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Mié</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Jue</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Vie</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Sáb</th>
                <th style="padding: 10px; border: 1px solid #e5e7eb; width: 14.28%;">Dom</th>
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
                c1 = ocupacion_calendario[dia]["Cabaña 1"]
