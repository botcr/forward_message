import telebot
from telebot import types
from config import *
import sqlite3
from loguru import logger
import threading
import time

# логи
logger.add("debug.log", format="{time} {level} {message}", level="DEBUG", rotation="1 MB", compression="zip")


admins = (ADMIN_ID1, ADMIN_ID2)#ADMIN_ID3
n = None
bot = telebot.TeleBot(BOT_TOKEN)
try:
    with sqlite3.connect('data.db') as data:
        cur = data.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS data (
            Number INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            message_chat_id INTEGER,
            message_message_id INTEGER,
            admin1_message_message_id INTEGER,
            admin2_message_message_id INTEGER,
            admin3_message_message_id INTEGER
            )""")

    with sqlite3.connect('data.db') as data:
        cur = data.cursor()
        #channel
        # 1 - open channel 
        # 2 - close channel
        cur.execute("""CREATE TABLE IF NOT EXISTS users (
            message_chat_id INTEGER,
            channel TEXT
            )""")
    
    # def work_control():
    #   while True:
    #     bot.send_message(-690162338, 'nalog_bot')
    #     time.sleep(60)
    # t20 = threading.Thread(name='work_control',
    #                   target=work_control)
    # t20.start()
    @bot.message_handler(commands=['start'])
    def greeting(message):
        # узнаем на какой канал пересылать
        try:
            ch = int(message.text.split(' ')[1])
        except Exception:
            ch = None
        if ch == 2:
            bot.send_message(message.chat.id, "Здравствуйте, напишите свой вопрос на закрытый канал uprav_nalog")
        else:
            bot.send_message(message.chat.id, "Здравствуйте, напишите свой вопрос.")
        if ch == 1 or ch == 2:
            #Записываем или обновляем данные пользователя
            try:
                with sqlite3.connect('data.db') as data:
                    curs = data.cursor()
                    curs.execute("""SELECT channel FROM users WHERE message_chat_id == ?""", (message.chat.id,))
                    n1 = curs.fetchone()
                    n = n1[0]
                    curs.execute(
                        """UPDATE users SET channel = ? WHERE message_chat_id = ?""",
                        (ch, message.chat.id))
            except Exception:
                with sqlite3.connect('data.db') as data:
                    curs = data.cursor()
                    curs.execute("INSERT INTO users (message_chat_id, channel) VALUES (?, ?)",
                                 (message.chat.id, ch))




    @bot.message_handler(content_types=["text", "photo", 'sticker', "document"])
    def forwarding(message):
        global n
        with sqlite3.connect('data.db') as data:
            curs = data.cursor()
            curs.execute("INSERT INTO data (message_chat_id, message_message_id) VALUES (?, ?)", (message.chat.id, message.message_id))
            curs.execute("""SELECT Number FROM data ORDER BY Number DESC LIMIT 1""")
            n1 = curs.fetchone()
            try:
                curs.execute("""SELECT channel FROM users WHERE message_chat_id = (?);""", (message.chat.id,))
                ch1 = curs.fetchone()
                ch = int(ch1[0])
            except Exception:
                ch = None
        n = n1[0]
        markup = types.InlineKeyboardMarkup()
        but1 = types.InlineKeyboardButton(text='Отправить', callback_data=n)
        but2 = types.InlineKeyboardButton(text='Удалить', callback_data=-n)
        markup.add(but1, but2)


        for a in admins:
            bot.forward_message(a, message.chat.id, message.message_id)
        if ch == 2:
            send1 = bot.send_message(ADMIN_ID1, f'Закрытый канал\n№{str(n)}', reply_markup=markup)
            send2 = bot.send_message(ADMIN_ID2, f'Закрытый канал\n№{str(n)}', reply_markup=markup)
           # send3 = bot.send_message(ADMIN_ID3, f'Закрытый канал\n№{str(n)}', reply_markup=markup)
        else:
            send1 = bot.send_message(ADMIN_ID1, f'Открытый канал\n№{str(n)}', reply_markup=markup)
            send2 = bot.send_message(ADMIN_ID2, f'Открытый канал\n№{str(n)}', reply_markup=markup)
          #  send3 = bot.send_message(ADMIN_ID3, f'Открытый канал\n№{str(n)}', reply_markup=markup)

        with sqlite3.connect('data.db') as data:
            curs = data.cursor()
            curs.execute("""UPDATE data SET admin1_message_message_id =?, admin2_message_message_id = ? WHERE Number = ?""", 
                         (send1.message_id, send2.message_id, n)) #send3.message_id

        bot.send_message(message.chat.id, 'Ваш вопрос отправлен на модерацию')

    @bot.callback_query_handler(func=lambda callback: callback.data)
    def callback(callback):
        with sqlite3.connect('data.db') as data:
            curs = data.cursor()
            curs.execute("""SELECT * FROM data WHERE Number = (?);""", (abs(int(callback.data)),))
            mess_data = curs.fetchone()
            try:
                curs.execute("""SELECT channel FROM users WHERE message_chat_id = (?);""", (mess_data[1],))
                ch1 = curs.fetchone()
                ch = int(ch1[0])
            except Exception:
                ch = None


        if callback.data >= '1' and ch == 2:
            bot.forward_message(channel2, mess_data[1], mess_data[2])
            bot.send_message(mess_data[1], f'Ваш вопрос одобрен')
        elif callback.data >= '1' and ch != 2:
            bot.forward_message(channel1, mess_data[1], mess_data[2])
            bot.send_message(mess_data[1], f'Ваш вопрос одобрен')
        elif callback.data < '0':
            bot.send_message(mess_data[1], f'Ваш вопрос отклонен')


        bot.edit_message_reply_markup(chat_id=ADMIN_ID1, message_id=mess_data[3])
        bot.edit_message_reply_markup(chat_id=ADMIN_ID2, message_id=mess_data[4])
       # bot.edit_message_reply_markup(chat_id=ADMIN_ID3, message_id=mess_data[5])
except Exception:
    logger.exception('-')

    bot.infinity_polling()

