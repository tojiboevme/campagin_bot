import csv
import os
import re
from datetime import datetime
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, ADMIN_ID
from codes import valid_codes  # ✅ Kodlar bazasini Python fayldan import qilamiz

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

used_codes_file = "storage/used_codes.csv"
users_file = "storage/users.csv"

# ✅ Kod formati tekshiruv funksiyasi
def is_valid_code_format(code: str) -> bool:
    return bool(re.fullmatch(r"\d{8}", code))

# ✅ Holatlar
class Form(StatesGroup):
    name = State()
    surname = State()
    phone = State()
    code = State()

# ✅ Boshlanish
@dp.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Assalomu alaykum! Aksiya botiga xush kelibsiz.\nIltimos, ismingizni kiriting:")

@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.surname)
    await message.answer("Familiyangizni kiriting:")

@dp.message(Form.surname)
async def get_surname(message: Message, state: FSMContext):
    await state.update_data(surname=message.text)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📱 Telefon raqam yuborish", request_contact=True)]
    ])
    await state.set_state(Form.phone)
    await message.answer("Telefon raqamingizni yuboring yoki kiriting:", reply_markup=keyboard)

@dp.message(Form.phone, F.content_type.in_({"contact"}))
@dp.message(Form.phone, F.content_type.in_({"text"}))
async def get_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    await state.set_state(Form.code)
    await message.answer("8 xonali mahsulot kodini kiriting:", reply_markup=ReplyKeyboardRemove())

@dp.message(Form.code)
async def get_code(message: Message, state: FSMContext):
    code = message.text.strip()
    user_data = await state.get_data()

    # ✅ Kod formati tekshiriladi
    if not is_valid_code_format(code):
        await message.answer("❌ Kod formati noto‘g‘ri. Iltimos, faqat 8 xonali raqam kiriting.")
        return

    if code not in valid_codes:
        await message.answer("❌ Bu kod bazada topilmadi. Iltimos, tekshirib qayta kiriting.")
        return

    os.makedirs("storage", exist_ok=True)
    if not os.path.exists(users_file):
        with open(users_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'surname', 'phone', 'code', 'telegram_id', 'datetime', 'random_number'])
            writer.writeheader()

    if not os.path.exists(used_codes_file):
        with open(used_codes_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(['code'])

    # ✅ Foydalanilgan kodlarni tekshirish
    with open(used_codes_file, "r", encoding="utf-8") as f:
        used_codes = set(line.strip() for line in f if line.strip() and line.strip() != "code")

    if code in used_codes:
        await message.answer("❗Bu kod allaqachon ishlatilgan. Boshqa kod kiriting.")
        return

    random_number = random.randint(1, 85000)

    user_data.update({
        'code': code,
        'telegram_id': message.from_user.id,
        'datetime': datetime.now().isoformat(),
        'random_number': random_number
    })

    # ✅ Malumotlarni CSV faylga yozish
    with open(users_file, "a", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'surname', 'phone', 'code', 'telegram_id', 'datetime', 'random_number'])
        writer.writerow(user_data)

    with open(used_codes_file, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([code])

    await message.answer(f"✅ Tabriklaymiz! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n🎯 Sizga berilgan aksiya raqami: {random_number}")

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🔁 Yana kod bor"), KeyboardButton(text="❌ Yo‘q, rahmat")]
    ])
    await state.clear()
    await message.answer("Sizda yana mahsulot kodi bormi?", reply_markup=keyboard)

@dp.message(F.text == "🔁 Yana kod bor")
async def again_handler(message: Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Yaxshi! Keling, yana ro'yxatdan o'taylik. Ismingizni kiriting:", reply_markup=ReplyKeyboardRemove())

@dp.message(F.text == "❌ Yo‘q, rahmat")
async def done_handler(message: Message):
    await message.answer("Rahmat! Aksiyada qatnashganingiz uchun minnatdormiz 😊", reply_markup=ReplyKeyboardRemove())

@dp.message(F.text == "/export")
async def export_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Sizda ruxsat yo'q.")
        return

    if os.path.isfile(users_file):
        await message.answer_document(types.FSInputFile(users_file))
    else:
        await message.answer("📂 Hozircha hech kim ro'yxatdan o'tmagan.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
