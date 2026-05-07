“””
🤖 Clavio — AI ассистент для SMM

- Бесплатно: 5 запросов в день
- Платно: безлимит (подписка)
- Powered by Google Gemini (БЕСПЛАТНО!)

Установка:
pip install aiogram google-generativeai

Запуск:
python clavio_bot.py
“””

import asyncio
import json
import os
from datetime import date
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import google.generativeai as genai

# ==========================================

# ⚙️ НАСТРОЙКИ — заполни свои токены

# ==========================================

TELEGRAM_TOKEN = “8653276200:AAFj4hQK0k94zZ6yq2pcdW1GtOlKkMtZKgk”   # от @BotFather
GEMINI_API_KEY = “AIzaSyBKlYjWxxtbFkony3Lrs0UtHUWG9YQjgcM”        # от aistudio.google.com (НЕ пиши в чат!)
ADMIN_ID = 1392667004                          # твой Telegram ID (узнай у @userinfobot)

FREE_REQUESTS_PER_DAY = 5
SUBSCRIPTION_PRICE_1 = “299₽”  # тариф Старт
SUBSCRIPTION_PRICE_2 = “599₽”  # тариф Про

# ==========================================

# 🤖 Настройка Gemini

# ==========================================

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
model_name=“gemini-1.5-flash”,
system_instruction=(
“Ты — Clavio, умный AI-ассистент для SMM-специалистов в Telegram. “
“Помогаешь писать посты, придумывать идеи контента, хэштеги, заголовки. “
“Отвечай чётко, по делу, на русском языке. “
“Будь дружелюбным, креативным и профессиональным. “
“Если просят написать пост — сразу пиши готовый текст без лишних объяснений.”
)
)

# ==========================================

# 💾 База данных (простой JSON файл)

# ==========================================

DB_FILE = “users.json”

def load_db():
if os.path.exists(DB_FILE):
with open(DB_FILE, “r”) as f:
return json.load(f)
return {}

def save_db(db):
with open(DB_FILE, “w”) as f:
json.dump(db, f, indent=2)

def get_user(user_id: int):
db = load_db()
uid = str(user_id)
if uid not in db:
db[uid] = {
“requests_today”: 0,
“last_request_date”: str(date.today()),
“is_subscribed”: False,
“plan”: “free”,
“total_requests”: 0
}
save_db(db)
return db[uid]

def update_user(user_id: int, data: dict):
db = load_db()
uid = str(user_id)
db[uid].update(data)
save_db(db)

def reset_daily_if_needed(user_id: int):
user = get_user(user_id)
today = str(date.today())
if user[“last_request_date”] != today:
update_user(user_id, {
“requests_today”: 0,
“last_request_date”: today
})

def can_use(user_id: int) -> bool:
reset_daily_if_needed(user_id)
user = get_user(user_id)
if user[“is_subscribed”]:
return True
return user[“requests_today”] < FREE_REQUESTS_PER_DAY

def requests_left(user_id: int) -> int:
reset_daily_if_needed(user_id)
user = get_user(user_id)
if user[“is_subscribed”]:
return 999
return max(0, FREE_REQUESTS_PER_DAY - user[“requests_today”])

# ==========================================

# 🎛️ Клавиатуры

# ==========================================

def main_keyboard():
return InlineKeyboardMarkup(inline_keyboard=[
[
InlineKeyboardButton(text=“✍️ Написать пост”, callback_data=“cmd_post”),
InlineKeyboardButton(text=”#️⃣ Хэштеги”, callback_data=“cmd_hashtags”),
],
[
InlineKeyboardButton(text=“📅 Контент-план”, callback_data=“cmd_plan”),
InlineKeyboardButton(text=“🔄 Переписать текст”, callback_data=“cmd_rewrite”),
],
[InlineKeyboardButton(text=“💎 Купить подписку”, callback_data=“subscribe”)],
[
InlineKeyboardButton(text=“📊 Мой статус”, callback_data=“status”),
InlineKeyboardButton(text=“❓ Помощь”, callback_data=“help”),
]
])

def subscribe_keyboard():
return InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=f”⚡ Старт — {SUBSCRIPTION_PRICE_1}/мес”, callback_data=“pay_1”)],
[InlineKeyboardButton(text=f”💎 Про — {SUBSCRIPTION_PRICE_2}/мес”, callback_data=“pay_2”)],
[InlineKeyboardButton(text=“◀️ Назад”, callback_data=“back”)]
])

def back_keyboard():
return InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=“◀️ Назад”, callback_data=“back”)]
])

# ==========================================

# 📨 Хэндлеры

# ==========================================

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Хранилище режимов ожидания

user_modes = {}

@dp.message(CommandStart())
async def start(message: types.Message):
user = get_user(message.from_user.id)
left = requests_left(message.from_user.id)

