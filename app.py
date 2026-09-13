import calendar
from datetime import datetime, timedelta
import json
import os
import urllib.parse
import pandas as pd
import streamlit as st

# Configuración panorámica de la interfaz
st.set_page_config(
    page_title="Gestión de Cabañas Refugio Repalet",
    page_icon="🏡",
    layout="wide"
)

ADMIN_PASSWORD = "cabañas@6375"

st.markdown(
    """
    <style>
        div[data-baseweb="select"], div[role="listbox"], ul[role="listbox"] {
            translate: no !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

ARCHIVO_DATOS = "reservas.json"

# =========================================================================
# 📱 INGRESA AQUÍ TU NÚMERO DE WHATSAPP (Código de país + 9 dígitos)
# =========================================================================
NUMERO_WHATSAPP = "56982067917" 

CABANA_1 = "Cabaña Colibrí"
CABANA_2 = "Cabaña Chercán"

NOMBRES_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo\u200b", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

def cargar_datos():
    if os.path.exists(ARCHIVO_DATOS):
        try:
            with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
                datos = json.load(f)
                for r in datos:
                    if r.get("Cabaña") in ["Cabaña 1", "Colibrí"]:
                        r["Cabaña"] = CABANA_1
                    elif r.get("Cabaña") in ["Cabaña 2", "Chercán"]:
                        r["Cabaña"] = CABANA_2
                    r["ingreso"] = datetime.strptime(r["ingreso"], "%Y-%m-%d").date()
                    r["salida"] = datetime.strptime(r["salida"], "%Y-%m-%d").date()
                return datos
        except Exception as e:
            st.error(f"Error al cargar los datos guardados: {e}")
            return []
    return []

def guardar_datos():
    try:
        registros_para_guardar = []
        for r in st.session_state.registros:
            r_copy = r.copy()
            r_copy["ingreso"] = r_copy["ingreso"].strftime("%Y-%m-%d")
            r_copy["salida"] = r_copy["salida"].strftime("%Y-%m-%d")
            registros_para_guardar.append(r_copy)
        with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
            json.dump(registros_para_guardar, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Error al guardar los datos: {e}")

if "registros" not in st.session_state:
    st.session_state.registros = cargar_datos()

query_params = st.query_params
modo_publico = query_params.get("view") == "public" or query_params.get("modo") == "publico"

# =========================================================================
# --- VISTA PÚBLICA (FONDO TOTAL DE LA PÁGINA 10% NEGRO / GRIS CLARO) ---
# =========================================================================
if modo_publico:
    # Fuerza el esquema de color claro y asigna el fondo gris de 10% negro (#E6E6E6)
    st.markdown(
        """
        <style>
            :root {
                color-scheme: light !important;
            }
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
                background-color: #E6E6E6 !important;
                color: #111827 !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "<h1 style='text-align: center; color: #111827; font-weight: 700;'>🏡 Refugio Repalet - Disponibilidad y Reservas</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #374151; font-size: 1.05rem;'>Consulta la disponibilidad en tiempo real para nuestras cabañas a continuación.</p>",
        unsafe_allow_html=True,
    )

    hoy = datetime.now()
    opciones_meses_pub = []
    
    for offset in range(0, 4):
        mes_calculado = (hoy.month - 1 + offset) % 12 + 1
        anio_calculado = hoy.year + ((hoy.month - 1 + offset) // 12)
        nombre_m = NOMBRES_MESES[mes_calculado - 1].strip()
        etiqueta = f"{nombre_m} {anio_calculado}"
        opciones_meses_pub.append({
            "label": etiqueta,
            "mes_num": mes_calculado,
            "anio_num": anio_calculado
        })

    _, col_sel_pub, _ = st.columns([1, 2, 1])
    with col_sel_pub:
        opcion_seleccionada = st.selectbox(
            label="Seleccionar Mes:",
            options=opciones_meses_pub,
            format_func=lambda x: x["label"],
            index=0,
            key="pub_mes_dinamico_select"
        )

    mes_num = opcion_seleccionada["mes_num"]
    anio_sel = opcion_seleccionada["anio_num"]
    mes_sel = NOMBRES_MESES[mes_num - 1].strip()

    dias_en_mes = calendar.monthrange(anio_sel, mes_num)[1]
    ocupacion_calendario = {d: {CABANA_1: False, CABANA_2: False} for d in range(1, dias_en_mes + 1)}

    for r in st.session_state.registros:
        if r["estado"] == "Activo":
            curr = r["ingreso"]
            while curr < r["salida"]:
                if curr.month == mes_num and curr.year == anio_sel and curr.day in ocupacion_calendario:
                    cab_nombre = r["Cabaña"]
                    if cab_nombre in ocupacion_calendario[curr.day]:
                        ocupacion_calendario[curr.day][cab_nombre] = True
                curr += timedelta(days=1)

    st.markdown("<hr style='border: none; border-top: 1px solid #9CA3AF; margin: 20px 0;'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color: #111827;'>📅 Disponibilidad - {mes_sel} {anio_sel}</h3>", unsafe_allow_html=True)

    # Leyenda pública
    st.markdown(
        f"""
        <div class="notranslate" translate="no" style="display: flex; gap: 18px; font-size: 0.9rem; margin-bottom: 15px; color: #1F2937; font-weight: 600;">
            <div style="display: flex; align-items: center; gap: 6px;"><span style="background-color:#FFFFFF;width:14px;height:14px;display:inline-block;border-radius:3px;border:1px solid #9CA3AF;"></span> Disponible</div>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="background-color:#728C11;width:14px;height:14px;display:inline-block;border-radius:3px;"></span> {CABANA_1}</div>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="background-color:#3D9DD9;width:14px;height:14px;display:inline-block;border-radius:3px;"></span> {CABANA_2}</div>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="background:linear-gradient(135deg,#728C11 50%,#3D9DD9 50%);width:14px;height:14px;display:inline-block;border-radius:3px;"></span> Ambas Ocupadas</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Estilos CSS del Calendario Público
    cal_html = """
    <style>
        .grid-cal { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; background: #FFFFFF; padding: 12px; border-radius: 8px; border: 1px solid #9CA3AF; }
        .h-dia { text-align: center; font-weight: bold; background: #F1F5F9; color: #1E293B; padding: 10px; border-radius: 6px; font-size: 0.9rem; border: 1px solid #CBD5E1; }
        .c-dia { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: bold; font-size: 1.05rem; border: 1px solid #E5E7EB; }
        .disp { background: #FFFFFF; color: #111827; }                      /* Blanco con número oscuro */
        .cb1 { background: #728C11; color: #FFFFFF; border-color: #728C11; } /* Verde Colibrí */
        .cb2 { background: #3D9DD9; color: #FFFFFF; border-color: #3D9DD9; } /* Azul Chercán */
        .amb { background: linear-gradient(135deg, #728C11 50%, #3D9DD9 50%); color: #FFFFFF; border-color: #CBD5E1; text-shadow: 0px 0px 3px rgba(0,0,0,0.6); }
    </style>
    <div class="grid-cal notranslate" translate="no">
        <div class="h-dia">Lu</div><div class="h-dia">Ma</div><div class="h-dia">Mi</div>
        <div class="h-dia">Ju</div><div class="h-dia">Vi</div><div class="h-dia">Sá</div><div class="h-dia">Do</div>
    """

    primer_dia_sem, _ = calendar.monthrange(anio_sel, mes_num)
    for _ in range(primer_dia_sem):
        cal_html += '<div class="c-dia" style="border:none; background:transparent;"></div>'

    for d in range(1, dias_en_mes + 1):
        c1, c2 = ocupacion_calendario[d][CABANA_1], ocupacion_calendario[d][CABANA_2]
        cls = "amb" if c1 and c2 else ("cb1" if c1 else ("cb2" if c2 else "disp"))
        cal_html += f'<div class="c-dia {cls}">{d}</div>'

    cal_html += "</div>"
    st.markdown(cal_html, unsafe_allow_html=True)

    msg_ws = urllib.parse.quote(f"Hola! Me gustaría consultar disponibilidad en Refugio Repalet para {mes_sel} {anio_sel}.")
    link_whatsapp = f"https://wa.me/{NUMERO_WHATSAPP}?text={msg_ws}"

    st.markdown("<br>", unsafe_allow_html=True)
    _, col_btn_center, _ = st.columns([1, 2, 1])
    with col_btn_center:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
                    <button style="background-color: #F2D231; color: #000000; border: none; padding: 14px 24px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; font-size: 1.05rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.2s;">
                        📲 Consultar Reserva por WhatsApp
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.stop()

# =========================================================================
# --- PROTECCIÓN ADMIN ---
# =========================================================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔒 Acceso Restringido - Refugio Repalet</h2>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        clave_ingresada = st.text_input("Ingresa la contraseña de administrador:", type="password", key="pwd_login")
        if st.button("🔓 Entrar al Panel", type="primary", use_container_width=True, key="btn_login"):
            if clave_ingresada == ADMIN_PASSWORD:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta. Acceso denegado.")
    st.stop()

# =========================================================================
# --- PANEL PRIVADO ---
# =========================================================================
st.sidebar.title("Menú Administrador")
if st.sidebar.button("🔒 Cerrar Sesión", key="btn_logout"):
    st.session_state.autenticado = False
    st.rerun()

st.markdown(
    "<h2 style='text-align: center; color: #1E3A8A;'>🏡 Refugio Repalet - Control Financiero</h2>",
    unsafe_allow_html=True,
)

st.markdown("### ⚙️ Panel de Control")

col_mes, col_anio, col_air, col_dir = st.columns(4)

meses = NOMBRES_MESES
meses_dict = {m.strip(): i + 1 for i, m in enumerate(meses)}

with col_mes:
    mes_sel_raw = st.selectbox(
        "Seleccionar Mes:",
        options=meses,
        index=datetime.now().month - 1,
        key="ctrl_mes_select_final",
    )
    mes_sel = mes_sel_raw.strip()

with col_anio:
    lista_anios = [2025, 2026, 2027, 2028]
    anio_sel = st.selectbox(
        "Seleccionar Año:", lista_anios, index=1, key="ctrl_anio_select_final"
    )

mes_num = meses_dict[mes_sel]
bloquear = st.checkbox(
    "🔒 Bloquear tarifas fijas para evitar errores de digitación",
    value=True,
    key="ctrl_lock_check_final",
)

with col_air:
    val_airbnb = st.number_input("Tarifa Airbnb por Noche ($):", value=76855, disabled=bloquear, key="ctrl_val_air_final")

with col_dir:
    val_directo = st.number_input("Tarifa Directo por Noche ($):", value=60000, disabled=bloquear, key="ctrl_val_dir_final")

st.markdown("---")

col_izq, col_der = st.columns(2)
fecha_base = datetime(anio_sel, mes_num, 1).date()

with col_izq:
    st.markdown("### 📝 Nueva Reserva")
    cliente = st.text_input("Nombre Completo del Huésped:", key="form_cliente_final")
    cabana = st.selectbox("Asignar Cabaña:", [CABANA_1, CABANA_2], key="form_cabana_final")
    canal = st.selectbox("Canal de Distribución:", ["Cliente Directo", "Airbnb"], key="form_canal_final")

    f_ingreso = st.date_input("Fecha de Ingreso:", value=fecha_base, format="DD/MM/YYYY", key="ingreso_sync_final")
    f_salida = st.date_input("Fecha de Salida:", value=fecha_base + timedelta(days=2), format="DD/MM/YYYY", key="salida_sync_final")

    if st.button("🚀 Procesar y Registrar Reserva", type="primary", use_container_width=True, key="form_btn_submit_final"):
        noches = (f_salida - f_ingreso).days
        
        conflicto_detectado = False
        reserva_conflicto_info = ""
        
        for r in st.session_state.registros:
            if r["estado"] == "Activo" and r["Cabaña"] == cabana:
                if max(f_ingreso, r["ingreso"]) < min(f_salida, r["salida"]):
                    conflicto_detectado = True
                    reserva_conflicto_info = f"Reservada por {r['Cliente']} ({r['ingreso'].strftime('%d/%m/%Y')} al {r['salida'].strftime('%d/%m/%Y')})"
                    break

        if noches < 2:
            st.error("❌ Restricción contable: Se exige un mínimo obligatorio de 2 noches para agendar.")
        elif not cliente:
            st.error("❌ Campos vacíos: Debes ingresar el nombre del cliente.")
        elif conflicto_detectado:
            st.error(f"⚠️ **Conflicto de Ocupación:** La {cabana} ya cuenta con una reserva activa en esas fechas. ({reserva_conflicto_info})")
        else:
            if canal == "Cliente Directo":
                bruto_total = val_directo * noches
                comision_airbnb = 0
                monto_base_iva = bruto_total
            else:
                bruto_total = val_airbnb * noches
                comision_airbnb = bruto_total * 0.155
                monto_base_iva = bruto_total * (1 - 0.155)

            neto_total = monto_base_iva / 1.19
            iva_total = monto_base_iva - neto_total
            id_unico = int(datetime.now().timestamp() * 1000)

            st.session_state.registros.append({
                "id": id_unico, "Cliente": cliente, "Cabaña": cabana, "Canal": canal,
                "Noches": noches, "Ing. Bruto": bruto_total, "Comision Airbnb": comision_airbnb,
                "Base IVA": monto_base_iva, "IVA 19%": iva_total, "Neto Real": neto_total, 
                "ingreso": f_ingreso, "salida": f_salida, "mes": f_ingreso.month, 
                "anio": f_ingreso.year, "estado": "Activo"
            })

            guardar_datos()
            st.success(f"✔️ Registro de {cliente} completado y guardado en disco.")
            st.rerun()

with col_der:
    col_tit, col_exp = st.columns([2, 1])
    with col_tit:
        st.markdown("### 📊 Planilla Mensual de Movimientos")

    registros_filtrados = [
        r for r in st.session_state.registros 
        if r["mes"] == mes_num and r["anio"] == anio_sel
    ]

    dias_en_mes = calendar.monthrange(anio_sel, mes_num)[1]
    ocupacion_calendario = {d: {CABANA_1: False, CABANA_2: False} for d in range(1, dias_en_mes + 1)}

    for r in st.session_state.registros:
        if r["estado"] == "Activo":
            curr = r["ingreso"]
            while curr < r["salida"]:
                if curr.month == mes_num and curr.year == anio_sel and curr.day in ocupacion_calendario:
                    cab_nombre = r["Cabaña"]
                    if cab_nombre in ocupacion_calendario[curr.day]:
                        ocupacion_calendario[curr.day][cab_nombre] = True
                curr += timedelta(days=1)

    if registros_filtrados:
        tabla_datos = []
        mapa_opciones = {}
        tot_noches, tot_bruto, tot_comision, tot_base, tot_iva, tot_liquido = 0, 0, 0, 0, 0, 0

        for idx, r in enumerate(registros_filtrados, start=1):
            check_in_str = r["ingreso"].strftime("%d/%m/%Y")
            check_out_str = r["salida"].strftime("%d/%m/%Y")

            label_opcion = f"ID #{idx} | {r['Cliente']} ({r['Cabaña']})"
            mapa_opciones[label_opcion] = r

            if r["estado"] == "Anulado":
                marca_estado = "❌ (ANULADO) "
                row_cliente = f"~~{r['Cliente']}~~"
                v_bruto, v_comision, v_base, v_iva, v_neto = 0, 0, 0, 0, 0
            else:
                marca_estado = "🟢 " if r["Cabaña"] == CABANA_1 else "🔵 "
                row_cliente = r["Cliente"]
                v_bruto = r["Ing. Bruto"]
                v_comision = r.get("Comision Airbnb", r["Ing. Bruto"] * 0.155 if r["Canal"] == "Airbnb" else 0)
                v_base = r["Base IVA"]
                v_iva = r["IVA 19%"]
                v_neto = r["Neto Real"]

                tot_noches += r["Noches"]
                tot_bruto += v_bruto
                tot_comision += v_comision
                tot_base += v_base
                tot_iva += v_iva
                tot_liquido += v_neto

            tabla_datos.append({
                "ID": str(idx),
                "Huésped": row_cliente,
                "Alojamiento": marca_estado + r["Cabaña"],
                "Canal": r["Canal"],
                "Noches": r["Noches"],
                "Ingreso": check_in_str,
                "Salida": check_out_str,
                "Bruto ($)": f"${v_bruto:,.0f}" if r["estado"] == "Activo" else "$0",
                "Comisión Airbnb ($)": f"${v_comision:,.0f}" if r["estado"] == "Activo" else "$0",
                "Monto Imponible ($)": f"${v_base:,.0f}" if r["estado"] == "Activo" else "$0",
                "IVA 19% ($)": f"${v_iva:,.0f}" if r["estado"] == "Activo" else "$0",
                "Valor Líquido ($)": f"${v_neto:,.0f}" if r["estado"] == "Activo" else "$0",
            })

        tabla_datos.append({
            "ID": "TOTAL",
            "Huésped": "---",
            "Alojamiento": "---",
            "Canal": "---",
            "Noches": tot_noches,
            "Ingreso": "---",
            "Salida": "---",
            "Bruto ($)": f"${tot_bruto:,.0f}",
            "Comisión Airbnb ($)": f"${tot_comision:,.0f}",
            "Monto Imponible ($)": f"${tot_base:,.0f}",
            "IVA 19% ($)": f"${tot_iva:,.0f}",
            "Valor Líquido ($)": f"${tot_liquido:,.0f}",
        })

        df = pd.DataFrame(tabla_datos)
        csv_data = df.to_csv(index=False).encode("utf-8-sig")

        with col_exp:
            st.download_button(
                label="📥 Descargar CSV/Excel",
                data=csv_data,
                file_name=f"Planilla_Movimientos_{mes_sel}_{anio_sel}.csv",
                mime="text/csv",
                use_container_width=True,
                key="btn_descargar_csv"
            )

        def resaltar_fila_total(row):
            if row["ID"] == "TOTAL":
                return [
                    'background-color: rgba(0, 0, 0, 0.05); '
                    'font-weight: bold; '
                    'border-top: 2px solid #cbd5e1;'
                ] * len(row)
            return [''] * len(row)

        df_styled = df.style.apply(resaltar_fila_total, axis=1)
        st.dataframe(df_styled, use_container_width=True, hide_index=True, key="planilla_view")

        st.markdown("#### ⚙️ Gestión de Estado Contable")
        opciones_id = list(mapa_opciones.keys())
        id_seleccionado = st.selectbox("Seleccionar Reserva:", opciones_id, key="mgmt_sel")

        if id_seleccionado:
            reserva_objeto = mapa_opciones[id_seleccionado]

            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("❌ Anular", use_container_width=True, key="btn_anular"):
                    reserva_objeto["estado"] = "Anulado"
                    guardar_datos()
                    st.rerun()
            with col_b2:
                if st.button("♻️ Activar", use_container_width=True, key="btn_activar"):
                    reserva_objeto["estado"] = "Activo"
                    guardar_datos()
                    st.rerun()
            with col_b3:
                if st.button("🗑️ Eliminar", use_container_width=True, key="btn_eliminar"):
                    st.session_state.registros.remove(reserva_objeto)
                    guardar_datos()
                    st.rerun()
    else:
        st.info("💡 No hay registros para este mes.")

    st.markdown("---")
    st.markdown(f"### 📅 Calendario - {mes_sel} {anio_sel}")
    
    st.markdown(
        f"""
        <div class="notranslate" translate="no" style="display: flex; gap: 15px; font-size: 0.85rem; margin-bottom: 10px;">
            <div><span style="background-color:#728C11;width:10px;height:10px;display:inline-block;border-radius:2px;"></span> {CABANA_1}</div>
            <div><span style="background-color:#3D9DD9;width:10px;height:10px;display:inline-block;border-radius:2px;"></span> {CABANA_2}</div>
            <div><span style="background:linear-gradient(135deg,#728C11 50%,#3D9DD9 50%);width:10px;height:10px;display:inline-block;border-radius:2px;"></span> Ambas</div>
        </div>
        """, unsafe_allow_html=True
    )

    cal_html = """
    <style>
        .grid-cal { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
        .h-dia { text-align: center; font-weight: bold; background: #1E3A8A; color: white; padding: 4px; border-radius: 4px; font-size: 0.8rem; }
        .c-dia { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-weight: bold; font-size: 0.9rem; box-shadow: inset 0 0 0 1px #E5E7EB; }
        .disp { background: #F9FAFB; color: #9CA3AF; }
        .cb1 { background: #728C11; color: white; }
        .cb2 { background: #3D9DD9; color: white; }
        .amb { background: linear-gradient(135deg, #728C11 50%, #3D9DD9 50%); color: white; }
    </style>
    <div class="grid-cal notranslate" translate="no">
        <div class="h-dia">Lu</div><div class="h-dia">Ma</div><div class="h-dia">Mi</div>
        <div class="h-dia">Ju</div><div class="h-dia">Vi</div><div class="h-dia">Sá</div><div class="h-dia">Do</div>
    """
    
    primer_dia_sem, _ = calendar.monthrange(anio_sel, mes_num)
    for _ in range(primer_dia_sem):
        cal_html += '<div class="c-dia" style="box-shadow:none;"></div>'

    for d in range(1, dias_en_mes + 1):
        c1, c2 = ocupacion_calendario[d][CABANA_1], ocupacion_calendario[d][CABANA_2]
        cls = "amb" if c1 and c2 else ("cb1" if c1 else ("cb2" if c2 else "disp"))
        cal_html += f'<div class="c-dia {cls}">{d}</div>'

    cal_html += "</div>"
    st.markdown(cal_html, unsafe_allow_html=True)
