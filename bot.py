import csv
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, ADMIN_ID

bot = Bot(token="7461009184:AAGaxqw5y8QOSpDxBp5_7Jy1RBPF3h4c8MY")
dp = Dispatcher(storage=MemoryStorage())

# ✅ Kodlar bazasi - text fayldan yuklash
with open("data/codes.txt", "r", encoding="utf-8") as f:
    valid_codes = set(line.strip() for line in f if line.strip())

# ✅ Holatlar
class Form(StatesGroup):
    name = State()
    surname = State()
    phone = State()
    code = State()

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
    await message.answer("Telefon raqamingizni kiriting yoki yuboring:", reply_markup=keyboard)

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

    if code not in valid_codes:
        await message.answer("❌ Bu kod bazada topilmadi. Iltimos, tekshirib qayta kiriting.")
        return

    user_data['code'] = code
    user_data['telegram_id'] = message.from_user.id
    user_data['datetime'] = datetime.now().isoformat()

    os.makedirs("storage", exist_ok=True)
    file_path = "storage/users.csv"
    file_exists = os.path.isfile(file_path)

    with open(file_path, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'surname', 'phone', 'code', 'telegram_id', 'datetime'])
        if not file_exists:
            writer.writeheader()
        writer.writerow(user_data)

    await message.answer("✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz. Rahmat!")
    await state.clear()

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

# ✅ Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
