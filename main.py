import os
import time
from datetime import datetime
from telegram.request import HTTPXRequest
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler,
                          ConversationHandler)
import pandas as pd
from google.oauth2 import service_account
from google.cloud import vision
import re
import requests
import psycopg2
import itertools
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

TOKEN = "TELEGRAM BOT TOKEN"    # https://t.me/techwithsibro_bot

READ_IMAGE = 0
GEMINI_AI = 0

# for GEMINI AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model
# See https://ai.google.dev/api/python/google/generativeai/GenerativeModel
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

system_instruction = f"""
Kamu adalah asisten dari IMAM SIBRO MUHLISI. Namamu adalah ASISTEN MASBRO. 
Gunakan bahasa Indonesia dengan baik dan benar. Tugasmu adalah untuk membantu orang-orang dalam kesehariannya. 
Utamakan berbahasa Indonesia yang baik dan benar. User dapat menghubungi Imam Sibro Muhlisi di :
 1. LinkedIn https://www.linkedin.com/in/imam-sibro-muhlisi/
 2. Telegram https://t.me/imamsmuh
 3. Youtube Channel https://www.youtube.com/@techwithsibro
User dapat meminta bantuan kepada Imam Sibro Muhlisi jika ingin membuat bot seperti kamu, membuat tools, dan lainnya.
Untuk lebih jelasnya, user dapat menghubungi Imam Sibro Muhlisi secara langsung.

Selalu gunakan Bahasa Indonesia, kecuali jika user menyapa kamu dengan bahasa inggris,
maka gunakanlah bahasa Inggris.
 
Perlu kamu ketahui tanggal hari ini adalah 
{datetime.now().strftime("%Y-%m-%d")}. Sekarang adalah jam {datetime.now().strftime("%H%M%S")}
"""

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction=system_instruction,
)

# for database
dbhost = "localhost"    # your db host
dbase = "db_sibro"      # your database name
dbuser = "sibro"        # your database username
dbpass = "12345"        # your database password
batas_history = 30      # chat history to keep 


def insert_to_db_chat_session(chat_id, role, parts, timestamp):
    schema_name = 'telebot'         # your schema
    table_name = 'chat_session'     # your table name

    insert_string = f"""
    INSERT INTO {schema_name}.{table_name}(chat_id, role, parts, timestamp)
    VALUES ('{chat_id}', '{role}', '{parts}', '{timestamp}')
    """

    # connect db
    conn = psycopg2.connect(host=dbhost, database=dbase, user=dbuser, password=dbpass)
    cursor = conn.cursor()

    # execute query
    cursor.execute(insert_string)

    # apply command
    conn.commit()

    # close connection
    conn.close()
    

def delete_db_records(chat_id):
    delete_string = f"""
    DELETE FROM telebot.chat_session
    WHERE chat_id = '{chat_id}' 
    AND timestamp = (SELECT MIN(timestamp) from telebot.chat_session WHERE chat_id = '{chat_id}')
    """

    # connect db
    conn = psycopg2.connect(host=dbhost, database=dbase, user=dbuser, password=dbpass)
    cursor = conn.cursor()

    # execute query
    cursor.execute(delete_string)

    # apply command
    conn.commit()

    # cek kembali apakah record lebih dari 20
    query_string = f"""
    SELECT
        COUNT(*)
    FROM
        telebot.chat_session
    WHERE
        chat_id = '{chat_id}'
    """

    # connect to database
    conn = psycopg2.connect(host=dbhost, database=dbase, user=dbuser, password=dbpass)

    # read query by pandas
    df = pd.read_sql_query(query_string, conn)
    if df['count'][0] >= batas_history:
        delete_db_records(chat_id=chat_id)

    # close connection
    conn.close()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text_diterima = msg.text.strip()
    full_name = msg.from_user.full_name
    user_id = msg.from_user.id
    user_link = msg.from_user.link
    chat_id = msg.chat_id
    group_name = msg.chat.title

    await msg.reply_text(f'Hi {full_name}.\nSelamat datang di bot @techwithsibro.\n'
                                           f'Gunakan menu di kiri bawah untuk menggunakan bot ini.\n\n'
                                           f'Bot by = Imam Sibro Muhlisi\n'
                                           f'YT = https://www.youtube.com/@techwithsibro\n'
                                           f'Telegram = https://t.me/imamsmuh')
    return ConversationHandler.END


async def read_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    # text_diterima = msg.text.strip()
    full_name = msg.from_user.full_name
    user_id = msg.from_user.id
    user_link = msg.from_user.link
    chat_id = msg.chat_id
    group_name = msg.chat.title

    try:        # untuk typenya yang document / attachment
        file_name_ori = update.message.document.file_name
        mime_type = update.message.document.mime_type
        file_id = update.message.document.file_id
    except:     # untuk image yang di compressed / photo
        file_name_ori = None
        mime_type = None
        file_id = update.message.photo[-1].file_id

    # filter jika itu adalah attachment, maka mime-type nya harus image/
    if mime_type is not None:
        if 'image/' not in mime_type.lower():
            await msg.reply_text('Mohon kirim hanya file gambar. Kirim kembali gambar yang benar atau klik:\n'
                                 '/reset\n\nuntuk kembali ke menu awal.')
            return READ_IMAGE

    # print('buat folder download jika tidak ada...')
    if not os.path.exists("download"):
        os.makedirs("download")

    # print('simpan file di folder download...')
    if mime_type is None:
        path_file = f"download/gambar_tele.jpg"
    else:
        path_file = f"download/gambar_tele{file_name_ori[file_name_ori.find('.'):]}"

    # download attachment / photo yang dikirim
    new_file = await context.bot.getFile(file_id)
    await new_file.download_to_drive(custom_path=path_file)

    # create vision client first
    credentials = service_account.Credentials.from_service_account_file('client_id_bro_google_vision.json')
    client = vision.ImageAnnotatorClient(credentials=credentials)

    # open image
    content = open(path_file, 'rb').read()

    # read text on image
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    text = response.text_annotations[0].description.strip()

    if text is not None:
        await msg.reply_text(text=text)
        return ConversationHandler.END
    else:
        await msg.reply_text('Gambar mungkin tidak mengandung text, atau text tidak terbaca. Silakan ulangi kembali.\n'
                             '\nGunakan menu /reset untuk kembali ke menu awal.')
        return READ_IMAGE


