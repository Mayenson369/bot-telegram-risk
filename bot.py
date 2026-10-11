import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Token limpio y sin espacios

API_URL = "http://127.0.0.1:8000/calcular"
TOKEN = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Bienvenido al Bot de Gestión de Riesgo SaaS! 🚀\n\n"
        "Para calcular tus niveles de riesgo y operación, usa el comando:\n"
        "`/calcular [capital] [riesgo%] [entrada] [stop_loss] [api_key]`\n\n"
        "Ejemplo:\n"
        "/calcular 1000 2 50000 49000 TEST_KEY_123",
        parse_mode="Markdown"
    )

async def calcular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 5:
            await update.message.reply_text(
                "❌ Faltan datos. El formato correcto es:\n"
                "`/calcular [capital] [riesgo%] [entrada] [stop_loss] [api_key]`",
                parse_mode="Markdown"
            )
            return

        capital = float(args[0])
        riesgo = float(args[1])
        entrada = float(args[2])
        stop_loss = float(args[3])
        api_key = args[4]

        # Enviamos la API Key en la cabecera de seguridad exigida por tu FastAPI
        headers = {"access_token": api_key}
        payload = {
            "capital_total": capital,
            "porcentaje_riesgo": riesgo,
            "precio_entrada": entrada,
            "precio_stop_loss": stop_loss
        }

        # Conexión directa a tu servidor local en FastAPI
        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json()
            mensaje = (
                f"✅ **Cálculo de Riesgo Exitoso**\n\n"
                f"📊 **Operación:** {data['operacion']}\n"
                f"💵 **Riesgo Máximo:** ${data['riesgo_maximo_usdt']} USDT\n"
                f"📦 **Tamaño de Posición:** ${data['tamano_posicion_sugerido_usdt']} USDT\n"
                f"🪙 **Cantidad a Operar:** {data['cantidad_a_operar']}\n"
                f"🎯 **Take Profit 1 (R:B 1:2):** ${data['take_profit_1_r_b_1_2']}\n"
                f"🎯 **Take Profit 2 (R:B 1:3):** ${data['take_profit_2_r_b_1_3']}"
            )
            await update.message.reply_text(mensaje, parse_mode="Markdown")
        else:
            error_detail = response.json().get("detail", "Error de autenticación")
            await update.message.reply_text(f"❌ **Acceso Denegado:** {error_detail}", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ocurrió un error procesando los datos: {str(e)}")

if __name__ == '__main__':
    print(f"--> TOKEN QUE ESTOY LEYENDO: {TOKEN}")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("calcular", calcular))
    print("🤖 Bot de Telegram encendido y escuchando comandos!")
    app.run_polling()
