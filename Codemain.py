import asyncio
import json
import os
from datetime import date
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery

import google.generativeai as genai

TELEGRAM_TOKEN = “8653276200:AAFj4hQK0k94zZ6yq2pcdW1GtOlKkMtZKgk”
GEMINI_API_KEY = “AIzaSyBKlYjWxxtbFkony3Lrs0UtHUWG9YQjgcM”
ADMIN_ID = 1392667004

FREE_REQUESTS_PER_DAY = 5
STARS_PRICE_START = 100
STARS_PRICE_PRO = 200

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(
model_name=“gemini-1.5-flash”,
system_instruction=“Ti Clavio, rozumnij AI-asistent dlya SMM u Telegram. Dopomogaesh pisati posti, vigaduvati idei kontenty, heshtegi, zagolovki. Vidpovidaj po-rosijsky abo po-ukrainsky zalezhno vid togo yak pyshe koristuvach. Bud druzhnім ta profesijnim.”
)

DB_FILE = “users.json”

def load_db():
if os.path.exists(DB_FILE):
with open(DB_FILE, “r”) as f:
return json.load(f)
return {}

def save_db(db):
with open(DB_FILE, “w”) as f:
json.dump(db, f, indent=2)

def get_user(user_id):
db = load_db()
uid = str(user_id)
if uid not in db:
db[uid] = {
“requests_today”: 0,
“last_request_date”: str(date.today()),
“is_subscribed”: False,
“total_requests”: 0
}
save_db(db)
return db[uid]

def update_user(user_id, data):
db = load_db()
uid = str(user_id)
db[uid].update(data)
save_db(db)

def reset_daily_if_needed(user_id):
user = get_user(user_id)
today = str(date.today())
if user[“last_request_date”] != today:
update_user(user_id, {“requests_today”: 0, “last_request_date”: today})

def can_use(user_id):
reset_daily_if_needed(user_id)
user = get_user(user_id)
if user[“is_subscribed”]:
return True
return user[“requests_today”] < FREE_REQUESTS_PER_DAY

def requests_left(user_id):
reset_daily_if_needed(user_id)
user = get_user(user_id)
if user[“is_subscribed”]:
return 999
return max(0, FREE_REQUESTS_PER_DAY - user[“requests_today”])

def main_keyboard():
return InlineKeyboardMarkup(inline_keyboard=[
[
InlineKeyboardButton(text=“Post”, callback_data=“cmd_post”),
InlineKeyboardButton(text=“Hashtagi”, callback_data=“cmd_hashtags”),
],
[
InlineKeyboardButton(text=“Kontent-plan”, callback_data=“cmd_plan”),
InlineKeyboardButton(text=“Perepisat tekst”, callback_data=“cmd_rewrite”),
],
[InlineKeyboardButton(text=“Kupit podpisku”, callback_data=“subscribe”)],
[
InlineKeyboardButton(text=“Moj status”, callback_data=“status”),
InlineKeyboardButton(text=“Pomosh”, callback_data=“help”),
]
])

def back_keyboard():
return InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=“Nazad”, callback_data=“back”)]
])

def subscribe_keyboard():
return InlineKeyboardMarkup(inline_keyboard=[
[InlineKeyboardButton(text=“Start - “ + str(STARS_PRICE_START) + “ Stars/mes”, callback_data=“pay_start”)],
[InlineKeyboardButton(text=“Pro - “ + str(STARS_PRICE_PRO) + “ Stars/mes”, callback_data=“pay_pro”)],
[InlineKeyboardButton(text=“Nazad”, callback_data=“back”)]
])

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
user_modes = {}

@dp.message(CommandStart())
async def start(message: types.Message):
user = get_user(message.from_user.id)
left = requests_left(message.from_user.id)
sub = “inf” if user[“is_subscribed”] else str(left) + “/” + str(FREE_REQUESTS_PER_DAY)
text = “Privet “ + message.from_user.first_name + “!\n\nYa Clavio, tvoj AI-pomoshnik dlya SMM.\n\nMogu:\nPisat posty dlya Instagram, VK, Telegram\nPodberat heshtegi\nSostavljat kontent-plan\nPerepIsyvat teksty\n\nZaprosov ostalosy: “ + sub + “\n\nVyberi dejstvie ili prosto napishi mne!”
await message.answer(text, reply_markup=main_keyboard())

