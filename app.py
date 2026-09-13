import calendar
from datetime import datetime, timedelta
import json
import os
import urllib.parse
import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Refugio Repalet - Gestión y Reservas",
    page_icon="🏡",
    layout="wide",
)

# -----------------------------------------------------------------------------
# SEGURIDAD / CONTRASEÑA
# -----------------------------------------------------------------------------
# Cambia 'repalet2026' por la contraseña que prefieras usar
ADMIN_PASSWORD = "repalet2026"

query_params = st.query_params
modo_publico = (query_params.get("view") == "public") or (
    query_params.get("modo") == "publico"
)

# -----------------------------------------------------------------------------
# PERSISTENCIA DE DATOS (JSON)
# -----------------------------------------------------------------------------
DB_FILE = "reservas.json"


def cargar_reservas():
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return []
  return []


def guardar_reservas(reservas):
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(reservas, f, ensure_ascii=False, indent=4)


if "reservas" not in st.session_state:
  st.session_state.reservas = cargar_reservas()

CABANAS = ["Cabaña 1", "Cabaña 2", "Cabaña 3"]

# -----------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------
MESES_ES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}


def obtener_dias_ocupados_cabana(cabana):
  dias = set()
  for r in st.session_state.reservas:
    if r.get("cabana") == cabana:
      try:
        f_in = datetime.strptime(r["checkin"], "%Y-%m-%d").date()
        f_out = datetime.strptime(r["checkout"], "%Y-%m-%d").date()
        curr = f_in
        while curr < f_out:
          dias.add(curr)
          curr += timedelta(days=1)
      except ValueError:
        pass
  return dias


def mostrar_calendario_cabana(cabana, año, mes):
  dias_ocupados = obtener_dias_ocupados_cabana(cabana)
  cal = calendar.monthcalendar(año, mes)
  st.markdown(f"#### {cabana}")

  cols = st.columns(7)
  dias_semana = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
  for idx, d in enumerate(dias_semana):
    cols[idx].markdown(f"**{d}**")

  for semana in cal:
    cols = st.columns(7)
    for idx, dia in enumerate(semana):
      if dia == 0:
        cols[idx].write("")
      else:
        fecha_eval = datetime(año, mes, dia).date()
        if fecha_eval in dias_ocupados:
          cols[idx].markdown(
              f"<div style='text-align:center; background-color:#ff4b4b; color:white;"
              f" border-radius:5px; padding:2px;'><b>{dia}</b></div>",
              unsafe_allow_html=True,
          )
        else:
          cols[idx].markdown(
              f"<div style='text-align:center; background-color:#28a745; color:white;"
              f" border-radius:5px; padding:2px;'><b>{dia}</b></div>",
              unsafe_allow_html=True,
          )