async def read_image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text_diterima = msg.text.strip()
    full_name = msg.from_user.full_name
    user_id = msg.from_user.id
    user_link = msg.from_user.link
    chat_id = msg.chat_id
    group_name = msg.chat.title

    # end conversation if exist
    ConversationHandler.END

    await msg.reply_text(f'Hi {full_name}, coba berikan saya gambar untuk dibaca.')
    return READ_IMAGE


async def gemini_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text_diterima = msg.text.strip()
    text_diterima_plain = msg.text
    full_name = msg.from_user.full_name
    user_id = msg.from_user.id
    user_link = msg.from_user.link
    chat_id = msg.chat_id
    group_name = msg.chat.title

    if text_diterima == '/reset':
        await msg.reply_text(f"Terima kasih {full_name}. Silakan lihat kembali menu di kiri bawah "
                             f"untuk menggunakan bot ini.")
        return ConversationHandler.END

    timestamp = time.time()
    timestamp_sql = datetime.fromtimestamp(timestamp)

    history = []

    # query string untuk chat_id untuk session per user
    sql_query = f"""
    select
        *
    from
        telebot.chat_session
    where
        chat_id = '{chat_id}'
    """

    # connect to database
    conn = psycopg2.connect(host=dbhost, database=dbase, user=dbuser, password=dbpass)

    # read query by pandas
    df = pd.read_sql_query(sql_query, conn)

    if not df.empty:
        df_user = df[df['role'] == 'user']
        df_model = df[df['role'] == 'model']
        list_user_parts = df_user['parts'].tolist()
        list_model_parts = df_model['parts'].tolist()

        history = []

        for (user_parts, model_parts) in itertools.zip_longest(list_user_parts, list_model_parts):
            history.append({"role": "user", "parts": [user_parts]})
            history.append({"role": "model", "parts": [model_parts]})

        if len(history) >= batas_history:
            delete_db_records(chat_id=chat_id)

    chat_session = model.start_chat(history=history)
    response = chat_session.send_message(text_diterima_plain)
    model_response = response.text

    # send response to user
    await msg.reply_text(model_response)

    history.append({"role": "user", "parts": [text_diterima_plain]})
    history.append({"role": "model", "parts": [model_response]})

    # insert to db
    insert_to_db_chat_session(chat_id=chat_id, role='user', parts=text_diterima_plain, timestamp=timestamp_sql)   # for user
    insert_to_db_chat_session(chat_id=chat_id, role='model', parts=model_response, timestamp=timestamp_sql)       # for model


async def gemini_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text_diterima = msg.text.strip()
    full_name = msg.from_user.full_name
    user_id = msg.from_user.id
    user_link = msg.from_user.link
    chat_id = msg.chat_id
    group_name = msg.chat.title

    # end conversation if exist
    ConversationHandler.END

    await msg.reply_text(f'Hi {full_name}, apa yang dapat saya bantu hari ini?')
    return GEMINI_AI


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text_diterima = msg.text.strip()
    full_name = msg.from_user.full_name
    user_id = msg.from_user.id
    user_link = msg.from_user.link
    chat_id = msg.chat_id
    group_name = msg.chat.title

    await msg.reply_text(f"Terima kasih {full_name}. Silakan lihat kembali menu di kiri bawah "
                         f"untuk menggunakan bot ini.")

    return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update : {update}\nError : {context.error}\nWaktu Error : {datetime.now()}')
    if update.message:
        full_name = update.message.from_user.full_name
        return await update.message.reply_text(f'Mohon maaf {full_name}, telah terjadi kesalahan. '
                                               f'Silakan dicoba kembali beberapa saat lagi atau hubungi developer.')


if __name__ == '__main__':
    print('Starting...')
    app = Application.builder().token(TOKEN).build()

    # Conversation Handler
    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler_ocr = ConversationHandler(
        entry_points=[CommandHandler("read_image", read_image_command)],
        states={
            READ_IMAGE: [
                MessageHandler(filters.PHOTO, read_image),
                MessageHandler(filters.ATTACHMENT, read_image)
            ]
        },
        fallbacks=[CommandHandler('reset', reset)],
    )

    conv_handler_gemini_ai = ConversationHandler(
        entry_points=[CommandHandler("gemini_ai", gemini_ai_command)],
        states={
            GEMINI_AI: [
                MessageHandler(filters.TEXT, gemini_ai)
            ]
        },
        fallbacks=[CommandHandler('reset', reset)],
    )

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(conv_handler_ocr)
    app.add_handler(conv_handler_gemini_ai)

    # error handler
    app.add_error_handler(error)

    # Pooling
    print('Pooling...')
    app.run_polling()