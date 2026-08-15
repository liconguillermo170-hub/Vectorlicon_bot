import os
import io
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
import vtracer

TOKEN = os.environ.get("TELEGRAM_TOKEN", "8935003510:AAG7PaqJ2Ymgz3Ag8uk-VpmLiVTMMgmOMe4")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Envíame una imagen (como foto o documento) y la convertiré a vector SVG listo para trabajar."
    )

async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Vectorizando imagen...")
    
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
        
        image = Image.open(io.BytesIO(image_bytes))
        image.save(input_path)

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
            length_threshold=4.0,
            max_iterations=10,
            splice_threshold=45,
            path_precision=3
        )

        with open(output_path, 'rb') as svg_file:
            await update.message.reply_document(
                document=svg_file,
                filename="vector.svg",
                caption="¡Aquí tienes tu SVG vectorizado!"
            )
        
        await msg.delete()

        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

    except Exception as e:
        await msg.edit_text(f"Error procesando la imagen: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, process_image))
    application.run_polling()

if __name__ == "__main__":
    main()
