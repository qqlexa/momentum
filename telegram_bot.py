import os

import sqlite3
import logging

from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery  # Message
from pyrogram.handlers import MessageHandler, CallbackQueryHandler

print(os.path.abspath(__file__))

try:
    TOKEN = os.environ['TOKEN_TG']
    api_hash = os.environ['API_HASH']
    api_id = os.environ['API_ID']
except:
    with open("TOKEN_TG") as f:
        TOKEN = f.read()

con = sqlite3.connect("main.db")
cur = con.cursor()

table_name = "info"
try:
    cur.execute(f"select * from {table_name}")
except:
    # if does not exist
    logging.info(f"Created new `{table_name}` table")
    cur.execute(f"""CREATE TABLE {table_name} (
        "tg_id" INTEGER, 
        "name" TEXT,
        "age" INTEGER,
        "sex" TEXT,
        PRIMARY KEY("tg_id")
    );""")
else:
    logging.info(f"There is `{table_name}` table")

table_name = "history"
try:
    cur.execute(f"select * from {table_name}")
except:
    # if does not exist
    logging.info(f"Created new `{table_name}` table")
    cur.execute(f"""CREATE TABLE {table_name} (
        "tg_id" INTEGER, 
        "event" TEXT,
        "time" TEXT
    );""")
else:
    logging.info(f"There is `{table_name}` table")

app = Client(
    "my_bot",
    bot_token=str(TOKEN),
    api_hash=str(api_hash),
    api_id=str(api_id)
)

active_users = {}
"""
active_users = {
     1:                   # id tg
     {"handler": [1],     # currently handler
     "name": "Alex",      # name of user
     "age": "1",          # age of user
     "sex": "male"},      # sex of user

     2:                   # id tg
     {"handler": [1, 2],  # currently handler
     "name": "Lauren",    # name of user
     "age": "2",          # age of user
     "sex": "female"},    # sex of user
 }
 """


def delete_handlers(telegram_id):
    if telegram_id in active_users.keys():
        while len(active_users[telegram_id]["handler"]):
            handler = active_users[telegram_id]["handler"].pop()
            app.remove_handler(handler[0])


def append_history(message, event, telegram_id=0):
    """
        Доповнення події до таблиці подій 'history'
    """
    if telegram_id == 0:
        telegram_id = message.from_user.id

    currently_time = datetime.now()
    currently_time_str = currently_time.strftime("%d-%b-%Y %H:%M")
    try:
        request = f"""insert into {"history"} values (
                    {telegram_id}, 
                    '{event}', 
                    '{currently_time_str}')
                    """
        print(request)
        cur.execute(request)
    except:
        logging.warning('This is error in the append_history()')
    else:
        con.commit()


async def save_information(message, telegram_id=0):
    """
        Збереження інформації про користувача
    """
    if telegram_id == 0:
        telegram_id = message.from_user.id

    # Перевіряємо чи усі дані були заповнені
    if active_users[telegram_id]["name"] and active_users[telegram_id]["age"] and active_users[telegram_id]["sex"]:
        try:
            local_table_name = 'info'
            if not await is_exist_person(telegram_id):
                # Якщо минулого запису користувача не існує - створюємо новий запис про нього
                cur.execute(f"""insert into {local_table_name} values ({telegram_id}, 
                            '{active_users[telegram_id]["name"]}',
                            '{active_users[telegram_id]["age"]}',
                            '{active_users[telegram_id]["sex"]}')
                        """)
            else:
                # Якщо минулий запис користувача існує - редагуємо попередній запис про нього
                cur.execute(f"""update '{local_table_name}' set 
                            'name'='{active_users[telegram_id]["name"]}',
                            'age'='{active_users[telegram_id]["age"]}',
                            'sex'='{active_users[telegram_id]["sex"]}'
                            where tg_id={telegram_id}
                            """)
            con.commit()
        except:
            await message.reply_text("Не вдалося зберегти інформацію про Вас. Спробуйте знову.")
        else:
            # Створюємо ReplyKeyboardMarkup з кнопками 'Інформація про мене' та 'Налаштування'
            await create_menu(app, message)
    else:
        await message.reply_text("Виявлена проблема у введених даних. Спробуйте знову.")

    # Видаляємо користувача та інформацію про нього зі словника
    del active_users[telegram_id]