```
text = (
    f"👋 Привет, {message.from_user.first_name}!\n\n"
    f"Я — Clavio, твой AI-помощник для создания контента 🚀\n\n"
    f"Что я умею:\n"
    f"✍️ Писать посты для Instagram, VK, Telegram\n"
    f"#️⃣ Подбирать хэштеги\n"
    f"📅 Составлять контент-план\n"
    f"🔄 Переписывать и улучшать тексты\n\n"
    f"📊 Сегодня осталось запросов: "
    f"{'∞' if user['is_subscribed'] else f'{left}/{FREE_REQUESTS_PER_DAY}'}\n\n"
    f"Выбери действие или просто напиши мне! 👇"
)
await message.answer(text, reply_markup=main_keyboard())
```

@dp.callback_query(F.data == “cmd_post”)
async def cmd_post(callback: types.CallbackQuery):
user_modes[callback.from_user.id] = “post”
await callback.message.edit_text(
“✍️ Напиши тему поста и для какой соцсети.\n\n”
“Например:\n”
“«Пост про утреннюю рутину для Instagram»\n”
“«Продающий пост про курс по фотографии для VK»”,
reply_markup=back_keyboard()
)

@dp.callback_query(F.data == “cmd_hashtags”)
async def cmd_hashtags(callback: types.CallbackQuery):
user_modes[callback.from_user.id] = “hashtags”
await callback.message.edit_text(
“#️⃣ Напиши тему или вставь свой пост — подберу хэштеги!\n\n”
“Например: «фитнес для начинающих»”,
reply_markup=back_keyboard()
)

@dp.callback_query(F.data == “cmd_plan”)
async def cmd_plan(callback: types.CallbackQuery):
user_modes[callback.from_user.id] = “plan”
await callback.message.edit_text(
“📅 Напиши тему твоего аккаунта — составлю контент-план на неделю!\n\n”
“Например: «магазин одежды», «личный блог про путешествия»”,
reply_markup=back_keyboard()
)

@dp.callback_query(F.data == “cmd_rewrite”)
async def cmd_rewrite(callback: types.CallbackQuery):
user_modes[callback.from_user.id] = “rewrite”
await callback.message.edit_text(
“🔄 Вставь текст который нужно улучшить — сделаю его живым и интересным!”,
reply_markup=back_keyboard()
)

@dp.callback_query(F.data == “subscribe”)
async def show_subscribe(callback: types.CallbackQuery):
user = get_user(callback.from_user.id)
if user[“is_subscribed”]:
await callback.message.edit_text(
“✅ У тебя уже есть активная подписка!\nПользуйся безлимитно 🎉”,
reply_markup=main_keyboard()
)
return
await callback.message.edit_text(
f”💎 Выбери тариф:\n\n”
f”⚡ Старт — {SUBSCRIPTION_PRICE_1}/мес\n”
f”• 100 запросов в день\n\n”
f”💎 Про — {SUBSCRIPTION_PRICE_2}/мес\n”
f”• Безлимитные запросы\n”
f”• Приоритетные ответы\n”
f”• Доступ к новым функциям первым”,
reply_markup=subscribe_keyboard()
)

@dp.callback_query(F.data.in_({“pay_1”, “pay_2”}))
async def pay(callback: types.CallbackQuery):
price = SUBSCRIPTION_PRICE_1 if callback.data == “pay_1” else SUBSCRIPTION_PRICE_2
plan = “Старт” if callback.data == “pay_1” else “Про”
await callback.message.edit_text(
f”💳 Оплата тарифа «{plan}» — {price}/мес\n\n”
f”1. Переведи оплату на карту:\n”
f”   [ВСТАВЬ НОМЕР СВОЕЙ КАРТЫ]\n\n”
f”2. В комментарии укажи свой ID:\n”
f”   {callback.from_user.id}\n\n”
f”3. Напиши @[ТВО_ЮЗЕРНЕЙМ] с чеком\n\n”
f”⚡ Активация в течение 15 минут”,
reply_markup=back_keyboard()
)

@dp.callback_query(F.data == “status”)
async def status_callback(callback: types.CallbackQuery):
user = get_user(callback.from_user.id)
left = requests_left(callback.from_user.id)
status = “💎 Подписка активна” if user[“is_subscribed”] else f”🆓 Бесплатный план”
text = (
f”📊 Твой статус:\n\n”
f”{status}\n”
f”📩 Запросов сегодня осталось: {‘∞’ if user[‘is_subscribed’] else f’{left}/{FREE_REQUESTS_PER_DAY}’}\n”
f”📈 Всего запросов: {user.get(‘total_requests’, 0)}\n”
)
if not user[“is_subscribed”]:
text += f”\n💎 Хочешь безлимит? Оформи подписку!”
await callback.message.edit_text(text, reply_markup=main_keyboard())

