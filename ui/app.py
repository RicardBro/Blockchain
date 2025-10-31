import streamlit as st
import requests
import time
import os

# set_page_config must be the very first Streamlit command
st.set_page_config(layout="wide")

# Prefer environment variable for API_URL (works in containers and local dev).
# Avoid using `st.secrets` to prevent Streamlit from complaining when no secrets.toml exists.
API_URL = os.environ.get("API_URL", "http://api:8000")
JOB_TTL = int(os.environ.get("JOB_TTL", "30"))
# Header with environment badges
cols_hdr = st.columns([3, 1])
with cols_hdr[0]:
    st.title("Simulador Blockchain - UI")
with cols_hdr[1]:
    st.markdown(f"**API:** `{API_URL}`")
    st.markdown(f"**JOB_TTL:** `{JOB_TTL}s`")

st.markdown("---")

if 'last_claim' not in st.session_state:
    st.session_state['last_claim'] = None
if 'ui_log' not in st.session_state:
    st.session_state['ui_log'] = []

# helper to persist UI events to data/ui_events.json (atomic write)
def persist_event(ts, msg):
    try:
        base = os.environ.get('DATA_DIR', '.')
        d = os.path.join(base, 'data')
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, 'ui_events.json')
        # load existing
        try:
            import json as _json
            if os.path.exists(path):
                arr = _json.load(open(path, 'r', encoding='utf-8'))
            else:
                arr = []
        except Exception:
            arr = []
        arr.append([ts, msg])
        # atomic write
        import json as _json
        with open(path + '.tmp', 'w', encoding='utf-8') as fh:
            _json.dump(arr, fh, ensure_ascii=False, indent=2)
        os.replace(path + '.tmp', path)
    except Exception:
        pass

left, middle, right = st.columns([1, 2, 1])

