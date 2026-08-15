import os
import io
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import vtracer

# Servidor Flask para responder a Render y mantener activo el servicio
app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = "8935003510:AAG7PaqJ2Ymgz3Ag8uk-VpmLiVTMMgmOMe4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Envíame una imagen (como foto o archivo) para vectorizarla.")

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("--> Imagen recibida. Iniciando procesamiento...")
    msg = await update.message.reply_text("⏳ Procesando imagen, por favor espera...")
    
    try:
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
        elif update.message.document:
            file_id = update.message.document.file_id
        else:
            await msg.edit_text("Por favor, envía una imagen válida.")
            return

        tg_file = await context.bot.get_file(file_id)
        image_bytes = await tg_file.download_as_bytearray()

        # Redimensionar la imagen para no saturar la RAM de Render
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((800, 800))  # Ajusta el máximo a 800px manteniendo la proporción
        
        input_path = "input.png"
        output_path = "output.svg"
        img.save(input_path, format="PNG")

        # Vectorización con parámetros optimizados y livianos
        vtracer.convert_image_to_svg_py(
            input_path,
            output_path,
            colormode='color',
            hierarchical='stacked',
            mode='spline',
            filter_speckle=4,
            color_precision=6,
            layer_difference=16,
            corner_threshold=60,
            length_threshold=4,
            max_iterations=3,
            splice_threshold=45,
            path_precision=3
        )

        with open(output_path, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename="vector.svg",
                caption="¡Aquí tienes tu imagen vectorizada!"
            )
            
        print("--> ¡Vectorización completada y enviada!")
        await msg.delete()

    except Exception as e:
        print(f"Error: {e}")
        await msg.edit_text(f"Ocurrió un error al procesar la imagen: {e}")

async def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, process_image))
    
    # Inicialización manual limpia para evitar conflictos con el hilo de Flask
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Mantiene corriendo el evento de Telegram sin bloquear
    while True:
        await asyncio.sleep(3600)

def main():
    # Inicia el servidor web en segundo plano
    Thread(target=run_flask, daemon=True).start()
    
    # Ejecuta el bot con asyncio
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()


