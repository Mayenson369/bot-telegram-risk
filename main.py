from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
import sqlite3

app = FastAPI(
    title="SaaS Risk Management API con Licenciamiento",
    description="Motor seguro con validación de API Key en base de datos contra piratería.",
    version="2.0.0"
)

# Configuración de seguridad: la API Key se enviará en las cabeceras HTTP con el nombre 'access_token'
API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Inicializar Base de Datos SQLite local de forma automática
def init_db():
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenses (
            api_key TEXT PRIMARY KEY,
            client_name TEXT,
            active INTEGER
        )
    """)
    # Insertar una llave de prueba por defecto para que puedas probarlo de inmediato
    cursor.execute("INSERT OR IGNORE INTO licenses (api_key, client_name, active) VALUES (?, ?, ?)",
                   ("TEST_KEY_123", "Mayenson (Cliente Demo)", 1))
    conn.commit()
    conn.close()

# Creamos la base de datos al arrancar el servidor
init_db()

# Función de seguridad que valida si la API Key existe y está activa (active = 1)
def verificar_api_key(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. No se proporcionó ninguna API Key."
        )

    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT active FROM licenses WHERE api_key = ?", (api_key,))
    result = cursor.fetchone()
    conn.close()

    if not result or result[0] != 1:
        raise HTTPException(
            status_code=403,
            detail="API Key inválida o suscripción vencida / inactiva."
        )
    return api_key

class RiskRequest(BaseModel):
    capital_total: float
    porcentaje_riesgo: float
    precio_entrada: float
    precio_stop_loss: float

@app.get("/")
def home():
    return {"mensaje": "¡El SaaS está activo y protegido con sistema de licencias!"}

@app.post("/calcular")
def calcular_riesgo(data: RiskRequest, token: str = Depends(verificar_api_key)):
    # Nota: El parámetro 'token: str = Depends(verificar_api_key)' obliga al servidor
    # a verificar la licencia antes de ejecutar los cálculos matemáticos.

    if data.precio_entrada == data.precio_stop_loss:
        raise HTTPException(status_code=400, detail="El Stop Loss no puede ser igual al precio de entrada.")

    riesgo_usd = data.capital_total * (data.porcentaje_riesgo / 100)
    distancia_sl_pct = abs(data.precio_entrada - data.precio_stop_loss) / data.precio_entrada

    if distancia_sl_pct == 0:
        raise HTTPException(status_code=400, detail="La distancia del Stop Loss no es válida.")

    tamano_posicion_usd = riesgo_usd / distancia_sl_pct
    cantidad_activos = tamano_posicion_usd / data.precio_entrada

    es_long = data.precio_entrada > data.precio_stop_loss

    if es_long:
        tp_1 = data.precio_entrada + (abs(data.precio_entrada - data.precio_stop_loss) * 2)
        tp_2 = data.precio_entrada + (abs(data.precio_entrada - data.precio_stop_loss) * 3)
        operacion = "LONG (Compra)"
    else:
        tp_1 = data.precio_entrada - (abs(data.precio_stop_loss - data.precio_entrada) * 2)
        tp_2 = data.precio_entrada - (abs(data.precio_stop_loss - data.precio_entrada) * 3)
        operacion = "SHORT (Venta)"

    return {
        "estado": "exito",
        "operacion": operacion,
        "riesgo_maximo_usdt": round(riesgo_usd, 2),
        "tamano_posicion_sugerido_usdt": round(tamano_posicion_usd, 2),
        "cantidad_a_operar": round(cantidad_activos, 4),
        "take_profit_1_r_b_1_2": round(tp_1, 4),
        "take_profit_2_r_b_1_3": round(tp_2, 4)
    }