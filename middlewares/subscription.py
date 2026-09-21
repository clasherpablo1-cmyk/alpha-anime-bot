import logging
from typing import Callable, Dict, Any, Awaitable, List
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database.db import db
from database.models import RequiredChannel
from keyboards.inline import get_subscription_keyboard

logger = logging.getLogger(__name__)


async def check_user_subscribed(bot, user_id: int, channel_id: str) -> bool:
    """Foydalanuvchining kanalga a'zoligini qat'iy tekshirish"""
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        # Agar foydalanuvchi kanaldan chiqqan yoki haydalgan bo'lsa
        if member.status in ["left", "kicked"]:
            return False
        # creator, administrator, member, restricted bo'lsa — obuna bo'lgan
        return True
    except TelegramBadRequest as e:
        err_msg = str(e).lower()
        # Telegram kanallarida obuna bo'lmagan foydalanuvchi uchun PARTICIPANT_ID_INVALID yoki user not found qaytadi
        if "participant_id_invalid" in err_msg or "user not found" in err_msg:
            return False
        logger.warning(f"Kanalni tekshirishda TelegramBadRequest ({channel_id}): {e}")
        return True
    except Exception as e:
        logger.warning(f"Kanal a'zoligini tekshirishda xatolik ({channel_id}): {e}")
        return True


class SubscriptionCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        bot = data.get("bot")
        user = data.get("event_from_user")

        if not user or not bot:
            return await handler(event, data)

        is_admin = await db.is_admin(user.id)
        data["is_admin"] = is_admin

        # 1. O'tkazib yuboriladigan maxsus holatlar:
        # - /claim_admin yoki admin buyruqlari
        if isinstance(event, Message) and event.text:
            text = event.text.strip()
            if text.startswith("/claim_admin"):
                return await handler(event, data)
            if is_admin and text.startswith("/"):
                return await handler(event, data)

        # - Obunani tekshirish callback tugmasi
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            return await handler(event, data)

        # 2. Kanallarga obunani tekshirish
        channels = await db.get_required_channels()
        unsubscribed_channels: List[RequiredChannel] = []

        for ch in channels:
            is_sub = await check_user_subscribed(bot, user.id, ch.channel_id)
            if not is_sub:
                unsubscribed_channels.append(ch)

        # 3. Agar obuna bo'lmagan kanallar mavjud bo'lsa — bloklash
        if unsubscribed_channels:
            sub_kb = get_subscription_keyboard(unsubscribed_channels)
            warning_text = (
                "⚠️ <b>Botdan to'liq foydalanish uchun quyidagi kanalimizga obuna bo'ling!</b>\n\n"
                "<i>Kanalga a'zo bo'lgach, «✅ Obunani tekshirish» tugmasini bosing.</i>"
            )

            if isinstance(event, Message):
                await event.answer(warning_text, reply_markup=sub_kb, parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ Botdan foydalanish uchun avval kanalga a'zo bo'ling!", show_alert=True)
                if event.message:
                    try:
                        await event.message.answer(warning_text, reply_markup=sub_kb, parse_mode="HTML")
                    except Exception:
                        pass
            return None

        return await handler(event, data)
