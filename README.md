# Blockchain Simulator 🔗⛏️

Este repositorio es con fines educativos. Se genera un simulador interactivo de blockchain usando Python y Streamlit para entender su funcionamiento y demostrarlo en presentaciones de estudio.

## 🎯 Características

- **Crear Transacciones**: Agrega transacciones entre remitentes y destinatarios
- **Mempool Visible**: Visualiza todas las transacciones pendientes antes de ser minadas
- **Minado con Animación**: Observa en tiempo real el proceso de minado (nonce y hash)
- **Cadena Encadenada**: Visualiza cómo cada bloque está enlazado con el anterior mediante hashes
- **Validación de Bloques**: Comprueba la integridad de toda la blockchain
- **Demostración de Inmutabilidad**: Hackea un bloque antiguo y observa cómo se rompe la cadena completa

## 🏗️ Arquitectura

### Block (Bloque)
Cada bloque contiene:
- **index**: Posición en la cadena
- **timestamp**: Momento de creación
- **transactions**: Lista de transacciones
- **previous_hash**: Hash del bloque anterior (crea el encadenamiento)
- **nonce**: Número usado en la prueba de trabajo
- **hash**: Hash SHA-256 del bloque

### Blockchain (Cadena de Bloques)
La blockchain incluye:
- **chain**: Lista de bloques encadenados
- **mempool**: Transacciones pendientes
- **difficulty**: Nivel de dificultad para el minado (número de ceros iniciales en el hash)
- **Validación**: Verifica la integridad de toda la cadena

## 🚀 Instalación y Ejecución

### Requisitos Previos
- Python 3.8 o superior
- pip

### Pasos

1. **Clonar el repositorio**
```bash
git clone https://github.com/RicardBro/Blockchain.git
cd Blockchain
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Ejecutar la aplicación**
```bash
streamlit run app.py
```

4. **Abrir en el navegador**
La aplicación se abrirá automáticamente en `http://localhost:8501`

## 📖 Cómo Usar

### 1. Agregar Transacciones
- En el panel izquierdo, completa el formulario con:
  - **Remitente**: Quien envía (ej: Alice)
  - **Destinatario**: Quien recibe (ej: Bob)
  - **Cantidad**: Monto a transferir
- Haz clic en "➕ Agregar a Mempool"

### 2. Ver el Mempool
- Las transacciones pendientes aparecen en la sección "📋 Mempool"
- Puedes agregar múltiples transacciones antes de minar

### 3. Minar un Bloque
- Haz clic en "⛏️ Minar Bloque" (solo disponible si hay transacciones pendientes)
- Observa la animación en tiempo real:
  - El **nonce** aumenta
  - El **hash** cambia en cada intento
  - El proceso continúa hasta encontrar un hash que cumpla con la dificultad

### 4. Visualizar la Blockchain
- En el panel derecho verás todos los bloques de la cadena
- Cada bloque muestra:
  - Su índice y timestamp
  - Hash actual y hash del bloque anterior
  - Todas las transacciones incluidas
  - Estado de validación (conectado o desconectado)

### 5. Demostrar Inmutabilidad (¡CRÍTICO!)
- En cualquier bloque (excepto el génesis), usa el formulario de "Modo Hackeo"
- Agrega una transacción fraudulenta
- Haz clic en "🔓 Hackear este bloque"
- **Observa cómo se rompe la cadena**: El bloque modificado ya no conecta correctamente con el siguiente
- El sistema detecta y muestra "⚠️ CADENA COMPROMETIDA"

## 🎓 Conceptos Educativos

### Hash (SHA-256)
Función criptográfica que genera una "huella digital" única para cada bloque. Cualquier cambio en los datos del bloque produce un hash completamente diferente.

### Encadenamiento
Cada bloque contiene el hash del bloque anterior, creando una cadena enlazada. Si modificas un bloque antiguo, su hash cambia, rompiendo el enlace con el siguiente bloque.

### Prueba de Trabajo (Proof of Work)
Para agregar un bloque, debes encontrar un nonce que produzca un hash con cierto número de ceros al inicio. Esto requiere muchos intentos (trabajo computacional).

### Inmutabilidad
Una vez que un bloque es agregado y otros bloques se construyen encima, modificarlo es prácticamente imposible porque:
1. Cambiar el bloque cambia su hash
2. Esto rompe el enlace con el siguiente bloque
3. Deberías re-minar todos los bloques siguientes
4. Mientras tanto, otros nodos ya tienen la cadena correcta

## 🔍 Casos de Uso Educativo

1. **Entender el minado**: Observa cómo el nonce se incrementa hasta encontrar un hash válido
2. **Visualizar el encadenamiento**: Ve cómo cada bloque apunta al anterior mediante hashes
3. **Demostrar seguridad**: Modifica un bloque antiguo y muestra cómo invalida la cadena
4. **Explicar transacciones**: Muestra cómo las transacciones se agrupan en bloques
5. **Mempool en acción**: Demuestra cómo las transacciones esperan antes de ser confirmadas

## 🛠️ Tecnologías Utilizadas

- **Python 3**: Lenguaje de programación
- **Streamlit**: Framework para crear la interfaz web interactiva
- **hashlib**: Biblioteca para el hash SHA-256
- **JSON**: Formato para estructurar transacciones

## 📝 Estructura del Proyecto

```
Blockchain/
├── app.py              # Aplicación Streamlit (interfaz visual)
├── blockchain.py       # Clases Block y Blockchain (lógica core)
├── requirements.txt    # Dependencias Python
└── README.md          # Documentación
```

## 🤝 Contribuciones

Este es un proyecto educativo. Las contribuciones para mejorar la didáctica son bienvenidas.

## 📄 Licencia

Proyecto educativo de código abierto.

---

**Creado con fines educativos para entender el funcionamiento de blockchain** 🎓⛓️