async def get_person(telegram_id: int):
    """
    Виконуємо пошук користувача у базі даних і повертаємо результат.
    :param telegram_id: Телеграм ID користувача.
    :return: True, якщо був знайдений. False, якщо не був знайдений.
    """
    try:
        cur.execute(f"""select * from {"info"} where tg_id={telegram_id}""")
        data = cur.fetchall()
    except:
        logging.warning('This is error in the get_person()')
    else:
        return data


async def is_exist_person(telegram_id: int) -> bool:
    """
    Виконуємо пошук користувача у базі даних і повертаємо статус знаходження запису.
    :param telegram_id: Телеграм ID користувача.
    :return: True, якщо був знайдений. False, якщо не був знайдений.
    """
    return True if len(await get_person(telegram_id)) else False


async def get_name(client, message):
    """
        Отримання імені

        Відсутнє обмеження на знаки/цифри і т.д., щоб обмежити це -
        при додаванні хендлера get_name можна додати filters.regex("^[a-zA-Z]+$")
    """

    # Збережемо вибір статі в історію активності
    append_history(message, "Get name")

    # Name: 2-20 chars
    if 2 <= len(message.text) <= 20:
        await message.reply_text(f'Окей, {message.text}.')
        # Зберігаємо попереднє значення імені користувача
        previous_name = active_users[message.from_user.id]["name"]

        # Записуємо ім'я в словник під ключем телеграм айді користувача
        active_users[message.from_user.id]["name"] = message.text

        # Видаляємо попередній handler на отримання імені
        delete_handlers(message.from_user.id)

        # Якщо під ключем age вже було значення, це значить handler був доданий у change_age()
        if previous_name:
            # Зберігаємо інформацію про користувача
            await save_information(message)
        else:
            await message.reply_text("Введіть Ваш вік")

            # Створюємо новий handler на отримання віку
            active_users[message.from_user.id]["handler"].append(
                app.add_handler(
                    MessageHandler(get_age,
                                   filters.regex("^[0-9]+$") & filters.user(message.from_user.id) & filters.private))
            )
    else:
        await message.reply_text("Ім'я повинно містити 2-20 літер")


async def get_age(client, message):
    """
        Отримання віку

        Присутній регулярний вираз з обмеженням на цифри, щоб прибрати це -
        при додаванні хендлера get_age можна забрати filters.regex("^[0-9]+$")
    """
    # Збережемо введення віку в історію активності
    append_history(message, "Get age")

    # Попри обмеження / необмеження вхідного повідомлення
    # використовується структура try except для обробки перетворення до типу int
    try:
        age = int(message.text)
    except:
        await message.reply_text(f'Спробуйте знову, {message.text}.')
    else:
        # Зберігаємо попереднє значення віку користувача
        previous_age = active_users[message.from_user.id]["age"]
        # Записуємо вік в словник під ключем телеграм айді користувача
        active_users[message.from_user.id]["age"] = age

        await message.reply_text(f'Окей, Вам {message.text}.')

        # Видаляємо попередній handler на отримання віку
        delete_handlers(message.from_user.id)

        # Якщо під ключем age вже було значення, це значить handler був доданий у change_age()
        if previous_age:
            # Зберігаємо інформацію про користувача
            await save_information(message)
        else:
            # Інакше продовжуємо введення даних
            await message.reply_text("Виберіть Вашу стать",
                                     reply_markup=InlineKeyboardMarkup(
                                         [
                                             [  # Перший рядок
                                                 InlineKeyboardButton(
                                                     "Чоловік",
                                                     callback_data="male"
                                                 ),
                                             ],
                                             [  # Другий рядок
                                                 InlineKeyboardButton(
                                                     "Жінка",
                                                     callback_data="female"
                                                 ),
                                             ]
                                         ]
                                     )
                                     )

            # Створюємо новий handler на отримання статі
            active_users[message.from_user.id]["handler"].append(
                app.add_handler(CallbackQueryHandler(get_sex, filters.user(message.from_user.id)))
            )