@dp.callback_query(F.data == “cmd_post”)
async def cmd_post(callback: types.CallbackQuery):
user_modes[callback.from_user.id] = “post”
await callback.message.edit_text(“Napishi temu posta i dlya kakoj socsetej.\n\nNapimer: Post pro utrennuyu rutinu dlya Instagram”, reply_markup=back_keyboard())

@dp.callback_query(F.data == “cmd_hashtags”)
async def cmd_hashtags(callback: types.CallbackQuery):
user_modes[callback.from_user.id] = “hashtags”
await callback.message.edit_text(“Napishi temu - poderu heshtegi!\n\nNapimer: fitnes dlya nachinayushih”, reply_markup=back_keyboard())

@dp.callback_query(F.data == “cmd_plan”)
async def cmd_plan(callback: types.CallbackQuery):
user_modes[callback.from_user.id] = “plan”
await callback.message.edit_text(“Napishi temu akkaunta - sostavlyu kontent-plan na nedelyu!\n\nNapimer: magazin odezhdy”, reply_markup=back_keyboard())

@dp.callback_query(F.data == “cmd_rewrite”)
async def cmd_rewrite(callback: types.CallbackQuery):
user_modes[callback.from_user.id] = “rewrite”
await callback.message.edit_text(“Vstav tekst kotoryj nuzno uluchshit!”, reply_markup=back_keyboard())

@dp.callback_query(F.data == “subscribe”)
async def show_subscribe(callback: types.CallbackQuery):
user = get_user(callback.from_user.id)
if user[“is_subscribed”]:
await callback.message.edit_text(“U tebya uzhe est podpiska! Polzujsya bezlimitno!”, reply_markup=main_keyboard())
return
await callback.message.edit_text(
“Vyberi tarif:\n\nStart - “ + str(STARS_PRICE_START) + “ Telegram Stars/mes\n100 zaprosov v den\n\nPro - “ + str(STARS_PRICE_PRO) + “ Telegram Stars/mes\nBezlimitnye zaprosy\n\nStars mozhno kupit pryamo v Telegram!”,
reply_markup=subscribe_keyboard()
)

@dp.callback_query(F.data == “pay_start”)
async def pay_start(callback: types.CallbackQuery):
await callback.message.delete()
await bot.send_invoice(
chat_id=callback.from_user.id,
title=“Clavio Start”,
description=“100 zaprosov v den na 30 dnej”,
payload=“start_subscription”,
currency=“XTR”,
prices=[LabeledPrice(label=“Clavio Start - 1 mes”, amount=STARS_PRICE_START)]
)

@dp.callback_query(F.data == “pay_pro”)
async def pay_pro(callback: types.CallbackQuery):
await callback.message.delete()
await bot.send_invoice(
chat_id=callback.from_user.id,
title=“Clavio Pro”,
description=“Bezlimitnye zaprosy na 30 dnej”,
payload=“pro_subscription”,
currency=“XTR”,
prices=[LabeledPrice(label=“Clavio Pro - 1 mes”, amount=STARS_PRICE_PRO)]
)

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
await pre_checkout_query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment(message: types.Message):
user_id = message.from_user.id
update_user(user_id, {“is_subscribed”: True})
payload = message.successful_payment.invoice_payload
plan = “Pro” if payload == “pro_subscription” else “Start”
await message.answer(“Oplata proshla! Tarif “ + plan + “ aktivirovan!\n\nTeper polzujsya Clavio bezlimitno!”, reply_markup=main_keyboard())

@dp.callback_query(F.data == “status”)
async def status_callback(callback: types.CallbackQuery):
user = get_user(callback.from_user.id)
left = requests_left(callback.from_user.id)
status = “Podpiska aktivna” if user[“is_subscribed”] else “Besplatnyj plan”
sub = “inf” if user[“is_subscribed”] else str(left) + “/” + str(FREE_REQUESTS_PER_DAY)
await callback.message.edit_text(“Tvoj status:\n\n” + status + “\nZaprosov ostalosy: “ + sub + “\nVsego zaprosov: “ + str(user.get(“total_requests”, 0)), reply_markup=main_keyboard())

