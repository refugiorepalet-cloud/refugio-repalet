import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

# Configuración panorámica estable de la interfaz
st.set_page_config(page_title="Gestión de Cabañas", layout="wide")

st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Control Financiero Local</h2>", unsafe_allow_html=True)

# Inicializar base de datos local persistente en sesión
if "registros" not in st.session_state:
    st.session_state.registros = []

# =========================================================================
# --- PANEL SUPERIOR: CONFIGURACIÓN DE TARIFAS Y FILTROS ---
# =========================================================================
st.markdown("### ⚙️ Panel de Control Mensual")
col_mes, col_anio, col_air, col_dir = st.columns(4)

meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
meses_dict = {m: i+1 for i, m in enumerate(meses)}

with col_mes:
    mes_sel = st.selectbox("Seleccionar Mes:", meses, index=datetime.now().month - 1)

with col_anio:
    # CORREGIDO EL ERROR LÓGICO: Lista de años explícita y completa
    lista_anios = [2025, 2026, 2027]
    anio_sel = st.selectbox("Seleccionar Año:", lista_anios, index=1)

mes_num = meses_dict[mes_sel]
bloquear = st.checkbox("🔒 Bloquear tarifas fijas para evitar errores de digitación", value=True)

with col_air:
    val_airbnb = st.number_input("Tarifa Airbnb por Noche ($):", value=76855, disabled=bloquear)

with col_dir:
    val_directo = st.number_input("Tarifa Directo por Noche ($):", value=60000, disabled=bloquear)

st.markdown("---")

# =========================================================================
# --- PANEL INFERIOR: FORMULARIO Y PLANILLA ---
# =========================================================================
col_izq, col_der = st.columns(2)

fecha_base = datetime(anio_sel, mes_num, 1).date()

with col_izq:
    st.markdown("### 📝 Nueva Reserva")
    cliente = st.text_input("Nombre Completo del Huésped:")
    cabana = st.selectbox("Asignar Cabaña:", ["Cabaña 1", "Cabaña 2"])
    canal = st.selectbox("Canal de Distribución:", ["Cliente Directo", "Airbnb"])
    
    f_ingreso = st.date_input("Fecha de Ingreso:", value=fecha_base, format="DD/MM/YYYY", key="ingreso_sync")
    f_salida = st.date_input("Fecha de Salida:", value=fecha_base + timedelta(days=2), format="DD/MM/YYYY", key="salida_sync")
    
    if st.button("🚀 Procesar y Registrar Reserva", type="primary", use_container_width=True):
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
            
            st.session_state.registros.append({
                "id": len(st.session_state.registros),
                "Cliente": cliente, "Cabaña": cabana, "Canal": canal, "Noches": noches,
                "Ing. Bruto": bruto_total, "Base IVA": monto_base_iva, "IVA 19%": iva_total, "Neto Real": neto_total,
                "ingreso": f_ingreso, "salida": f_salida,
                "mes": f_ingreso.month, "anio": f_ingreso.year,
                "estado": "Activo"
            })
            st.success(f"✔️ Registro de {cliente} completado.")

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
                "ID": r["id"],
                "Huésped": row_cliente,
                "Alojamiento": marca_estado + r["Cabaña"],
                "Canal": r["Canal"],
                "Noches": r["Noches"],
                "Ingreso": check_in_str,
                "Salida": check_out_str,
                "Bruto ($)": f"${v_bruto:,.0f}" if r["estado"] == "Activo" else "$0 (Anulado)",
                "Base IVA ($)": f"${v_base:,.0f}" if r["estado"] == "Activo" else "$0",
                "IVA 19% ($)": f"${v_iva:,.0f}" if r["estado"] == "Activo" else "$0",
                "Neto ($)": f"${v_neto:,.0f}" if r["estado"] == "Activo" else "$0"
            })
            
            acum_iva += v_iva
            acum_neto += v_neto
            
        df = pd.DataFrame(tabla_datos)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("#### ⚙️ Gestión de Estado Contable")
        opciones_id = [f"ID {r['id']} - {r['Cliente']} ({r['Cabaña']})" for r in registros_filtrados]
        id_seleccionado = st.selectbox("Seleccionar Reserva para Modificar Estado:", opciones_id)
        
        if id_seleccionado:
            id_real = int(id_seleccionado.split(" "))
            reserva_objeto = next(r for r in st.session_state.registros if r["id"] == id_real)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("❌ Anular Reserva Seleccionada", use_container_width=True):
                    reserva_objeto["estado"] = "Anulado"
                    st.rerun()
            with col_b2:
                if st.button("🔄 Reactivar Reserva Seleccionada", use_container_width=True):
                    reserva_objeto["estado"] = "Activo"
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
                c2 = ocupacion_calendario[dia]["Cabaña 2"]
                
                if c1 and c2:
                    celda_style = "border: 2px solid #eab308; background-color: #fef08a; font-weight: bold; color: #374151;"
                    esferas_html = "🟢 🔵"
                elif c1:
                    celda_style = "border: 1px solid #2e7d32; background-color: #e2f0d9; font-weight: bold; color: #1b5e20;"
                    esferas_html = "🟢"
                elif c2:
                    celda_style = "border: 1px solid #1565c0; background-color: #ddebf7; font-weight: bold; color: #0d47a1;"
                    esferas_html = "🔵"
                else:
                    celda_style = "border: 1px solid #e5e7eb; background-color: #ffffff; color: #9CA3AF;"
                    esferas_html = "<span style='color: transparent;'>⚪</span>"
                
