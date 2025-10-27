import streamlit as st
import time
from blockchain import Blockchain, Block
import json

# Configuración de la página
st.set_page_config(
    page_title="Simulador Blockchain",
    page_icon="⛓️",
    layout="wide"
)

# Inicializar la blockchain en session_state
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain(difficulty=4)
if 'mining_animation' not in st.session_state:
    st.session_state.mining_animation = False
if 'hack_mode' not in st.session_state:
    st.session_state.hack_mode = False

blockchain = st.session_state.blockchain

# Título principal
st.title("⛓️ Simulador de Blockchain Educativo")
st.markdown("---")

# Layout en columnas
col1, col2 = st.columns([1, 2])

# ========== COLUMNA IZQUIERDA: ACCIONES ==========
with col1:
    st.header("🎮 Panel de Control")
    
    # Sección: Agregar Transacción
    st.subheader("💸 Nueva Transacción")
    with st.form("transaction_form"):
        sender = st.text_input("Remitente", value="Alice")
        recipient = st.text_input("Destinatario", value="Bob")
        amount = st.number_input("Cantidad", min_value=0.01, value=10.0, step=0.01)
        submit_tx = st.form_submit_button("➕ Agregar a Mempool")
        
        if submit_tx:
            transaction = {
                "sender": sender,
                "recipient": recipient,
                "amount": amount
            }
            blockchain.add_transaction(transaction)
            st.success(f"✅ Transacción agregada al mempool")
            st.rerun()
    
    # Mostrar Mempool
    st.subheader("📋 Mempool (Transacciones Pendientes)")
    if blockchain.mempool:
        st.info(f"🔢 Total: {len(blockchain.mempool)} transacción(es)")
        for idx, tx in enumerate(blockchain.mempool):
            with st.expander(f"TX {idx + 1}: {tx.get('sender', 'N/A')} → {tx.get('recipient', 'N/A')}"):
                st.json(tx)
    else:
        st.warning("⚠️ Mempool vacío")
    
    # Botón de Minado
    st.markdown("---")
    if st.button("⛏️ Minar Bloque", type="primary", disabled=len(blockchain.mempool) == 0):
        st.session_state.mining_animation = True
        st.rerun()
    
    # Animación de minado
    if st.session_state.mining_animation:
        st.subheader("⚙️ Minando...")
        
        # Crear el bloque
        new_block = Block(
            index=len(blockchain.chain),
            transactions=blockchain.mempool.copy(),
            previous_hash=blockchain.get_latest_block().hash
        )
        
        # Placeholder para animación
        animation_placeholder = st.empty()
        progress_bar = st.progress(0)
        
        # Constantes para la animación de minado
        UPDATE_FREQUENCY = 1000  # Actualizar cada 1000 intentos
        PROGRESS_CYCLE_SIZE = 50000  # Ciclo de progreso visual
        MAX_MINING_ATTEMPTS = 1000000  # Límite máximo de intentos
        
        # Proceso de minado con animación
        target = "0" * blockchain.difficulty
        attempts = 0
        
        while new_block.hash[:blockchain.difficulty] != target and attempts < MAX_MINING_ATTEMPTS:
            new_block.nonce += 1
            new_block.hash = new_block.calculate_hash()
            attempts += 1
            
            # Actualizar cada ciertos intentos
            if attempts % UPDATE_FREQUENCY == 0:
                animation_placeholder.code(f"""
Nonce: {new_block.nonce}
Hash: {new_block.hash}
Target: {target}{'.' * (32 - len(target))}
Intentos: {attempts:,}
                """)
                # Mostrar progreso basado en el número de intentos (estimación)
                progress_estimate = min((attempts % PROGRESS_CYCLE_SIZE) / PROGRESS_CYCLE_SIZE, 0.99)
                progress_bar.progress(progress_estimate)
        
        # Verificar si se alcanzó el límite sin encontrar solución
        if attempts >= MAX_MINING_ATTEMPTS:
            animation_placeholder.error(f"""
❌ Error de Minado
Se alcanzó el límite de {MAX_MINING_ATTEMPTS:,} intentos sin encontrar un hash válido.
Intenta reducir la dificultad.
            """)
            st.session_state.mining_animation = False
            st.stop()
        
        # Finalizar minado
        blockchain.chain.append(new_block)
        blockchain.mempool = []
        
        progress_bar.progress(1.0)
        animation_placeholder.success(f"""
✅ ¡Bloque Minado!
Nonce final: {new_block.nonce}
Hash: {new_block.hash}
Intentos totales: {attempts:,}
        """)
        
        time.sleep(2)
        st.session_state.mining_animation = False
        st.rerun()

