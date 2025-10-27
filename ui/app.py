import streamlit as st
import requests

API_URL = st.secrets.get("API_URL", "http://api:8000")

st.title("Simulador Blockchain - UI")

with st.sidebar:
    st.header("Nueva transacción")
    sender = st.text_input("Sender")
    recipient = st.text_input("Recipient")
    amount = st.number_input("Amount", min_value=0.01, value=1.0)
    message = st.text_input("Message")
    if st.button("Agregar TX"):
        payload = {"sender": sender, "recipient": recipient, "amount": amount, "message": message}
        try:
            r = requests.post(f"{API_URL}/transactions", json=payload)
            st.success("TX agregada")
        except Exception as e:
            st.error(str(e))

st.subheader("Mempool")
try:
    mempool = requests.get(f"{API_URL}/mempool").json()
    st.write(mempool)
except Exception as e:
    st.write("No se pudo obtener mempool: ", e)

st.subheader("Cadena")
try:
    chain = requests.get(f"{API_URL}/chain").json()
    for b in chain:
        st.write(b)
except Exception as e:
    st.write("No se pudo obtener chain: ", e)

if st.button("Validar Cadena"):
    try:
        val = requests.get(f"{API_URL}/validate").json()
        st.write(val)
    except Exception as e:
        st.error(str(e))
