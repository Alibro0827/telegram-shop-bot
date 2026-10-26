import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_ID = 123456789  # Bu yerga o'z Telegram ID raqamingizni yozasiz (admin uchun)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Foydalanuvchi savatchasini saqlab turish uchun vaqtinchalik baza
user_carts = {}

# Buyurtma berish holatlari (FSM)
class OrderState(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍️ Mahsulotlar katalogi", callback_data="catalog")
    builder.button(text="🛒 Savatcha", callback_data="view_cart")
    builder.button(text="📞 Biz bilan bog'lanish", callback_data="contact")
    builder.adjust(1)
    
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n"
        "Bizning online do'konimizga xush kelibsiz. Kerakli bo'limni tanlang:",
        reply_markup=builder.as_markup()
    )

# Katalog menyusi
@dp.callback_query(F.data == "catalog")
async def show_catalog(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Smartfonlar", callback_data="category_phones")
    builder.button(text="💻 Noutbuklar", callback_data="category_laptops")
    builder.button(text="🔙 Asosiy menyu", callback_data="back_home")
    builder.adjust(1)
    
    await callback.message.edit_text("Kategoriyani tanlang:", reply_markup=builder.as_markup())
    await callback.answer()

# Smartfonlar kategoriyasi
@dp.callback_query(F.data == "category_phones")
async def show_phones(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="iPhone 13 - $700", callback_data="add_iPhone_13_$700")
    builder.button(text="Samsung S23 - $650", callback_data="add_Samsung_S23_$650")
    builder.button(text="🔙 Orqaga", callback_data="catalog")
    builder.adjust(1)
    
    await callback.message.edit_text("Smartfonlar ro'yxati (sotib olish uchun bosing):", reply_markup=builder.as_markup())
    await callback.answer()

# Noutbuklar kategoriyasi
@dp.callback_query(F.data == "category_laptops")
async def show_laptops(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="MacBook Air M1 - $900", callback_data="add_MacBook_Air_M1_$900")
    builder.button(text="ASUS ZenBook - $800", callback_data="add_ASUS_ZenBook_$800")
    builder.button(text="🔙 Orqaga", callback_data="catalog")
    builder.adjust(1)
    
    await callback.message.edit_text("Noutbuklar ro'yxati (sotib olish uchun bosing):", reply_markup=builder.as_markup())
    await callback.answer()

# Mahsulotni savatga qo'shish
@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(callback: types.CallbackQuery):
    data = callback.data.replace("add_", "").split("_")
    product = " ".join(data[:-1])
    price = data[-1]
    
    user_id = callback.from_user.id
    if user_id not in user_carts:
        user_carts[user_id] = []
    
    user_carts[user_id].append({"product": product, "price": price})
    
    await callback.answer(f"✅ {product} savatchaga qo'shildi!", show_alert=True)

# Savatchani ko'rish
@dp.callback_query(F.data == "view_cart")
async def view_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    cart = user_carts.get(user_id, [])
    
    if not cart:
        builder = InlineKeyboardBuilder()
        builder.button(text="🛍️ Xarid qilishni boshlash", callback_data="catalog")
        builder.adjust(1)
        await callback.message.edit_text("🛒 Savatchangiz bo'sh.", reply_markup=builder.as_markup())
        return
    
    text = "🛒 **Sizning savatchangiz:**\n\n"
    total = 0
    for idx, item in enumerate(cart, 1):
        text += f"{idx}. {item['product']} - {item['price']}\n"
        total += int(item['price'].replace("$", ""))
    
    text += f"\nJami: ${total}"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Buyurtma berish", callback_data="checkout")
    builder.button(text="🗑️ Savatchani tozalash", callback_data="clear_cart")
    builder.button(text="🔙 Katalogga qaytish", callback_data="catalog")
    builder.adjust(1)
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=builder.as_markup())
    await callback.answer()

# Savatchani tozalash
@dp.callback_query(F.data == "clear_cart")
async def clear_cart(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_carts[user_id] = []
    await callback.message.edit_text("🗑️ Savatcha tozalandi.", reply_markup=InlineKeyboardBuilder().button(text="🛍️ Katalog", callback_data="catalog").as_markup())
    await callback.answer()

# Buyurtmani rasmiylashtirishni boshlash (Ism so'rash)
@dp.callback_query(F.data == "checkout")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Ism va familiyangizni kiriting:")
    await state.set_state(OrderState.waiting_for_name)
    await callback.answer()

@dp.message(OrderState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    # Telefon raqamni ulash uchun tugma
    builder = ReplyKeyboardBuilder()
    builder.button(text="📱 Telefon raqamni yuborish", request_contact=True)
    builder.adjust(1)
    
    await message.answer("Telefon raqamingizni yuboring (tugmani bosing yoki yozib yuboring):", reply_markup=builder.as_markup())
    await state.set_state(OrderState.waiting_for_phone)

@dp.message(OrderState.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    await message.answer("Yetkazib berish manzilini kiriting (shahar, ko'cha, uy raqami):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(OrderState.waiting_for_address)

@dp.message(OrderState.waiting_for_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Yetkazib berish manzilini kiriting (shahar, ko'cha, uy raqami):", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(OrderState.waiting_for_address)

@dp.message(OrderState.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    address = message.text
    data = await state.get_data()
    
    name = data.get("name")
    phone = data.get("phone")
    user_id = message.from_user.id
    
    cart = user_carts.get(user_id, [])
    
    order_text = f"🚨 **Yangi buyurtma!**\n\n" \
                 f"👤 Mijoz: {name}\n" \
                 f"📞 Tel: {phone}\n" \
                 f"📍 Manzil: {address}\n\n" \
                 f"🛒 **Mahsulotlar:**\n"
    
    total = 0
    for item in cart:
        order_text += f"- {item['product']} ({item['price']})\n"
        total += int(item['price'].replace("$", ""))
    
    order_text += f"\n💰 **Jami summa: ${total}**"
    
    # Adminga yuborish
    try:
        await bot.send_message(ADMIN_ID, order_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Adminga yuborishda xatolik: {e}")
    
    # Mijozga javob
    await message.answer("Rahmat! Buyurtmangiz qabul qilindi. Tez orada operatorlarimiz siz bilan bog'lanishadi.")
    
    # Savatchani tozalash va holatni yakunlash
    user_carts[user_id] = []
    await state.clear()

# Bog'lanish bo'limi
@dp.callback_query(F.data == "contact")
async def show_contact(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Orqaga", callback_data="back_home")
    builder.adjust(1)
    await callback.message.edit_text("📞 Murojaat uchun: @AdminUsername\n📱 Tel: +998 90 123-45-67", reply_markup=builder.as_markup())
    await callback.answer()

# Asosiy menyuga qaytish
@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🛍️ Mahsulotlar katalogi", callback_data="catalog")
    builder.button(text="🛒 Savatcha", callback_data="view_cart")
    builder.button(text="📞 Biz bilan bog'lanish", callback_data="contact")
    builder.adjust(1)
    await callback.message.edit_text("Asosiy menyu:", reply_markup=builder.as_markup())
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