# -----------------------------------------------------------------------------
# VISTA PÚBLICA (CLIENTES)
# -----------------------------------------------------------------------------
if modo_publico:
  st.title("🏡 Refugio Repalet - Disponibilidad")
  st.markdown("Consulta la disponibilidad de nuestras cabañas en tiempo real:")

  hoy = datetime.now()
  meses_opciones = []
  for i in range(4):
    m = (hoy.month - 1 + i) % 12 + 1
    y = hoy.year + ((hoy.month - 1 + i) // 12)
    meses_opciones.append((y, m))

  opcion = st.selectbox(
      "Selecciona el mes a consultar:",
      options=range(len(meses_opciones)),
      format_func=lambda idx: (
          f"{MESES_ES[meses_opciones[idx][1]]} {meses_opciones[idx][0]}"
      ),
  )

  año_sel, mes_sel = meses_opciones[opcion]
  st.write("---")

  col1, col2, col3 = st.columns(3)
  with col1:
    mostrar_calendario_cabana("Cabaña 1", año_sel, mes_sel)
  with col2:
    mostrar_calendario_cabana("Cabaña 2", año_sel, mes_sel)
  with col3:
    mostrar_calendario_cabana("Cabaña 3", año_sel, mes_sel)

  st.write("---")
  msg = (
      f"Hola! Quisiera consultar disponibilidad para el mes de"
      f" {MESES_ES[mes_sel]} {año_sel} en Refugio Repalet."
  )
  wa_url = f"https://wa.me/56912345678?text={urllib.parse.quote(msg)}"
  st.markdown(
      f'<a href="{wa_url}" target="_blank" style="text-decoration:none;"><button'
      ' style="background-color:#25D366; color:white; border:none; padding:12px'
      " 24px; font-size:16px; border-radius:8px; cursor:pointer; font-weight:"
      'bold;">📲 Consultar Reserva por WhatsApp</button></a>',
      unsafe_allow_html=True,
  )

# -----------------------------------------------------------------------------
# VISTA PRIVADA (ADMINISTRADOR)
# -----------------------------------------------------------------------------
else:
  if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

  if not st.session_state.autenticado:
    st.title("🔒 Acceso Restringido - Refugio Repalet")
    clave = st.text_input("Ingresa la contraseña de administrador:", type="password")
    if st.button("Ingresar"):
      if clave == ADMIN_PASSWORD:
        st.session_state.autenticado = True
        st.rerun()
      else:
        st.error("Contraseña incorrecta.")
  else:
    st.sidebar.title("Menú Administrador")
    if st.sidebar.button("🔒 Cerrar Sesión"):
      st.session_state.autenticado = False
      st.rerun()

    st.title("📊 Panel de Control y Administración - Refugio Repalet")

    tab1, tab2, tab3 = st.tabs(
        ["📝 Nueva Reserva", "📈 Finanzas e Impuestos", "📅 Calendario Interno"]
    )

    with tab1:
      st.header("Ingresar Nueva Reserva")
      with st.form("form_reserva", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        cliente = col_c1.text_input("Nombre del Huésped")
        cabana_sel = col_c2.selectbox("Seleccionar Cabaña", CABANAS)

        col_f1, col_f2 = st.columns(2)
        checkin = col_f1.date_input("Fecha Check-in")
        checkout = col_f2.date_input(
            "Fecha Check-out", value=checkin + timedelta(days=1)
        )

        col_p1, col_p2 = st.columns(2)
        monto_total = col_p1.number_input(
            "Monto Total Cobrado ($)", min_value=0, step=5000
        )
        plataforma = col_p2.selectbox(
            "Plataforma de Origen",
            ["Directo (Sin comisión)", "Airbnb", "Booking"],
        )

        submitted = st.form_submit_button("Guardar Reserva")
        if submitted:
          if checkout <= checkin:
            st.error(
                "La fecha de Check-out debe ser posterior a la de Check-in."
            )
          else:
            nueva_reserva = {
                "id": len(st.session_state.reservas) + 1,
                "cliente": cliente,
                "cabana": cabana_sel,
                "checkin": str(checkin),
                "checkout": str(checkout),
                "monto": monto_total,
                "plataforma": plataforma,
            }
            st.session_state.reservas.append(nueva_reserva)
            guardar_reservas(st.session_state.reservas)
            st.success(
                f"Reserva de {cliente} en {cabana_sel} guardada con éxito."
            )

    with tab2:
      st.header("Resumen Financiero e Impuestos")
      if st.session_state.reservas:
        df = pd.DataFrame(st.session_state.reservas)

        # Cálculos de comisiones e impuestos
        def calc_comision(row):
          p = row.get("plataforma", "")
          m = row.get("monto", 0)
          if "Airbnb" in p:
            return m * 0.03
          elif "Booking" in p:
            return m * 0.15
          return 0.0

        df["Comisión ($)"] = df.apply(calc_comision, axis=1)
        df["Ingreso Neto ($)"] = df["monto"] - df["Comisión ($)"]
        df["Estimación IVA/Impuesto ($)"] = df["Ingreso Neto ($)"] * 0.19

        st.dataframe(df, use_container_width=True)

        tot_bruto = df["monto"].sum()
        tot_com = df["Comisión ($)"].sum()
        tot_neto = df["Ingreso Neto ($)"].sum()
        tot_iva = df["Estimación IVA/Impuesto ($)"].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ingreso Bruto Total", f"${tot_bruto:,.0f}")
        m2.metric("Comisiones Plataformas", f"${tot_com:,.0f}")
        m3.metric("Ingreso Neto", f"${tot_neto:,.0f}")
        m4.metric("Est. IVA (19%)", f"${tot_iva:,.0f}")
      else:
        st.info("No hay reservas registradas aún.")

    with tab3:
      st.header("Calendario Interno de Disponibilidad")
      hoy = datetime.now()
      c1, c2, c3 = st.columns(3)
      with c1:
        mostrar_calendario_cabana("Cabaña 1", hoy.year, hoy.month)
      with c2:
        mostrar_calendario_cabana("Cabaña 2", hoy.year, hoy.month)
      with c3:
        mostrar_calendario_cabana("Cabaña 3", hoy.year, hoy.month)
