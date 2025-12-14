# app.py
# Dashboard de 10 salas (grid 5x2) + ícones + detalhe com histórico (30 min)

import random
import time
from datetime import datetime, timedelta
from textwrap import dedent

import pandas as pd
import streamlit as st

# ---------------------------
# Configuração da página
# ---------------------------
st.set_page_config(page_title="Dashboard Salas – Clima & CO₂", layout="wide")

# ---------------------------
# SVGs inline (ícones)
# ---------------------------
def svg_icon(kind: str, size: int = 18) -> str:
    # Ícones simples em SVG (sem dependência externa)
    if kind == "temp":
        svg = f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
          <path d="M14 14.76V5a2 2 0 10-4 0v9.76a4 4 0 104 0Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          <path d="M10 14.5V5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        """
    elif kind == "hum":
        svg = f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
          <path d="M12 2s7 7.2 7 12a7 7 0 11-14 0c0-4.8 7-12 7-12Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
        </svg>
        """
    else:  # co2
        svg = f"""
        <svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none">
          <path d="M4 14c0 4 4 7 8 7s8-3 8-7-4-7-8-7-8 3-8 7Z" stroke="currentColor" stroke-width="2"/>
          <path d="M8 12h1.5a1.5 1.5 0 010 3H8v-3Z" stroke="currentColor" stroke-width="2"/>
          <path d="M16 12h-1.5a1.5 1.5 0 000 3H16v-3Z" stroke="currentColor" stroke-width="2"/>
        </svg>
        """
    return svg

