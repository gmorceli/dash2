# app.py
# Dashboard fictício para 10 salas (Temperatura, Umidade, CO2)
# Regra de "piscar em vermelho": temp > 30°C E CO2 > 1000 ppm

import random
import time
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="Dashboard Salas - Clima & CO2", layout="wide")

# ---------- CSS (cards + blink) ----------
st.markdown(
    """
    <style>
      .grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 14px;
      }
      .card {
        background: #0f1b2d;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 14px 14px 10px 14px;
        color: #e9eef7;
        box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        min-height: 140px;
      }
      .title {
        font-size: 16px;
        font-weight: 700;
        letter-spacing: 0.2px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .badge {
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid rgba(255,255,255,0.12);
        background: rgba(255,255,255,0.05);
      }
      .row {
        display: flex;
        justify-content: space-between;
        margin: 6px 0;
        font-size: 14px;
      }
      .kpi {
        font-weight: 700;
      }

      /* Pisca em vermelho (quando temp>30 e CO2>1000) */
      @keyframes blinkRed {
        0%   { box-shadow: 0 0 0 rgba(255,0,0,0.0); border-color: rgba(255,0,0,0.25); background: #0f1b2d; }
        50%  { box-shadow: 0 0 30px rgba(255,0,0,0.40); border-color: rgba(255,0,0,0.95); background: rgba(255,0,0,0.18); }
        100% { box-shadow: 0 0 0 rgba(255,0,0,0.0); border-color: rgba(255,0,0,0.25); background: #0f1b2d; }
      }
      .blink-red {
        animation: blinkRed 0.9s linear infinite;
      }

      /* Alertas individuais */
      .alert-high-temp { color: #ff6b6b; font-weight: 700; }
      .alert-low-hum   { color: #74c0fc; font-weight: 700; }
      .alert-high-co2  { color: #ffa94d; font-weight: 700; }

      .muted {
        color: rgba(233, 238, 247, 0.75);
        font-size: 12px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Controles ----------
st.title("Dashboard – Temperatura, Umidade e CO₂ (10 salas)")
st.caption("Dados fictícios com atualização automática e alertas por sala.")

colA, colB, colC, colD = st.columns([1, 1, 1, 2])
with colA:
    temp_high_threshold = st.number_input("Alerta: Temp alta (°C)", value=30.0, step=0.5)
with colB:
    hum_low_threshold = st.number_input("Alerta: Umidade baixa (%)", value=30.0, step=1.0)
with colC:
    co2_high_threshold = st.number_input("Alerta: CO₂ alto (ppm)", value=1000, step=50)
with colD:
    refresh_s = st.slider("Atualizar a cada (segundos)", min_value=1, max_value=10, value=2)

st.divider()

# ---------- Geração de dados fictícios ----------
def fake_room_data(room_id: int) -> dict:
    # Ajuste as faixas para simular o comportamento desejado
    temp = round(random.uniform(25.0, 33.5), 1)
    hum = round(random.uniform(20.0, 55.0), 0)
    co2 = int(random.uniform(600, 1400))

    return {
        "room": f"Sala {room_id}",
        "temp": temp,
        "hum": int(hum),
        "co2": co2,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }

# ---------- Loop de atualização ----------
# Observação: Streamlit reexecuta o script; usamos auto-refresh simples via sleep + rerun.
placeholder = st.empty()

while True:
    rooms = [fake_room_data(i) for i in range(1, 11)]

    # Resumo de alertas
    high_temp = [r for r in rooms if r["temp"] > temp_high_threshold]
    low_hum = [r for r in rooms if r["hum"] < hum_low_threshold]
    high_co2 = [r for r in rooms if r["co2"] > co2_high_threshold]
    critical_blink = [
        r for r in rooms if (r["temp"] > temp_high_threshold and r["co2"] > co2_high_threshold)
    ]

    with placeholder.container():
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temp alta", len(high_temp))
        c2.metric("Umidade baixa", len(low_hum))
        c3.metric("CO₂ acima do limite", len(high_co2))
        c4.metric("Crítico (pisca)", len(critical_blink))

        st.markdown(
            f"<div class='muted'>Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='grid'>", unsafe_allow_html=True)

        for r in rooms:
            is_blink = (r["temp"] > temp_high_threshold and r["co2"] > co2_high_threshold)
            card_class = "card blink-red" if is_blink else "card"

            # Alertas por regra
            temp_alert = r["temp"] > temp_high_threshold
            hum_alert = r["hum"] < hum_low_threshold
            co2_alert = r["co2"] > co2_high_threshold

            badges = []
            if temp_alert:
                badges.append("<span class='alert-high-temp'>Temp alta</span>")
            if hum_alert:
                badges.append("<span class='alert-low-hum'>Umidade baixa</span>")
            if co2_alert:
                badges.append("<span class='alert-high-co2'>CO₂ alto</span>")

            badge_html = " | ".join(badges) if badges else "<span class='muted'>Sem alertas</span>"

            st.markdown(
                f"""
                <div class="{card_class}">
                  <div class="title">
                    <span>{r["room"]}</span>
                    <span class="badge">{r["timestamp"]}</span>
                  </div>

                  <div class="row"><span>Temperatura</span><span class="kpi">{r["temp"]} °C</span></div>
                  <div class="row"><span>Umidade</span><span class="kpi">{r["hum"]}%</span></div>
                  <div class="row"><span>CO₂</span><span class="kpi">{r["co2"]} ppm</span></div>

                  <div class="row" style="margin-top:10px;">
                    <span class="muted">Alertas</span>
                    <span>{badge_html}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    time.sleep(refresh_s)
    st.rerun()