# ========== COLUMNA DERECHA: BLOCKCHAIN ==========
with col2:
    st.header("🔗 Blockchain")
    
    # Mostrar información general
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("📦 Bloques", len(blockchain.chain))
    with col_info2:
        st.metric("🔒 Dificultad", blockchain.difficulty)
    with col_info3:
        is_valid, msg = blockchain.is_chain_valid()
        st.metric("✅ Estado", "VÁLIDA" if is_valid else "⚠️ INVÁLIDA")
    
    # Mostrar estado de validación
    if not is_valid:
        st.error(f"🚨 **CADENA COMPROMETIDA**: {msg}")
        st.warning("⚠️ ¡La modificación de bloques antiguos rompe la cadena!")
    
    st.markdown("---")
    
    # Mostrar cada bloque
    for i, block in enumerate(blockchain.chain):
        is_genesis = i == 0
        
        # Verificar si este bloque está conectado correctamente con el anterior
        is_linked = True
        if i > 0:
            is_linked = block.previous_hash == blockchain.chain[i-1].hash
        
        # Color según el estado
        if not is_linked:
            block_color = "🔴"
            status = "DESCONECTADO"
        elif is_genesis:
            block_color = "🟢"
            status = "GÉNESIS"
        else:
            block_color = "🔵"
            status = "VÁLIDO"
        
        with st.expander(f"{block_color} Bloque #{block.index} - {status}", expanded=(i >= len(blockchain.chain) - 1)):
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.write(f"**📊 Índice:** {block.index}")
                st.write(f"**🕐 Timestamp:** {block.timestamp}")
                st.write(f"**🔢 Nonce:** {block.nonce}")
                st.write(f"**💼 Transacciones:** {len(block.transactions)}")
            
            with col_b:
                st.write(f"**🔗 Hash:**")
                st.code(block.hash, language=None)
                st.write(f"**⬅️ Hash Anterior:**")
                st.code(block.previous_hash, language=None)
            
            # Mostrar transacciones
            st.write("**📝 Transacciones:**")
            for tx_idx, tx in enumerate(block.transactions):
                st.json(tx)
            
            # Botón de hackeo (solo para bloques no génesis)
            if not is_genesis:
                with st.form(f"hack_form_{i}"):
                    st.warning("⚠️ **Modo Hackeo**: Modifica este bloque para demostrar inmutabilidad")
                    hack_data = st.text_input("Nueva transacción fraudulenta", 
                                             value='{"sender": "Hacker", "recipient": "Hacker", "amount": 999999}')
                    hack_button = st.form_submit_button("🔓 Hackear este bloque")
                    
                    if hack_button:
                        try:
                            hack_tx = json.loads(hack_data)
                            blockchain.hack_block(i, hack_tx)
                            st.success("✅ Bloque modificado - ¡Observa cómo se rompe la cadena!")
                            time.sleep(1)
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error("❌ Error: Formato JSON inválido")
            
            # Indicador visual de la cadena
            if i < len(blockchain.chain) - 1:
                if is_linked:
                    st.markdown("### ⬇️ **Conectado a:**")
                else:
                    st.markdown("### ⚠️ **CADENA ROTA** ⚠️")

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
### 📚 Conceptos Clave de Blockchain

- **Hash**: Huella digital única de un bloque (SHA-256)
- **Previous Hash**: Enlaza cada bloque con el anterior, creando la cadena
- **Nonce**: Número usado en el proceso de minado para encontrar un hash válido
- **Mempool**: Transacciones pendientes esperando ser incluidas en un bloque
- **Inmutabilidad**: Modificar un bloque antiguo rompe todos los bloques siguientes
- **Prueba de Trabajo (PoW)**: Encontrar un hash que cumpla con la dificultad requerida

**🎯 Objetivo educativo**: Esta simulación demuestra cómo la blockchain garantiza la integridad 
de los datos mediante el encadenamiento criptográfico. Intenta modificar un bloque antiguo 
y observa cómo se invalida toda la cadena posterior.
""")