async def get_sex(client, callback_query):
    """
        Отримання статі
    """
    # Якщо не прийшло через Message
    if isinstance(callback_query, CallbackQuery):
        message = callback_query.message

        telegram_id = callback_query.from_user.id
        data = callback_query.data

        # Стираємо markup на попередньому повідомленні
        await message.edit_reply_markup()
    else:
        # isinstance(callback_query, Message):
        message = callback_query

        telegram_id = message.from_user.id
        data = message.text

    # Збережемо вибір статі в історію активності
    append_history(message, "Get sex", telegram_id)

    await message.reply_text(f'Ви {"👨" if data == "male" or data == "Чоловік 👨" else "👩"}.')

    # Записуємо стать в словник під ключем телеграм айді користувача
    active_users[telegram_id]["sex"] = "male" if data == "male" or data == "Чоловік 👨" else "female"

    # Видаляємо попередній handler на отримання статі
    delete_handlers(telegram_id)

    # Зберігаємо інформацію про користувача
    await save_information(message, telegram_id)


@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    """
        Анкетування
    """

    # Збережемо нажаття на 'Start' в історію активності
    append_history(message, "Start")

    if message.from_user.id in active_users.keys():
        # Видаляємо існуючий handler
        delete_handlers(message.from_user.id)

        del active_users[message.from_user.id]

    await message.reply_text("Введіть Ваше ім'я")
    # Створюємо пустий словник за ключем телеграм айді користувача
    active_users[message.from_user.id] = {"handler": [],
                                          "name": None,
                                          "age": None,
                                          "sex": None
                                          }

    # Передаємо handler на обробку повідомлень в словник active_users з ключем message.from_user.id
    # При отриманні повідомлення оброблюємо ім'я, потім вік, а потім стать
    active_users[message.from_user.id]["handler"].append(
        app.add_handler(
            MessageHandler(get_name, filters.user(message.from_user.id) & filters.private))
    )


@app.on_message(filters.regex("Назад") & filters.private)
async def create_menu(client, message):
    """
        Створюємо ReplyKeyboardMarkup з кнопками 'Інформація про мене' та 'Налаштування'
    """

    await message.reply_text('Виберіть пункт з головного меню.',
                             reply_markup=ReplyKeyboardMarkup(
                                 [
                                     ["Інформація про мене"],  # Перший рядок
                                     ["Налаштування"],  # Другий рядок
                                 ],
                                 resize_keyboard=True  # Використання малої клавіатури
                             )
                             )


@app.on_message(filters.regex('Інформація про мене') & filters.private)
async def show_information(client, message):
    # Збережемо нажаття на 'Інформація про мене' в історію активності
    append_history(message, "Information")
    is_exist = await is_exist_person(message.from_user.id)
    if not is_exist:
        await message.reply_text('Ви ще не авторизовані 🥺')
        return

    # Відправити інформацію про користувача
    person = await get_person(message.from_user.id)
    reply_message = f'**Інформація про вас:**\n' \
                    f'Ім\'я: {person[0][1]}\n' \
                    f'Вік: {person[0][2]}\n' \
                    f'Стать: {"👨" if person[0][3] == "male" else "👩"}'
    await message.reply_text(reply_message)


@app.on_message(filters.regex('Налаштування') & filters.private)
async def create_settings(client, message):
    # Збережемо введення віку в історію активності
    append_history(message, "Create settings")

    if not await is_exist_person(message.from_user.id):
        await message.reply_text('Ви ще не авторизовані 🥺')
        return

    await message.reply_text('Налаштування.',
                             reply_markup=ReplyKeyboardMarkup(
                                 [
                                     ["Змінити вік"],  # Перший рядок
                                     ["Змінити стать"],  # Другий рядок
                                     ["Змінити ім\'я"],  # Третій рядок
                                     ["Назад"],  # Четвертий рядок
                                 ],
                                 resize_keyboard=True  # Використання малої клавіатури
                             )
                             )
    # Видаляємо існуючий handler
    delete_handlers(message.from_user.id)


