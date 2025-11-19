import telebot
from dotenv import load_dotenv
import os
from telebot import types

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Пачка")
    btn2 = types.KeyboardButton("Блок")
    markup.row(btn1, btn2)
    return markup

def get_payment_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Платно")
    btn2 = types.KeyboardButton("Бесплатно")
    markup.row(btn1, btn2)
    return markup

def get_edit_menu():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("💰 Изменить баланс", callback_data="edit_balance")
    btn2 = types.InlineKeyboardButton("📦 Изменить пачки", callback_data="edit_packs")
    btn3 = types.InlineKeyboardButton("📦 Изменить блоки", callback_data="edit_blocks")
    btn4 = types.InlineKeyboardButton("💵 Изменить профит", callback_data="edit_profit")
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    return markup

class UserState:
    """Класс для хранения состояния пользователя во время диалога"""
    def __init__(self, category=None, payment_type=None):
        self.category = category
        self.payment_type = payment_type 

    def reset(self):
        self.category = None
        self.payment_type = None

    def is_complete(self):
        return self.category is not None and self.payment_type is not None

    def __repr__(self):
        return f"UserState(category={self.category}, payment_type={self.payment_type})"

from db import Database

load_dotenv()
bot = telebot.TeleBot(os.getenv("TOKEN"))
USERID1 = int(os.getenv("USERID1"))
USERID2 = int(os.getenv("USERID2"))

db = Database("data.txt")
user_states = {}

PRICE_PACK = 40
PRICE_BLOCK = 400

def is_authorized(userid):
    return userid == USERID1 or userid == USERID2

@bot.message_handler(commands=['start'])
def start_handler(message):
    """Обработчик команды /start"""
    if not is_authorized(message.from_user.id):
        bot.send_message(message.chat.id, "❌ Доступ запрещен")
        return
    
    bot.send_message(
        message.chat.id,
        "👋 Привет, хозяин!\n\nВыбери категорию:",
        reply_markup=get_main_menu()
    )


@bot.message_handler(func=lambda m: m.text in ["Пачка", "Блок"])
def category_handler(message):
    """Обработчик выбора категории"""
    if not is_authorized(message.from_user.id):
        return
    
    user_id = message.from_user.id
    user_states[user_id] = UserState(category=message.text)
    
    bot.send_message(
        message.chat.id,
        f"✅ Выбрано: {message.text}\n\nВыбери тип оплаты:",
        reply_markup=get_payment_menu()
    )


@bot.message_handler(func=lambda m: m.text in ["Платно", "Бесплатно"])
def payment_handler(message):
    """Обработчик выбора типа оплаты"""
    if not is_authorized(message.from_user.id):
        return
    
    user_id = message.from_user.id
    
    if user_id not in user_states or not user_states[user_id].category:
        bot.send_message(message.chat.id, "⚠️ Сначала выбери категорию (Пачка/Блок)")
        return
    
    user_states[user_id].payment_type = message.text
    
    data = db.load_data()
    
    category_text = "пачек" if user_states[user_id].category == "Пачка" else "блоков"
    
    info_text = f"""
📊 Текущее состояние:

💰 Баланс: {data['balance']} шек.
📦 Пачек: {data['packs']} шт.
📦 Блоков: {data['blocks']} шт.
💵 Чистый профит: {data['profit']} шек.

Введи количество {category_text}:
"""
    
    msg = bot.send_message(message.chat.id, info_text)
    bot.register_next_step_handler(msg, quantity_handler)


