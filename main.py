import os
import io
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import vtracer

# Servidor Flask para responder a Render y evitar el timeout
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
    msg = await update.message.reply_text("⏳ Procesando imagen, por favor espera...")
    
    try:
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
        elif update.message.document:
            file_id = update.message.document.file_id
        else:
            await msg.edit_text("Envía una imagen válida.")
            return

        tg_file = await context.bot.get_file(file_id)
        image_bytes = await tg_file.download_as_bytearray()

        input_path = "input.png"
        output_path = "output.svg"

        with open(input_path, "wb") as f:
            f.write(image_bytes)

        # Configuración de vectorización con vtracer
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
                caption="¡Aquí tienes tu imagen vectorizada en SVG! 🎨"
            )

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Ocurrió un error al procesar la imagen: {str(e)}")

def main():
    # Inicia el servidor HTTP de Flask en un hilo secundario
    Thread(target=run_flask).start()

    # Inicia el bot de Telegram
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, process_image))
    
    application.run_polling()

if __name__ == '__main__':
    main()