@app.on_message(filters.regex("Змінити вік") & filters.private)
async def change_age(client, message):
    """
        Змінення віку користувача
    """
    # Збережемо введення віку в історію активності
    append_history(message, "Change age")

    if not await is_exist_person(message.from_user.id):
        await message.reply_text('Ви ще не авторизовані 🥺')
        return

    person = await get_person(message.from_user.id)
    active_users[message.from_user.id] = {"handler": [],
                                          "name": person[0][1],
                                          "age": person[0][2],
                                          "sex": person[0][3]
                                          }
    await message.reply_text('Введіть нове значення, або поверніться назад.',
                             reply_markup=ReplyKeyboardMarkup(
                                 [
                                     ["Назад"],  # Перший рядок
                                 ],
                                 resize_keyboard=True  # Використання малої клавіатури
                             )
                             )

    # Створюємо новий handler на отримання віку
    active_users[message.from_user.id]["handler"].append(
        app.add_handler(
            MessageHandler(get_age, filters.regex("^[0-9]+$") & filters.user(message.from_user.id) & filters.private))
    )
    # Створюємо новий handler на перехід назад
    active_users[message.from_user.id]["handler"].append(
        app.add_handler(
            MessageHandler(create_settings,
                           filters.regex("Назад") & filters.user(message.from_user.id) & filters.private))
    )


@app.on_message(filters.regex("Змінити стать") & filters.private)
async def change_sex(client, message):
    """
        Змінення статі користувача
    """
    # Збережемо введення віку в історію активності
    append_history(message, "Change sex")

    if not await is_exist_person(message.from_user.id):
        await message.reply_text('Ви ще не авторизовані 🥺')
        return

    person = await get_person(message.from_user.id)
    active_users[message.from_user.id] = {"handler": [],
                                          "name": person[0][1],
                                          "age": person[0][2],
                                          "sex": person[0][3]
                                          }
    await message.reply_text("Виберіть Вашу стать, або перейдіть назад.",
                             reply_markup=ReplyKeyboardMarkup(
                                 [
                                     ["Чоловік 👨", "Жінка 👩"],  # Перший рядок
                                     ["Назад"],  # Другий рядок
                                 ]
                             )
                             )

    # Створюємо новий handler на отримання статі
    active_users[message.from_user.id]["handler"].append(
        app.add_handler(MessageHandler(get_sex, filters.user(message.from_user.id)))
    )
    # Створюємо новий handler на перехід назад
    active_users[message.from_user.id]["handler"].append(
        app.add_handler(
            MessageHandler(create_settings,
                           filters.regex("Назад") & filters.user(message.from_user.id) & filters.private))
    )


@app.on_message(filters.regex("Змінити ім'я") & filters.private)
async def change_name(client, message):
    """
        Змінення імені користувача
    """
    # Збережемо введення віку в історію активності
    append_history(message, "Change name")

    if not await is_exist_person(message.from_user.id):
        await message.reply_text('Ви ще не авторизовані 🥺')
        return

    person = await get_person(message.from_user.id)
    active_users[message.from_user.id] = {"handler": [],
                                          "name": person[0][1],
                                          "age": person[0][2],
                                          "sex": person[0][3]
                                          }
    await message.reply_text('Введіть нове значення, або поверніться назад.',
                             reply_markup=ReplyKeyboardMarkup(
                                 [
                                     ["Назад"],  # Перший рядок
                                 ],
                                 resize_keyboard=True  # Використання малої клавіатури
                             )
                             )
    # Передаємо handler на обробку повідомлень в словник active_users з ключем message.from_user.id
    # При отриманні повідомлення оброблюємо ім'я, потім вік, а потім стать
    active_users[message.from_user.id]["handler"].append(
        app.add_handler(
            MessageHandler(get_name, filters.user(message.from_user.id) & filters.private))
    )
    # Створюємо новий handler на перехід назад
    active_users[message.from_user.id]["handler"].append(
        app.add_handler(
            MessageHandler(create_settings,
                           filters.regex("Назад") & filters.user(message.from_user.id) & filters.private))
    )


app.run()