# ---------------------------
# CSS – grid + cards + blink
# ---------------------------
st.markdown(
    """
    <style>
      .topbar { margin-bottom: 10px; }
      .gridwrap { margin-top: 6px; }

      /* Card */
      .room-card {
        background: #0f1b2d;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 14px;
        padding: 12px 12px 10px 12px;
        box-shadow: 0 10px 26px rgba(0,0,0,0.18);
        min-height: 150px;
      }
      .room-title {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap: 8px;
        font-weight: 800;
        font-size: 15px;
        color: #e9eef7;
        margin-bottom: 8px;
      }
      .badge {
        font-size: 11px;
        padding: 3px 8px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.06);
        color: rgba(233,238,247,0.85);
        white-space: nowrap;
      }
      .metric-line {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap: 8px;
        margin: 6px 0;
        color: rgba(233,238,247,0.92);
        font-size: 13px;
      }
      .metric-left {
        display:flex; align-items:center; gap:8px;
        color: rgba(233,238,247,0.85);
      }
      .metric-val {
        font-weight: 800;
        color: #e9eef7;
      }
      .alerts {
        margin-top: 10px;
        font-size: 12px;
        color: rgba(233,238,247,0.85);
      }
      .tag {
        display:inline-block;
        margin-right: 6px;
        margin-top: 6px;
        padding: 3px 8px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.14);
        background: rgba(255,255,255,0.06);
      }
      .tag-high-temp { border-color: rgba(255,107,107,0.55); color: #ffb3b3; }
      .tag-low-hum   { border-color: rgba(116,192,252,0.55); color: #b9ddff; }
      .tag-high-co2  { border-color: rgba(255,169,77,0.55); color: #ffd0a1; }

      /* Piscar em vermelho (temp > 30 e CO2 > 1000) */
      @keyframes blinkRed {
        0%   { box-shadow: 0 0 0 rgba(255,0,0,0.0); border-color: rgba(255,0,0,0.25); background: #0f1b2d; }
        50%  { box-shadow: 0 0 22px rgba(255,0,0,0.42); border-color: rgba(255,0,0,0.95); background: rgba(255,0,0,0.18); }
        100% { box-shadow: 0 0 0 rgba(255,0,0,0.0); border-color: rgba(255,0,0,0.25); background: #0f1b2d; }
      }
      .blink-red { animation: blinkRed 0.9s linear infinite; }

      /* Ajuste para botões do Streamlit não “incharem” o layout */
      div.stButton > button {
        width: 100%;
        border-radius: 14px;
        padding: 0;
        border: none;
        background: transparent;
      }
      div.stButton > button:hover { background: transparent; }
      div.stButton > button:focus { outline: none; box-shadow: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# Funções de dados fictícios
# ---------------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def init_history(now: datetime) -> pd.DataFrame:
    # 48 pontos = 24h em intervalos de 30 min
    times = [now - timedelta(minutes=30 * i) for i in reversed(range(48))]
    base_temp = random.uniform(24.5, 30.5)
    base_hum = random.uniform(25, 50)
    base_co2 = random.uniform(650, 1100)

    rows = []
    t = base_temp
    h = base_hum
    c = base_co2
    for ts in times:
        # “caminhada” suave
        t = clamp(t + random.uniform(-0.6, 0.6), 20.0, 36.0)
        h = clamp(h + random.uniform(-2.0, 2.0), 15.0, 70.0)
        c = clamp(c + random.uniform(-60, 60), 450, 1600)
        rows.append({"timestamp": ts, "temp": round(t, 1), "hum": int(round(h)), "co2": int(round(c))})

    return pd.DataFrame(rows)

def update_current_from_history(df: pd.DataFrame) -> dict:
    last = df.iloc[-1]
    return {"temp": float(last["temp"]), "hum": int(last["hum"]), "co2": int(last["co2"])}

def step_history(df: pd.DataFrame, now: datetime) -> pd.DataFrame:
    """
    Atualiza o histórico simulando um novo ponto a cada 30 minutos.
    Para demo: se passou >=30 min do último timestamp, adiciona um ponto.
    """
    last_ts = pd.to_datetime(df["timestamp"].iloc[-1])
    if now - last_ts >= timedelta(minutes=30):
        last = df.iloc[-1]
        new_temp = clamp(float(last["temp"]) + random.uniform(-0.8, 0.8), 20.0, 36.0)
        new_hum = clamp(int(last["hum"]) + int(random.uniform(-3, 3)), 15, 70)
        new_co2 = clamp(int(last["co2"]) + int(random.uniform(-90, 90)), 450, 1600)

        new_row = pd.DataFrame([{
            "timestamp": now.replace(second=0, microsecond=0),
            "temp": round(new_temp, 1),
            "hum": int(new_hum),
            "co2": int(new_co2),
        }])

        df = pd.concat([df, new_row], ignore_index=True)
        # mantém últimos 48 pontos
        if len(df) > 48:
            df = df.iloc[-48:].reset_index(drop=True)

    return df

# ---------------------------
# Estado da aplicação
# ---------------------------
now = datetime.now()

if "rooms" not in st.session_state:
    st.session_state.rooms = {}
    for i in range(1, 11):
        hist = init_history(now)
        st.session_state.rooms[i] = {
            "name": f"Sala {i}",
            "history": hist,
            "current": update_current_from_history(hist),
        }

if "selected_room" not in st.session_state:
    st.session_state.selected_room = 1

# ---------------------------
# Controles / Limiares
# ---------------------------
st.markdown(
    dedent(f"""
    <div class="{card_class}">
      <div class="room-title">
        <span>{room['name']}</span>
        <span class="badge">agora</span>
      </div>

      <div class="metric-line">
        <span class="metric-left">{svg_icon("temp")} Temperatura</span>
        <span class="metric-val">{cur["temp"]:.1f} °C</span>
      </div>

      <div class="metric-line">
        <span class="metric-left">{svg_icon("hum")} Umidade</span>
        <span class="metric-val">{cur["hum"]}%</span>
      </div>

      <div class="metric-line">
        <span class="metric-left">{svg_icon("co2")} CO₂</span>
        <span class="metric-val">{cur["co2"]} ppm</span>
      </div>

      <div class="alerts">
        {tags_html}
      </div>
    </div>
    """),
    unsafe_allow_html=True,
)

# Auto-refresh sem travar cliques (Streamlit moderno)
# Se sua versão do Streamlit não tiver st.autorefresh, atualize: pip install -U streamlit
#st.autorefresh(interval=refresh_s * 1000, key="tick")

# Atualiza históricos (quando completar 30 min desde o último ponto)
for i in range(1, 11):
    st.session_state.rooms[i]["history"] = step_history(st.session_state.rooms[i]["history"], now)
    st.session_state.rooms[i]["current"] = update_current_from_history(st.session_state.rooms[i]["history"])

# ---------------------------
# Grid 5x2 (uma tela) – cada sala é um “quadrado” clicável
# ---------------------------
st.subheader("Salas (clique para ver detalhes e histórico)")
st.markdown("<div class='gridwrap'>", unsafe_allow_html=True)

room_ids = list(range(1, 11))
rows = [room_ids[:5], room_ids[5:]]

for row in rows:
    cols = st.columns(5, gap="medium")
    for col, rid in zip(cols, row):
        with col:
            room = st.session_state.rooms[rid]
            cur = room["current"]

            temp_alert = cur["temp"] > temp_thr
            hum_alert = cur["hum"] < hum_thr
            co2_alert = cur["co2"] > co2_thr
            blink = temp_alert and co2_alert

            tags = []
            if temp_alert:
                tags.append("<span class='tag tag-high-temp'>Temp alta</span>")
            if hum_alert:
                tags.append("<span class='tag tag-low-hum'>Umidade baixa</span>")
            if co2_alert:
                tags.append("<span class='tag tag-high-co2'>CO₂ alto</span>")
            tags_html = "".join(tags) if tags else "<span class='tag'>Sem alertas</span>"

            card_class = "room-card blink-red" if blink else "room-card"

            # Botão “invisível” que envolve o card (clique na sala)
            if st.button(f"{room['name']}", key=f"room_btn_{rid}"):
                st.session_state.selected_room = rid

            # Render do card (aproveita o espaço do botão acima)
            st.markdown(
                f"""
                <div class="{card_class}">
                  <div class="room-title">
                    <span>{room['name']}</span>
                    <span class="badge">agora</span>
                  </div>

                  <div class="metric-line">
                    <span class="metric-left">{svg_icon("temp")} Temperatura</span>
                    <span class="metric-val">{cur["temp"]:.1f} °C</span>
                  </div>

                  <div class="metric-line">
                    <span class="metric-left">{svg_icon("hum")} Umidade</span>
                    <span class="metric-val">{cur["hum"]}%</span>
                  </div>

                  <div class="metric-line">
                    <span class="metric-left">{svg_icon("co2")} CO₂</span>
                    <span class="metric-val">{cur["co2"]} ppm</span>
                  </div>

                  <div class="alerts">
                    {tags_html}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ---------------------------
# Visão detalhada (ao clicar em uma sala)
# ---------------------------
sel = st.session_state.selected_room
room = st.session_state.rooms[sel]
hist = room["history"].copy()
hist["timestamp"] = pd.to_datetime(hist["timestamp"])

st.subheader(f"Detalhes – {room['name']} (histórico a cada 30 min)")

k1, k2, k3, k4 = st.columns([1, 1, 1, 2])
k1.metric("Temperatura (agora)", f"{room['current']['temp']:.1f} °C")
k2.metric("Umidade (agora)", f"{room['current']['hum']}%")
k3.metric("CO₂ (agora)", f"{room['current']['co2']} ppm")
k4.caption("O histórico é simulado em pontos de 30 minutos (últimas 24h).")

tabs = st.tabs(["Temperatura", "Umidade", "CO₂", "Tabela"])
with tabs[0]:
    st.line_chart(hist.set_index("timestamp")["temp"])
with tabs[1]:
    st.line_chart(hist.set_index("timestamp")["hum"])
with tabs[2]:
    st.line_chart(hist.set_index("timestamp")["co2"])
with tabs[3]:
    st.dataframe(hist.sort_values("timestamp", ascending=False), use_container_width=True)
#time.sleep(refresh_s)
#st.rerun()