@dp.callback_query(F.data == “help”)
async def help_callback(callback: types.CallbackQuery):
await callback.message.edit_text(
“❓ Как пользоваться Clavio:\n\n”
“• Нажми кнопку или просто напиши запрос\n\n”
“Примеры запросов:\n”
“📝 «Напиши пост про скидки в моём магазине»\n”
“🎯 «Придумай 10 идей для контента про фитнес»\n”
“✨ «Сделай этот текст более живым: [текст]»\n”
“📅 «Контент-план на неделю для кофейни»\n”
“#️⃣ «Хэштеги для поста про йогу»”,
reply_markup=main_keyboard()
)

@dp.callback_query(F.data == “back”)
async def back(callback: types.CallbackQuery):
user_modes.pop(callback.from_user.id, None)
user = get_user(callback.from_user.id)
left = requests_left(callback.from_user.id)
await callback.message.edit_text(
f”Чем могу помочь?\n\n”
f”📊 Запросов сегодня: {‘∞’ if user[‘is_subscribed’] else f’{left}/{FREE_REQUESTS_PER_DAY}’}”,
reply_markup=main_keyboard()
)

@dp.message(Command(“admin”))
async def admin_panel(message: types.Message):
if message.from_user.id != ADMIN_ID:
return
db = load_db()
total = len(db)
subscribed = sum(1 for u in db.values() if u.get(“is_subscribed”))
requests = sum(u.get(“total_requests”, 0) for u in db.values())
await message.answer(
f”👑 Админ панель\n\n”
f”👥 Пользователей: {total}\n”
f”💎 Подписчиков: {subscribed}\n”
f”📩 Всего запросов: {requests}\n\n”
f”Выдать подписку: /give_sub USER_ID”
)

@dp.message(Command(“give_sub”))
async def give_sub(message: types.Message):
if message.from_user.id != ADMIN_ID:
return
parts = message.text.split()
if len(parts) < 2:
await message.answer(“Использование: /give_sub USER_ID”)
return
target_id = parts[1]
db = load_db()
if target_id not in db:
await message.answer(“Пользователь не найден”)
return
db[target_id][“is_subscribed”] = True
save_db(db)
await message.answer(f”✅ Подписка выдана пользователю {target_id}”)
try:
await bot.send_message(int(target_id), “🎉 Вам активирована подписка! Теперь у вас безлимитный доступ к Clavio.”)
except:
pass

# Главный хэндлер

@dp.message()
async def handle_message(message: types.Message):
user_id = message.from_user.id

```
if not can_use(user_id):
    await message.answer(
        f"⛔ Лимит на сегодня исчерпан!\n\n"
        f"У тебя было {FREE_REQUESTS_PER_DAY} бесплатных запросов в день.\n\n"
        f"💎 Оформи подписку и пользуйся безлимитно!",
        reply_markup=main_keyboard()
    )
    return

# Формируем промпт в зависимости от режима
mode = user_modes.pop(user_id, None)
user_text = message.text

if mode == "post":
    prompt = f"Напиши готовый пост для соцсетей на тему: {user_text}. Сделай его живым, с эмодзи и призывом к действию."
elif mode == "hashtags":
    prompt = f"Подбери 20-25 релевантных хэштегов для темы: {user_text}. Разбей на группы: популярные, средние, нишевые."
elif mode == "plan":
    prompt = f"Составь контент-план на 7 дней для аккаунта на тему: {user_text}. Для каждого дня укажи тему и формат поста."
elif mode == "rewrite":
    prompt = f"Перепиши этот текст — сделай его более живым, интересным и вовлекающим, сохрани смысл:\n\n{user_text}"
else:
    prompt = user_text

thinking = await message.answer("🤖 Clavio думает...")

try:
    response = model.generate_content(prompt)
    result = response.text

    user = get_user(user_id)
    update_user(user_id, {
        "requests_today": user["requests_today"] + 1,
        "total_requests": user.get("total_requests", 0) + 1
    })

    left = requests_left(user_id)
    footer = "" if user["is_subscribed"] else f"\n\n_Осталось запросов: {left}/{FREE_REQUESTS_PER_DAY}_"

    await thinking.edit_text(result + footer, parse_mode="Markdown", reply_markup=main_keyboard())

except Exception as e:
    await thinking.edit_text("❌ Ошибка. Попробуй ещё раз.", reply_markup=main_keyboard())
    print(f"Error: {e}")
```

# ==========================================

# 🚀 Запуск

# ==========================================

async def main():
print(“🤖 Clavio запущен!”)
await dp.start_polling(bot)

if **name** == “**main**”:
asyncio.run(main())
