# config.py:
# ADMIN_ID = <telegram_id>
# PC_URL = 'http://<ip>:<порт>'

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import requests
import config

from SERVER.config import TOKEN

bot = Bot(token=TOKEN)

dp = Dispatcher(bot)

def get_main_keyboard(pc_online: bool):
    status_sticker = '🟢' if pc_online else '🔴'
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton('Обновить', callback_data='refresh'),
        InlineKeyboardButton('Запущенные программы', callback_data='programs'),
    )
    kb.add(InlineKeyboardButton('Управление ПК', callback_data='manage'))
    return kb, status_sticker

def get_manage_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton('Выключить', callback_data='shutdown'),
        InlineKeyboardButton('Перезагрузить', callback_data='reboot'),
        InlineKeyboardButton('Сон', callback_data='sleep'),
        InlineKeyboardButton('Назад', callback_data='back')
    )
    return kb

def check_pc_status():
    try:
        r = requests.get(f"{config.PC_URL}/status", timeout=2)
        if r.status_code == 200:
            return True, r.json()
    except Exception:
        pass
    return False, None

def get_pc_programs():
    try:
        r = requests.get(f"{config.PC_URL}/programs", timeout=2)
        if r.status_code == 200:
            return r.json().get('programs', [])
    except Exception:
        pass
    return []

def send_pc_command(cmd):
    try:
        r = requests.get(f"{config.PC_URL}/{cmd}", timeout=3)
        if r.status_code == 200:
            return True
    except Exception:
        pass
    return False

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    if message.from_user.id != getattr(config, 'ADMIN_ID', None):
        await message.answer("Доступ запрещен.")
        return
    pc_online, info = check_pc_status()
    kb, status_sticker = get_main_keyboard(pc_online)
    text = f"ПК {status_sticker}\n"
    if pc_online:
        uptime = info.get('uptime', 'Неизвестно')
        text += f"Аптайм: {uptime}"
    await message.answer(text, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'refresh')
async def refresh_cb(call: types.CallbackQuery):
    pc_online, info = check_pc_status()
    kb, status_sticker = get_main_keyboard(pc_online)
    text = f"ПК {status_sticker}\n"
    if pc_online:
        uptime = info.get('uptime', 'Неизвестно')
        text += f"Аптайм: {uptime}"
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer('Обновлено')

@dp.callback_query_handler(lambda c: c.data == 'programs')
async def programs_cb(call: types.CallbackQuery):
    pc_online, _ = check_pc_status()
    if not pc_online:
        await call.answer('ПК не в сети', show_alert=True)
        return
    programs = get_pc_programs()
    text = 'Запущенные программы:\n' + ('\n'.join(programs) if programs else 'Нет данных')
    kb, _ = get_main_keyboard(True)
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'manage')
async def manage_cb(call: types.CallbackQuery):
    kb = get_manage_keyboard()
    await call.message.edit_text('Управление ПК:', reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data in ['shutdown', 'reboot', 'sleep'])
async def pc_control_cb(call: types.CallbackQuery):
    cmd = call.data
    ok = send_pc_command(cmd)
    msg = 'Команда выполнена' if ok else 'Ошибка выполнения команды'
    kb = get_manage_keyboard()
    await call.message.edit_text(f'Управление ПК:\n{msg}', reply_markup=kb)
    await call.answer()

@dp.callback_query_handler(lambda c: c.data == 'back')
async def back_cb(call: types.CallbackQuery):
    pc_online, info = check_pc_status()
    kb, status_sticker = get_main_keyboard(pc_online)
    text = f"ПК {status_sticker}\n"
    if pc_online:
        uptime = info.get('uptime', 'Неизвестно')
        text += f"Аптайм: {uptime}"
    await call.message.edit_text(text, reply_markup=kb)
    await call.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