def quantity_handler(message):
    """Обработчик ввода количества"""
    if not is_authorized(message.from_user.id):
        return
    
    user_id = message.from_user.id
    
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "⚠️ Введи число:")
        bot.register_next_step_handler(msg, quantity_handler)
        return
    
    quantity = int(message.text)
    state = user_states[user_id]
    data = db.load_data()
    
    if state.category == "Пачка":
        packs_change = quantity
        blocks_change = 0
        price = quantity * PRICE_PACK
    else:  
        packs_change = quantity * 10
        blocks_change = quantity
        price = quantity * PRICE_BLOCK
    
    if state.payment_type == "Платно":
        new_balance = data['balance'] + price
        new_packs = data['packs'] + packs_change
        new_blocks = data['blocks'] + blocks_change
        new_profit = data['profit'] + price
    else:  
        new_balance = data['balance']
        new_packs = data['packs'] + packs_change
        new_blocks = data['blocks'] + blocks_change
        new_profit = data['profit']
    
    result_text = f"""
✅ Обработано: {quantity} {state.category.lower()}

💰 Цена: {price if state.payment_type == 'Платно' else 0} шек.

📊 Новое состояние:
💰 Баланс: {new_balance} шек.
📦 Пачек: {new_packs} шт.
📦 Блоков: {new_blocks} шт.
💵 Чистый профит: {new_profit} шек.
"""
    
    db.save_data({
        'balance': new_balance,
        'packs': new_packs,
        'blocks': new_blocks,
        'profit': new_profit
    })
    
    bot.send_message(
        message.chat.id,
        result_text,
        reply_markup=get_edit_menu()
    )


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Обработчик inline кнопок"""
    if not is_authorized(call.from_user.id):
        return
    
    if call.data == "edit_balance":
        msg = bot.send_message(call.message.chat.id, "💰 Введи новый баланс:")
        bot.register_next_step_handler(msg, edit_balance_handler)
    
    elif call.data == "edit_packs":
        msg = bot.send_message(call.message.chat.id, "📦 Введи новое количество пачек:")
        bot.register_next_step_handler(msg, edit_packs_handler)
    
    elif call.data == "edit_blocks":
        msg = bot.send_message(call.message.chat.id, "📦 Введи новое количество блоков:")
        bot.register_next_step_handler(msg, edit_blocks_handler)
    
    elif call.data == "edit_profit":
        msg = bot.send_message(call.message.chat.id, "💵 Введи новый профит:")
        bot.register_next_step_handler(msg, edit_profit_handler)
    
    bot.answer_callback_query(call.id)


def edit_balance_handler(message):
    """Изменение баланса"""
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "⚠️ Введи число:")
        bot.register_next_step_handler(msg, edit_balance_handler)
        return
    
    data = db.load_data()
    data['balance'] = int(message.text)
    db.save_data(data)
    
    bot.send_message(
        message.chat.id,
        f"✅ Баланс изменен на {data['balance']} шек.",
        reply_markup=get_main_menu()
    )


def edit_packs_handler(message):
    """Изменение количества пачек"""
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "⚠️ Введи число:")
        bot.register_next_step_handler(msg, edit_packs_handler)
        return
    
    data = db.load_data()
    data['packs'] = int(message.text)
    db.save_data(data)
    
    bot.send_message(
        message.chat.id,
        f"✅ Количество пачек изменено на {data['packs']} шт.",
        reply_markup=get_main_menu()
    )


def edit_blocks_handler(message):
    """Изменение количества блоков"""
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "⚠️ Введи число:")
        bot.register_next_step_handler(msg, edit_blocks_handler)
        return
    
    data = db.load_data()
    data['blocks'] = int(message.text)
    db.save_data(data)
    
    bot.send_message(
        message.chat.id,
        f"✅ Количество блоков изменено на {data['blocks']} шт.",
        reply_markup=get_main_menu()
    )


def edit_profit_handler(message):
    """Изменение профита"""
    if not message.text.isdigit():
        msg = bot.send_message(message.chat.id, "⚠️ Введи число:")
        bot.register_next_step_handler(msg, edit_profit_handler)
        return
    
    data = db.load_data()
    data['profit'] = int(message.text)
    db.save_data(data)
    
    bot.send_message(
        message.chat.id,
        f"✅ Профит изменен на {data['profit']} шек.",
        reply_markup=get_main_menu()
    )


if __name__ == "__main__":
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)