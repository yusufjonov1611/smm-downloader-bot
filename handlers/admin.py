import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID, ADMIN_USERNAME, SUPPORT_CHAT_LINK
from database import get_statistics, get_all_user_ids
from keyboards import get_admin_keyboard, get_broadcast_confirm_keyboard

admin_router = Router()

class BroadcastState(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()

@admin_router.message(Command("admin"))
@admin_router.message(F.text == "⚙️ Admin Panel")
async def cmd_admin(message: Message, state: FSMContext):
    """Admin panel bosh menyusi."""
    if message.from_user.id != ADMIN_ID:
        return

    await state.clear()
    await message.answer(
        "🛠 <b>Admin Panelga xush kelibsiz!</b>\n\n"
        "Quyidagi bo'limlardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )

@admin_router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    """Statistikani ko'rsatish."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Ruxsat berilmagan!", show_alert=True)
        return

    stats = await get_statistics()
    text = (
        "📊 <b>Bot Statistikasi:</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b> ta\n"
        f"🆕 Bugun qo'shilganlar: <b>{stats['today_users']}</b> ta\n"
        f"📥 Jami muvaffaqiyatli yuklashlar: <b>{stats['total_downloads']}</b> ta\n"
        f"⚡️ Bugungi yuklashlar: <b>{stats['today_downloads']}</b> ta\n"
        f"💾 Keshdagi fayllar (Tezkor baza): <b>{stats.get('cached_files', 0)}</b> ta\n"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_keyboard())
    await callback.answer()

@admin_router.callback_query(F.data == "admin_contact_info")
async def cb_admin_contact(callback: CallbackQuery):
    """Admin aloqa sozlamalari ko'rinishi."""
    if callback.from_user.id != ADMIN_ID:
        return

    contact_text = (
        "📞 <b>Admin va Muhokama ma'lumotlari:</b>\n\n"
        f"🆔 Admin ID: <code>{ADMIN_ID}</code>\n"
        f"👤 Admin Username: <b>{ADMIN_USERNAME or 'Kiritilmagan'}</b>\n"
        f"💬 Muhokama guruhi/kanal: <b>{SUPPORT_CHAT_LINK or 'Kiritilmagan'}</b>\n\n"
        "<i>Bularni o'zgartirish uchun <code>.env</code> faylidagi ADMIN_USERNAME va SUPPORT_CHAT_LINK parametrlarini tahrirlashingiz mumkin.</i>"
    )
    await callback.message.edit_text(contact_text, parse_mode="HTML", reply_markup=get_admin_keyboard())
    await callback.answer()

@admin_router.callback_query(F.data == "admin_close")
async def cb_admin_close(callback: CallbackQuery, state: FSMContext):
    """Admin panelni yopish."""
    if callback.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await callback.message.delete()
    await callback.answer("Admin panel yopildi.")

@admin_router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    """Xabar tarqatishni boshlash."""
    if callback.from_user.id != ADMIN_ID:
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await callback.message.edit_text(
        "📢 <b>Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring.</b>\n\n"
        "<i>Matn, rasm, video yoki istalgan xabar turini yuborishingiz mumkin. "
        "Bekor qilish uchun /cancel deb yozing.</i>",
        parse_mode="HTML"
    )
    await callback.answer()

@admin_router.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Admin yuborgan xabarni qabul qilish va tasdiqlashni so'rash."""
    if message.from_user.id != ADMIN_ID:
        return

    if message.text == "/cancel":
        await state.clear()
        await message.answer("Xabar tarqatish bekor qilindi.", reply_markup=get_admin_keyboard())
        return

    await state.update_data(broadcast_message_id=message.message_id, broadcast_chat_id=message.chat.id)
    await state.set_state(BroadcastState.confirm_broadcast)

    await message.reply(
        "👆 <b>Ushbu xabar barcha bot foydalanuvchilariga yuboriladi.</b>\n\n"
        "Tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=get_broadcast_confirm_keyboard()
    )

@admin_router.callback_query(F.data == "broadcast_confirm", BroadcastState.confirm_broadcast)
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Xabarni barcha foydalanuvchilarga yuborish."""
    if callback.from_user.id != ADMIN_ID:
        return

    data = await state.get_data()
    msg_id = data.get("broadcast_message_id")
    chat_id = data.get("broadcast_chat_id")
    await state.clear()

    user_ids = await get_all_user_ids()
    total = len(user_ids)

    status_msg = await callback.message.edit_text(
        f"⏳ <b>Xabar yuborilmoqda...</b>\nJami: {total} ta foydalanuvchi.",
        parse_mode="HTML"
    )

    success_count = 0
    blocked_count = 0

    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=chat_id, message_id=msg_id)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            blocked_count += 1

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"🟢 Yetkazildi: <b>{success_count}</b>\n"
        f"🔴 Yetib bormadi (bloklagan): <b>{blocked_count}</b>\n"
        f"📊 Jami: <b>{total}</b>",
        parse_mode="HTML",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

@admin_router.callback_query(F.data == "broadcast_cancel", BroadcastState.confirm_broadcast)
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Xabar tarqatishni bekor qilish."""
    if callback.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await callback.message.edit_text("❌ Xabar tarqatish bekor qilindi.", reply_markup=get_admin_keyboard())
    await callback.answer()