with left:
    st.header("Nueva transacción")
    sender = st.text_input("Sender", key="sender")
    recipient = st.text_input("Recipient", key="recipient")
    amount = st.number_input("Amount", min_value=0.01, value=1.0, key="amount")
    message = st.text_input("Message", key="message")
    if st.button("Agregar TX", key="add_tx"):
        payload = {"sender": sender, "recipient": recipient, "amount": amount, "message": message}
        try:
            r = requests.post(f"{API_URL}/transactions", json=payload, timeout=5)
            if r.ok:
                st.success("TX agregada")
                ev = (time.time(), f"TX agregada: {sender} → {recipient} ({amount})")
                st.session_state['ui_log'].append(ev)
                persist_event(*ev)
            else:
                st.error(f"Error: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"No se pudo conectar al API: {e}")

    st.markdown("---")
    st.header("Control de Minado")
    cols_actions = st.columns([1,1,1])
    if cols_actions[0].button("Claim work", key="claim"):
        try:
            r = requests.post(f"{API_URL}/jobs/claim", timeout=5)
            data = r.json()
            st.session_state['last_claim'] = data
            if data.get('claim_id'):
                st.success(f"Claim obtenido: {data.get('claim_id')}")
                ev = (time.time(), f"Claim obtenido: {data.get('claim_id')} (txs={len(data.get('txs') or [])})")
                st.session_state['ui_log'].append(ev)
                persist_event(*ev)
                if data.get('txs'):
                    st.info(f"Transacciones: {len(data.get('txs'))}")
            else:
                st.info("No hay trabajo disponible")
                ev = (time.time(), "Claim vacío: no hay trabajo disponible")
                st.session_state['ui_log'].append(ev)
                persist_event(*ev)
        except Exception as e:
            st.error(f"Error al reclamar trabajo: {e}")
    if cols_actions[1].button("Release last claim", key="release_last_btn"):
        lc = st.session_state.get('last_claim') or {}
        cid = lc.get('claim_id')
        if cid:
            try:
                requests.post(f"{API_URL}/jobs/release", json={"claim_id": cid}, timeout=5)
                st.success("Released")
                ev = (time.time(), f"Released claim {cid}")
                st.session_state['ui_log'].append(ev)
                persist_event(*ev)
                st.session_state['last_claim'] = None
            except Exception as e:
                st.error(str(e))
        else:
            st.info("No hay claim reciente para liberar")
    if cols_actions[2].button("Refresh status", key="refresh_status"):
        st.experimental_rerun()

    if st.session_state['last_claim']:
        lc = st.session_state['last_claim']
        st.write("Último claim:")
        st.json(lc)
        if lc.get('claim_id') and st.button("Release last claim", key="release_last"):
            try:
                requests.post(f"{API_URL}/jobs/release", json={"claim_id": lc.get('claim_id')}, timeout=5)
                st.success("Released")
                st.session_state['last_claim'] = None
            except Exception as e:
                st.error(str(e))

    st.markdown("---")
    st.subheader("Últimas acciones")
    # show a compact visual log with simple coloring
    for ts, msg in reversed(st.session_state['ui_log'][-30:]):
        tstr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        # simple heuristics for coloring
        if 'error' in msg.lower() or 'no se pudo' in msg.lower():
            emoji = "❌"
            color = "#ff6b6b"
        elif 'claim obtenido' in msg.lower() or 'tx agregada' in msg.lower() or 'released' in msg.lower():
            emoji = "✅"
            color = "#6bff9a"
        else:
            emoji = "ℹ️"
            color = "#ffd66b"
        st.markdown(f"<div style='padding:6px;border-radius:6px;margin-bottom:4px;background:{color};'><strong>{emoji} {tstr}</strong> — {msg}</div>", unsafe_allow_html=True)

with middle:
    st.header("Mempool")
    try:
        mempool = requests.get(f"{API_URL}/mempool", timeout=5).json()
        total_txs = len(mempool) if isinstance(mempool, list) else 0
        st.write("Total TX:", total_txs)
        st.json(mempool)
    except Exception as e:
        st.error(f"No se pudo obtener mempool: {e}")

    st.markdown("---")
    st.header("Inflight claims")
    try:
        infl = requests.get(f"{API_URL}/jobs/inflight", timeout=5).json()
        infl_list = infl.get("inflight", [])
        for c in infl_list:
            cid = c.get('claim_id') or str(time.time())
            with st.expander(f"Claim {cid} - by {c.get('worker','unknown')}", expanded=False):
                st.json(c)
                if st.button("Release", key=f"release_{cid}"):
                    try:
                        requests.post(f"{API_URL}/jobs/release", json={"claim_id": c.get('claim_id')}, timeout=5)
                        st.success("Released")
                        ev = (time.time(), f"Released claim {c.get('claim_id')} via inflight UI")
                        st.session_state['ui_log'].append(ev)
                        persist_event(*ev)
                    except Exception as e:
                        st.error(str(e))
        # show inflight count
        st.write(f"Inflight count: {len(infl_list)}")
    except Exception as e:
        st.error(f"No se pudo obtener inflight: {e}")

    # Force mine button
    st.markdown("---")
    st.subheader("Acciones de minado")
    cols_m = st.columns([1,1])
    if cols_m[0].button("Forzar minado", key="force_mine"):
        try:
            # only attempt to force-mine if there are inflight claims; do not fall back to mempool
            infl = requests.get(f"{API_URL}/jobs/inflight", timeout=2).json().get('inflight', [])
            if not infl:
                st.info("No hay inflight para minar. Primero reclamá trabajo con 'Claim work'.")
            else:
                r = requests.post(f"{API_URL}/_internal/force_mine", timeout=2)
                if r.status_code == 202 or r.status_code == 200 or r.ok:
                    info = r.json() if r.text else {"status":"started"}
                    ev = (time.time(), f"Forzar minado arrancado: {info}")
                    st.session_state['ui_log'].append(ev)
                    persist_event(*ev)
                    # Kick off polling UI: show difficulty and poll miner_status until done
                    try:
                        diff = requests.get(f"{API_URL}/difficulty", timeout=2).json().get('difficulty', None)
                    except Exception:
                        diff = None
                    with st.spinner("Miner arrancado - esperando resultado..."):
                        bar = st.progress(0)
                        attempts_text = st.empty()
                        while True:
                            try:
                                s = requests.get(f"{API_URL}/_internal/miner_status", timeout=2).json()
                            except Exception as e:
                                ev = (time.time(), f"Error polling miner status: {e}")
                                st.session_state['ui_log'].append(ev)
                                persist_event(*ev)
                                break
                            state = s.get('state')
                            attempts = s.get('attempts', 0) or 0
                            attempts_text.write(f"Miner state: {state} — attempts: {attempts}")
                            # if difficulty known, show rough progress as attempts / 2**difficulty (clamped)
                            if diff:
                                try:
                                    expected = float(2 ** diff)
                                    progress = min(0.9999, attempts / expected)
                                    bar.progress(int(progress * 100))
                                except Exception:
                                    pass
                            if state != 'mining':
                                # final update
                                bar.progress(100)
                                ev = (time.time(), f"Miner finished: {s}")
                                st.session_state['ui_log'].append(ev)
                                persist_event(*ev)
                                break
                            time.sleep(0.5)
                else:
                    ev = (time.time(), f"Forzar minado error: {r.status_code} {r.text}")
                    st.session_state['ui_log'].append(ev)
                    persist_event(*ev)
        except Exception as e:
            ev = (time.time(), f"Forzar minado falló: {e}")
            st.session_state['ui_log'].append(ev)
            persist_event(*ev)

    if cols_m[1].button("Estado minero", key="miner_status"):
        try:
            s = requests.get(f"{API_URL}/_internal/miner_status", timeout=2).json()
            ev = (time.time(), f"Miner status: {s}")
            st.session_state['ui_log'].append(ev)
            persist_event(*ev)
        except Exception as e:
            ev = (time.time(), f"No se pudo obtener estado del minero: {e}")
            st.session_state['ui_log'].append(ev)
            persist_event(*ev)

    # Timeline panel (combine ui_log + inflight + miner status)
    st.markdown("---")
    st.header("Timeline")
    # read persisted UI events if any (lightweight)
    events = list(st.session_state.get('ui_log', []))
    # try to read data/ui_events.json for persisted events
    try:
        data_dir = os.environ.get('DATA_DIR', '.')
        evpath = os.path.join(data_dir, 'data', 'ui_events.json')
        if os.path.exists(evpath):
            import json
            with open(evpath, 'r', encoding='utf-8') as fh:
                more = json.load(fh)
            # more is expected to be list of [ts,msg]
            events = list(more) + events
    except Exception:
        pass

    # show most recent 40 events
    for ts, msg in reversed(events[-40:]):
        tstr = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        st.markdown(f"- **{tstr}** — {msg}")

    # Blockchain list view: show blocks with basic metadata and transactions
    st.markdown("---")
    st.subheader("Blockchain (lista de bloques)")
    try:
        chain = requests.get(f"{API_URL}/chain", timeout=3).json()
        total = len(chain) if isinstance(chain, list) else 0
        st.write(f"Total bloques: {total}")
        # show each block in an expander with key metadata and transaction list
        for b in chain:
            idx = b.get('index')
            ts = b.get('timestamp')
            txs = b.get('transactions', []) or b.get('txs', []) or []
            header = f"#{idx} — {ts} — {len(txs)} tx(s)"
            with st.expander(header, expanded=False):
                st.write(f"Hash: {b.get('hash')}")
                st.write(f"Prev hash: {b.get('prev_hash')}")
                st.write(f"Nonce: {b.get('nonce')}")
                st.markdown("**Transacciones**")
                if txs:
                    st.json(txs)
                else:
                    st.info("Este bloque no contiene transacciones")
    except Exception as e:
        st.error(f'No se pudo obtener la cadena: {e}')

    # Right column: Miner logs (persistent)
    st.markdown('---')
    st.subheader('Miner logs (persisted)')
    try:
        data_dir = os.environ.get('DATA_DIR', '.')
        logs_path = os.path.join(data_dir, 'data', 'miner_logs.json')
        if os.path.exists(logs_path):
            import json
            with open(logs_path, 'r', encoding='utf-8') as fh:
                logs = json.load(fh)
            # logs expected to be list of dict snapshots; if lines of json objects, handle both
            if isinstance(logs, dict):
                logs = [logs]
            if not isinstance(logs, list):
                st.write('Formato de logs no reconocido')
            else:
                # show most recent 50 entries
                for entry in reversed(logs[-50:]):
                    ts = entry.get('ts') or entry.get('timestamp') or entry.get('time')
                    try:
                        tstr = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts)) if ts else ''
                    except Exception:
                        tstr = str(ts)
                    state = entry.get('state')
                    claim_id = entry.get('claim_id')
                    attempts = entry.get('attempts')
                    blk_idx = entry.get('block_index')
                    h = entry.get('hash')
                    line = f"{tstr} — state={state} claim={claim_id} attempts={attempts} block={blk_idx} hash={h}"
                    st.markdown(f"<div style='padding:6px;border-radius:6px;margin-bottom:4px;background:#eef2ff;'>{line}</div>", unsafe_allow_html=True)
        else:
            st.info('No se encontraron miner logs en data/miner_logs.json')
    except Exception as e:
        st.error(f'No se pudieron leer miner logs: {e}')