@dp.callback_query(F.data == “help”)
async def help_callback(callback: types.CallbackQuery):
await callback.message.edit_text(“Kak polzovatsya Clavio:\n\nNazhmi knopku ili prosto napishi zapros\n\nPrimery:\nNapishi post pro skidki v moem magazine\nPridumaj 10 idej dlya kontenta pro fitnes\nHeshtegi dlya posta pro yogu\nKontent-plan dlya kofejni”, reply_markup=main_keyboard())

@dp.callback_query(F.data == “back”)
async def back(callback: types.CallbackQuery):
user_modes.pop(callback.from_user.id, None)
user = get_user(callback.from_user.id)
left = requests_left(callback.from_user.id)
sub = “inf” if user[“is_subscribed”] else str(left) + “/” + str(FREE_REQUESTS_PER_DAY)
await callback.message.edit_text(“Chem mogu pomoch?\n\nZaprosov segodnya: “ + sub, reply_markup=main_keyboard())

@dp.message(Command(“give_sub”))
async def give_sub(message: types.Message):
if message.from_user.id != ADMIN_ID:
return
parts = message.text.split()
if len(parts) < 2:
await message.answer(“Ispolzovanie: /give_sub USER_ID”)
return
target_id = parts[1]
db = load_db()
if target_id not in db:
await message.answer(“Polzovatel ne najden”)
return
db[target_id][“is_subscribed”] = True
save_db(db)
await message.answer(“Podpiska vydana “ + target_id)
try:
await bot.send_message(int(target_id), “Vam aktivirovana podpiska Clavio Pro!”)
except:
pass

@dp.message(Command(“admin”))
async def admin_panel(message: types.Message):
if message.from_user.id != ADMIN_ID:
return
db = load_db()
total = len(db)
subscribed = sum(1 for u in db.values() if u.get(“is_subscribed”))
requests = sum(u.get(“total_requests”, 0) for u in db.values())
await message.answer(“Admin panel\n\nPolzovatelej: “ + str(total) + “\nPodpischikov: “ + str(subscribed) + “\nVsego zaprosov: “ + str(requests))

@dp.message()
async def handle_message(message: types.Message):
user_id = message.from_user.id
if not can_use(user_id):
await message.answer(“Limit na segodnya ischerpan!\n\nOformi podpisku cherez Telegram Stars i polzujsya bezlimitno!”, reply_markup=main_keyboard())
return
mode = user_modes.pop(user_id, None)
user_text = message.text
if mode == “post”:
prompt = “Napishi gotovyj post dlya socsetej na temu: “ + user_text + “. Sdelaj ego zhivym, s emoji i prizvom k dejstviyu.”
elif mode == “hashtags”:
prompt = “Podberi 20-25 relevantnyh heshtegow dlya temy: “ + user_text + “. Razbej na gruppy: populyarnye, srednie, nishovye.”
elif mode == “plan”:
prompt = “Sostavj kontent-plan na 7 dnej dlya akkaunta na temu: “ + user_text + “. Dlya kazhdogo dnya ukazi temu i format posta.”
elif mode == “rewrite”:
prompt = “Perepishi etot tekst - sdelaj ego bolee zhivym i vovlekayushim, sohrani smysl:\n\n” + user_text
else:
prompt = user_text
thinking = await message.answer(“Clavio dumaet…”)
try:
response = model.generate_content(prompt)
result = response.text
user = get_user(user_id)
update_user(user_id, {
“requests_today”: user[“requests_today”] + 1,
“total_requests”: user.get(“total_requests”, 0) + 1
})
left = requests_left(user_id)
footer = “” if user[“is_subscribed”] else “\n\nOstalosy zaprosov: “ + str(left) + “/” + str(FREE_REQUESTS_PER_DAY)
await thinking.edit_text(result + footer, reply_markup=main_keyboard())
except Exception as e:
await thinking.edit_text(“Oshibka. Poprobuj eshhe raz.”, reply_markup=main_keyboard())
print(“Error: “ + str(e))

async def main():
print(“Clavio zapushen!”)
await dp.start_polling(bot)

if **name** == “**main**”:
asyncio.run(main())
