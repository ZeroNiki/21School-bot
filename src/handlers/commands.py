"""
Base commands for bot
"""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

rt = Router()


@rt.message(CommandStart())
async def command_start(message: Message):
    await message.answer("Start")


@rt.message(Command("help"))
async def help_message(message: Message):
    await message.answer("Help")
