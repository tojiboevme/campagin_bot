import csv
import os
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, ADMIN_ID  # config.py da token va admin ID bor

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ✅ Kodlar faylidan yuklash
with open("data/codes.txt", "r", encoding="utf-8") as f:
    valid_codes = set(line.strip() for line in f if line.strip())

# ✅ Holatlar
class Form(StatesGroup):
    name = State()
    surname = State()
    phone = State()
    code = State()

# ✅ /start komandasi
@dp.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Assalomu alaykum! Aksiya botiga xush kelibsiz.\nIltimos, ismingizni kiriting:")

# ✅ Ism
@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.surname)
    await message.answer("Familiyangizni kiriting:")

# ✅ Familiya
@dp.message(Form.surname)
async def get_surname(message: Message, state: FSMContext):
    await state.update_data(surname=message.text)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="📱 Telefon raqam yuborish", request_contact=True)]
    ])
    await state.set_state(Form.phone)
    await message.answer("Telefon raqamingizni kiriting yoki yuboring:", reply_markup=keyboard)

# ✅ Telefon raqam
@dp.message(Form.phone, F.content_type.in_({"contact"}))
@dp.message(Form.phone, F.content_type.in_({"text"}))
async def get_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    await state.set_state(Form.code)
    await message.answer("8 xonali mahsulot kodini kiriting:", reply_markup=ReplyKeyboardRemove())

# ✅ Kod va CSV ga yozish
@dp.message(Form.code)
async def get_code(message: Message, state: FSMContext):
    code = message.text.strip()
    user_data = await state.get_data()

    if code not in valid_codes:
        await message.answer("❌ Bu kod bazada topilmadi. Iltimos, tekshirib qayta kiriting.")
        return

    user_data['code'] = code
    user_data['telegram_id'] = message.from_user.id
    user_data['datetime'] = datetime.now().isoformat()

    # ✅ CSV faylga yozish
    os.makedirs("storage", exist_ok=True)
    file_path = "storage/users.csv"
    file_exists = os.path.isfile(file_path)

    # Mavjud random raqamlarni o‘qish
    existing_numbers = set()
    if file_exists:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'random_number' in row and row['random_number'].isdigit():
                    existing_numbers.add(int(row['random_number']))

    # Yangi random raqam
    def generate_unique_number(existing, max_number=85000):
        for _ in range(100000):
            number = random.randint(1, max_number)
            if number not in existing:
                return number
        raise Exception("❌ Bo'sh raqam qolmadi!")

    random_number = generate_unique_number(existing_numbers)
    user_data['random_number'] = random_number

    # CSV yozuv
    fieldnames = ['name', 'surname', 'phone', 'code', 'random_number', 'telegram_id', 'datetime']
    with open(file_path, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'name': user_data['name'],
            'surname': user_data['surname'],
            'phone': user_data['phone'],
            'code': user_data['code'],
            'random_number': user_data['random_number'],
            'telegram_id': user_data['telegram_id'],
            'datetime': user_data['datetime']
        })

    await message.answer(
        f"✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz!\n"
        f"🎟 Aksiya raqamingiz: {random_number}\n"
        f"Omad tilaymiz!"
    )
    await state.clear()

# ✅ Admin uchun export
@dp.message(F.text == "/export")
async def export_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Sizda ruxsat yo'q.")
        return

    file_path = "storage/users.csv"
    if os.path.isfile(file_path):
        await message.answer_document(types.FSInputFile(file_path))
    else:
        await message.answer("Hozircha hech kim ro'yxatdan o'tmagan.")

# ✅ Botni ishga tushurish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
