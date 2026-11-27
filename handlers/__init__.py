from aiogram import Router
from handlers.user import user_router
from handlers.admin import admin_router

main_router = Router()
main_router.include_router(admin_router)
main_router.include_router(user_router)
