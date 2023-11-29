import os
import time

import logging

import aiogram.utils.exceptions
import tgcrypto
import asyncio

import subprocess

from PIL import Image

from aiogram import Bot, types, utils
from aiogram.dispatcher import Dispatcher
from aiogram.types import *
from aiogram.utils.exceptions import *

from converterDB import db
from settings import Settings

from pyrogram import Client, filters
from dotenv import load_dotenv, find_dotenv

from download_media import (convert_in_gif, convert_in_photo, convert_in_video,
                            convert_in_audio, distort_media_gradus, reconvert_mp3, flip_file, file_remove_sound,
                            remove_background)

sets = Settings()

load_dotenv(find_dotenv())
logging.basicConfig(level=logging.INFO)

# api_id = int(os.getenv('api_id'))
# api_hash = os.getenv('api_hash')
#
# client = Client(name='YouTubeBot', api_id=api_id, api_hash=api_hash)
# client.start()

bot = Bot(token=os.getenv('TOKEN'), parse_mode='html')
dp = Dispatcher(bot)

async_lock = asyncio.Lock()


@dp.callback_query_handler(lambda call: True)
async def callback(call):
    if call.message:
        try:
            if 'eng' in call.data:
                if 'start' not in call.data:
                    await bot.answer_callback_query(call.id,
                                                    text='💠 Bot translated into English.',
                                                    cache_time=0)

                    await bot.delete_message(call.message.chat.id, message_id=call.message.message_id)

                await bot.set_my_commands(
                    commands=[
                        BotCommand('restart', 'restart the bot'),
                        BotCommand('language', 'choose language'),
                        BotCommand('info', 'about the bot')
                    ], scope=BotCommandScopeChat(chat_id=call.message.chat.id)
                )
                db.add_language(call.message.chat.id, 'en')

            if 'rus' in call.data:
                if 'start' not in call.data:
                    await bot.answer_callback_query(call.id,
                                                    text='💠 Бот переведён на русский язык.',
                                                    cache_time=0)

                    await bot.delete_message(call.message.chat.id, message_id=call.message.message_id)

                await bot.set_my_commands(
                    commands=[
                        BotCommand('restart', 'перезапустить бота'),
                        BotCommand('language', 'выбрать язык'),
                        BotCommand('info', 'о боте')
                    ], scope=BotCommandScopeChat(chat_id=call.message.chat.id)
                )
                db.add_language(call.message.chat.id, 'ru')

            if 'startlang' in call.data:
                await bot.delete_message(call.message.chat.id, message_id=call.message.message_id)

                start_message = {"en": f"<b>Greetings! I am FileСonverterBot.</b>\n\n"
                                       f"With my help, you can convert files to different formats and also "
                                       f" change their quality.\n\n<b>Send any media file to get started.</b>",
                                 "ru": f"<b>Приветcтвую! Я - FileConverterBot.</b>\n\n"
                                       f"С моей помощью вы можете конвертировать файлы в разные форматы, а также "
                                       f"изменять их качество.\n\n<b>Отправьте любой медиафайл, чтобы начать работу"
                                       f".</b>"}[db.get_language(call.message.chat.id)]

                await bot.send_message(call.message.chat.id, start_message)

            if 'main_back' in call.data:
                data = call.data
                back_format = data[data.find('|') + 1:].upper()
                file_type = data[data.find('/') + 1:data.find('|')]

                user_language = db.get_language(call.message.chat.id)

                db.add_wait_quality(call.message.chat.id, 'False')

                if back_format == 'MP3':
                    first_button_text = {'ru': 'Качество', 'en': 'Quality'}[user_language]
                    first_button = [InlineKeyboardButton(first_button_text,
                                                         callback_data=F'change_quality_audio/MP3')]

                else:
                    first_button_text = {'ru': 'Редактирование', 'en': 'Editing'}[user_language]
                    first_button = [InlineKeyboardButton(first_button_text,
                                                         callback_data=F'edit_file_{file_type}/{back_format}')]

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[first_button,
                                     [InlineKeyboardButton(
                                         {'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                         callback_data=F'change_format_{file_type}/' + back_format)]])

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=
                                                   {'ru': 'Выберите нужный раздел', 'en': 'Select the desired section'}[
                                                       user_language] + ' ↓', reply_markup=markup)
                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'second_back' in call.data:
                user_language = db.get_language(call.message.chat.id)
                video_format = call.data[call.data.find('/') + 1:]

                if video_format.lower() not in ['webm', 'tgs']:
                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton({'ru': 'Видеоформаты', 'en': 'Video formats'}[user_language],
                                                  callback_data='videos' + video_format)],
                            [InlineKeyboardButton({'ru': 'Аудиоформаты', 'en': 'Audio formats'}[user_language],
                                                  callback_data='audios' + video_format)],
                            [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                                  callback_data='main_back/video|' + video_format)]])
                else:
                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton({'ru': 'Видеоформаты', 'en': 'Video formats'}[user_language],
                                                  callback_data='videos' + video_format)],
                            [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                                  callback_data='main_back/video|' + video_format)]])

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=
                                                   {'ru': 'Выберите нужный раздел', 'en': 'Select the desired section'}[
                                                       user_language] + ' ↓', reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'edit' in call.data:
                edit_data = call.data

                db.add_audiotrack(call.message.chat.id, 'False')
                db.add_wait_quality(call.message.chat.id, 'False')

                user_language = db.get_language(call.message.chat.id)
                media_type = edit_data[edit_data.find('file_') + 5:edit_data.find('/')]
                file_format = edit_data[edit_data.find('/') + 1:]

                add_audio_way = []
                if 'video' in media_type:
                    add_audio_way = [InlineKeyboardButton(
                        {'ru': 'Звук', 'en': 'Sound'}[user_language],
                        callback_data=f'sound_file_{media_type}/{file_format}')]

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            {'ru': 'Разрешение', 'en': 'Resolution'}[user_language],
                            callback_data=f'change_quality_{media_type}/{file_format}')],
                        add_audio_way,
                        [InlineKeyboardButton({'ru': 'Искажение', 'en': 'Distortion'}[user_language],
                                              callback_data=f'distort_file_{media_type}/{file_format}')],

                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data=f'main_back/{media_type}|{file_format}')]
                    ])

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=
                                                   {'ru': 'Выберите нужный раздел',
                                                    'en': 'Select the desired section'}[
                                                       user_language] + ' ↓', reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'sound' in call.data:
                edit_data = call.data

                user_language = db.get_language(call.message.chat.id)
                media_type = edit_data[edit_data.find('file_') + 5:edit_data.find('/')]
                file_format = edit_data[edit_data.find('/') + 1:]

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                                {'ru': 'Добавить аудио дорожку', 'en': 'Add an audio track'}[user_language],
                                callback_data=f'add_audiotrack_{media_type}/{file_format}')],

                        [InlineKeyboardButton({'ru': 'Убрать звук', 'en': 'Remove the sound'}[user_language],
                                              callback_data=f'remove_snd_{media_type}/{file_format}')],

                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data=f'edit_back_file_{media_type}/{file_format}')]
                    ])
                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=
                                                   {'ru': 'Выберите действие', 'en': 'Select the action'}[
                                                       user_language] + ' ↓', reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'distort_' in call.data:
                edit_data = call.data

                user_language = db.get_language(call.message.chat.id)
                media_type = edit_data[edit_data.find('file_') + 5:edit_data.find('/')]
                file_format = edit_data[edit_data.find('/') + 1:]

                photo_no_background = []
                if media_type == "photo":
                    photo_no_background = [InlineKeyboardButton(
                            {'ru': 'Убрать задний фон', 'en': 'Remove the background'}[user_language],
                            callback_data=f'no_background_photo/{file_format}')]

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            {'ru': 'Повернуть', 'en': 'Rotate'}[user_language],
                            callback_data=f'rotate_{media_type}/{file_format}')],

                        [InlineKeyboardButton({'ru': 'Отразить', 'en': 'Reflect'}[user_language],
                                              callback_data=f'mirror_{media_type}/{file_format}')],

                        photo_no_background,

                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data=f'edit_back_file_{media_type}/{file_format}')]
                    ])
                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=
                                                   {'ru': 'Выберите действие', 'en': 'Select the action'}[
                                                       user_language] + ' ↓', reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'add_audiotrack' in call.data:
                audiotrack_data = call.data

                db.add_audiotrack(call.message.chat.id, 'True')

                user_language = db.get_language(call.message.chat.id)
                media_type = audiotrack_data[audiotrack_data.find('track_') + 6:audiotrack_data.find('/')]
                file_format = audiotrack_data[audiotrack_data.find('/') + 1:]

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton({'ru': '❌ Отменить и вернуться назад', 'en': '❌ Cancel and go back'}
                                              [user_language],
                                              callback_data=f'sound_back_file_{media_type}/{file_format}')]
                    ])

                track_caption = {'ru': 'Отправьте аудиофайл в чат.', 'en': 'Send an audio file to the chat.'}[
                    user_language]

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=track_caption, reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'mirror_' in call.data:
                rotate_data = call.data

                user_language = db.get_language(call.message.chat.id)
                media_type = rotate_data[rotate_data.find('_') + 1:rotate_data.find('/')]
                file_format = rotate_data[rotate_data.find('/') + 1:]

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(
                            {'ru': 'Отразить вертикально', 'en': 'Flip vertically'}[user_language],
                            callback_data=f'reflect_vertical|{media_type}/{file_format}')],
                        [InlineKeyboardButton(
                            {'ru': 'Отразить горизонтально', 'en': 'Flip horizontally'}[user_language],
                            callback_data=f'reflect_horizontal|{media_type}/{file_format}')],
                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data=f'distort_back_file_{media_type}/{file_format}')]
                    ])

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=
                                                   {'ru': 'Выберите действие',
                                                    'en': 'Select the action'}[
                                                       user_language] + ' ↓', reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'rotate_' in call.data:
                mirror_data = call.data

                user_language = db.get_language(call.message.chat.id)
                media_type = mirror_data[mirror_data.find('_') + 1:mirror_data.find('/')]
                file_format = mirror_data[mirror_data.find('/') + 1:]

                degrees = [45, 90, 135, 180, 225, 270, 315]

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(f"{i}°", callback_data=f'degrees_rotate{i}|{media_type}/{file_format}')
                         for i in
                         degrees[0:3]],
                        [InlineKeyboardButton(f"{i}°", callback_data=f'degrees_rotate{i}|{media_type}/{file_format}')
                         for i in
                         degrees[3:6]],
                        [InlineKeyboardButton(f"{i}°", callback_data=f'degrees_rotate{i}|{media_type}/{file_format}')
                         for i in
                         degrees[6:]],
                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data=f'distort_back_file_{media_type}/{file_format}')]
                    ])

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=
                                                   {'ru': 'Градусы поворота (влево)',
                                                    'en': 'Degrees of rotation (left)'}[
                                                       user_language] + ' ↓', reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'change_format' in call.data:
                if 'video' in call.data and 'note' not in call.data:
                    user_language = db.get_language(call.message.chat.id)
                    video_format = call.data[call.data.find('/') + 1:]

                    if video_format.lower() not in ['webm', 'tgs']:
                        markup = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton({'ru': 'Видеоформаты', 'en': 'Video formats'}[user_language],
                                                      callback_data='videos' + video_format)],
                                [InlineKeyboardButton({'ru': 'Аудиоформаты', 'en': 'Audio formats'}[user_language],
                                                      callback_data='audios' + video_format)],
                                [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                                      callback_data='main_back/video|' + video_format)]])
                    else:
                        markup = InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton({'ru': 'Видеоформаты', 'en': 'Video formats'}[user_language],
                                                      callback_data='videos' + video_format)],
                                [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                                      callback_data='main_back/video|' + video_format)]])

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=
                                                       {'ru': 'Выберите нужный раздел',
                                                        'en': 'Select the desired section'}[
                                                           user_language] + ' ↓', reply_markup=markup)
                    except MessageCantBeEdited:
                        await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                            message_id=call.message.message_id, reply_markup=markup)

                if 'video_note' in call.data:
                    user_language = db.get_language(call.message.chat.id)
                    video_format = call.data[call.data.find('/') + 1:]

                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton({'ru': 'Видеоформаты', 'en': 'Video formats'}[user_language],
                                                  callback_data='videos' + video_format)],
                            [InlineKeyboardButton({'ru': 'Аудиоформаты', 'en': 'Audio formats'}[user_language],
                                                  callback_data='audios' + video_format)],
                            [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                                  callback_data='main_back/video_note|' + video_format)]])

                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

                if 'photo' in call.data:
                    photo_format = call.data[call.data.find('/') + 1:].upper()

                    user_language = db.get_language(call.message.chat.id)

                    if photo_format == 'WEBP':
                        sticker_button = []

                    else:
                        sticker_message = {'ru': '🌄  Стикер', 'en': '🌄  Sticker'}[user_language]
                        sticker_button = [InlineKeyboardButton(sticker_message, callback_data='load_photo WEBP')]

                    photo_formats = [i for i in ['JPG', 'PNG', 'ICO', 'PDF'] if i != photo_format.upper()]

                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(f"🏙  {i}", callback_data='load_photo ' + i) for i in
                             photo_formats[0:3]],
                            [InlineKeyboardButton(f"🏙  {i}", callback_data='load_photo ' + i) for i in
                             photo_formats[3:]],
                            sticker_button,
                            [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                                  callback_data='main_back/photo|' + photo_format)]])
                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=
                                                       {'ru': 'Форматы для конвертирования ↓',
                                                        'en': 'Formats for conversion ↓'}[
                                                           user_language],
                                                       reply_markup=markup)
                    except MessageCantBeEdited:
                        await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                            message_id=call.message.message_id, reply_markup=markup)

                if 'audio' in call.data:
                    audio_formats = [i for i in ['AAC', 'WAV', 'FLAC']]

                    user_language = db.get_language(call.message.chat.id)
                    keyboard_buttons = [
                        [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[0:3]],
                        [InlineKeyboardButton(
                            {'ru': '🗣 Голосовое сообщение', 'en': '🗣 Voice message'}[user_language],
                            callback_data='aud OGG')],
                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data='main_back/audio|MP3')]
                    ]

                    markup = InlineKeyboardMarkup(
                        inline_keyboard=keyboard_buttons)

                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={'ru': 'Форматы для конвертирования',
                                                            'en': 'Formats for conversion'}[user_language] + ' ↓',
                                                   reply_markup=markup)

                if 'gif' in call.data:
                    video_formats = ['MP4', 'MKV', 'AVI', 'WEBM', 'MOV']

                    user_language = db.get_language(call.message.chat.id)

                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(f"📟 {i}", callback_data='vid ' + i) for i in video_formats[0:3]],
                            [InlineKeyboardButton(f"📟 {i}", callback_data='vid ' + i) for i in video_formats[3:]],
                            [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                                  callback_data='main_back/gif|GIF')]
                        ])

                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={'ru': 'Форматы для конвертирования',
                                                            'en': 'Formats for conversion'}[user_language] + ' ↓',
                                                   reply_markup=markup)

            if 'change_quality' in call.data:
                user_language = db.get_language(call.message.chat.id)

                answer = {'ru': '<b>Отправьте нужное разрешение в чат (длина x ширина)</b>.\n\n'
                                'Примеры:  <b>1920x1080</b>,  <b>100x100</b>,  <b>300x800</b>.\n\n'
                                'Eсли хотите сохранить соотношение сторон,'
                                ' то вместо высоты картинки укажите "<b>-1</b>" (также работает и с шириной).\n\n'
                                'Примеры:  <b>1920x-1</b>,  <b>850x-1</b>,  <b>-1x350</b>.',

                          'en': '<b>Send a necessary resolution in the chat (width x height)</b>.\n\n'
                                'Examples:  <b>1920x1080</b>,  <b>100x100</b>,  <b>300x800</b>.\n\n'
                                'If you want to keep the aspect ratio, then specify "<b>-1</b>"'
                                'instead of the image height (also works with width).\n\n'
                                'Examples:  <b>1920x-1</b>,  <b>850x-1</b>,  <b>-1x350</b>.'}

                if 'video' in call.data:
                    video_data = call.data
                    video_format = video_data[video_data.find('/') + 1:]
                    video_type = video_data[video_data.find('quality_') + 8:video_data.find('/')]

                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(
                                {'ru': '❌ Отменить и вернуться назад',
                                 'en': '❌ Cancel and go back'}[user_language],
                                callback_data=f'edit_back_file_{video_type}/' + video_format)]])

                    db.add_wait_quality(call.message.chat.id, 'True')

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language],
                                                       reply_markup=markup)

                    except MessageCantBeEdited:
                        await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                            message_id=call.message.message_id, reply_markup=markup)

                if 'audio' in call.data:
                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton(f"📻 {i}", callback_data='audio_mp3/' + i) for i in
                             ['32', '64', '96']],
                            [InlineKeyboardButton(f"📻 {i}", callback_data='audio_mp3/' + i) for i in
                             ['128', '160', '192']],
                            [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                                  callback_data='main_back/audio|MP3')]])

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption={'ru': '<b>Битрейты аудио ↓</b>',
                                                                'en': '<b>Audio bitrates ↓</b>'}[user_language],
                                                       reply_markup=markup)

                    except MessageCantBeEdited:
                        await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                            message_id=call.message.message_id, reply_markup=markup)

                if 'photo' in call.data:
                    photo_format = call.data[call.data.find('/') + 1:].upper()

                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton({'ru': '❌ Отменить и вернуться назад',
                                                   'en': '❌ Cancel and go back'}[user_language],
                                                  callback_data='edit_back_file_photo/' + photo_format)]])

                    db.add_wait_quality(call.message.chat.id, 'True')
                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language],
                                                       reply_markup=markup)
                    except MessageCantBeEdited:
                        await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                            message_id=call.message.message_id, reply_markup=markup)

                if 'gif' in call.data:
                    markup = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [InlineKeyboardButton({'ru': '❌ Отменить и вернуться назад',
                                                   'en': '❌ Cancel and go back'}[user_language],
                                                  callback_data='edit_back_file_gif/gif')]])

                    db.add_wait_quality(call.message.chat.id, 'True')

                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=answer[user_language],
                                                   reply_markup=markup)

            if 'videos' in call.data or 'cancel' in call.data:
                user_language = db.get_language(call.message.chat.id)

                already_have_format = call.data[6:].upper()
                if already_have_format not in ['WEBM', 'TGS']:
                    video_formats = ['MP4', 'MKV', 'AVI', 'WEBM', 'MOV', 'GIF']
                else:
                    video_formats = ['MP4', 'MKV', 'AVI', 'WEBM', 'MOV']

                video_formats = [i for i in video_formats if i != already_have_format]

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(f"📟 {i}", callback_data='vid ' + i) for i in video_formats[0:3]],
                        [InlineKeyboardButton(f"📟 {i}", callback_data='vid ' + i) for i in video_formats[3:]],
                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data='second_back/' + already_have_format)]
                    ])

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={'ru': 'Форматы для конвертирования ↓',
                                                            'en': 'Formats for conversion ↓'}[user_language],
                                                   reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'audios' in call.data:
                user_language = db.get_language(call.message.chat.id)
                already_have_format = call.data[6:].upper()

                audio_formats = ['MP3', 'AAC', 'WAV', 'FLAC']

                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[0:3]],
                        [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[3:]],
                        [InlineKeyboardButton(f"🗣 Голосовое сообщение", callback_data='aud OGG')],
                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data='second_back/' + already_have_format)]
                    ])

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={'ru': 'Форматы для конвертирования ↓',
                                                            'en': 'Formats for conversion ↓'}[user_language],
                                                   reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'vid ' in call.data and 'GIF' not in call.data.upper():
                msg = None

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={"en": '<b>💤 You got in line, wait.</b>',
                                                            "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                       db.get_language(call.message.chat.id)])
                except MessageCantBeEdited:
                    msg = await bot.send_message(call.message.chat.id,
                                                 {"en": '<b>💤 You got in line, wait.</b>',
                                                  "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                     db.get_language(call.message.chat.id)])

                async with async_lock:
                    bot_message = msg

                    user_language = db.get_language(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Конвертирование видео\n\n"
                                    f"📥: ◻️ Видео скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ Video Conversion\n\n"
                                    f" 📥 : ◻️ Video is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    form = call.data
                    form = form[4:]

                    file_id = db.get_file_id(call.message.chat.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    file_name = db.get_file_title(call.message.chat.id)

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Конвертирование видео\n\n"
                                    f"📥: ✅ Видео скачано.\n"
                                    f"📤: ◻️ Видео конвертируется...</b>",

                              'en': f"<b> ♻️ Video Conversion\n\n"
                                    f" 📥 : ✅ Video downloaded.\n"
                                    f" 📤 : ◻️ Video is being converted...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    convert_in_video(call.message.chat.id, file_name, form)
                    new_file = db.get_new_file_title(call.message.chat.id)

                    file_size = os.stat(new_file).st_size
                    file_size = "{}{}".format(
                        round(file_size / sets.file_size_format[len(str(file_size))][0], 1),
                        sets.file_size_format[len(str(file_size))][1]
                    )

                    answer = {'ru': f"<b>♻️ Конвертирование видео\n\n"
                                    f"📥: ✅ Видео скачано.\n"
                                    f"📤: ✅ Видео отправляется.</b>",

                              'en': f"<b> ♻️ Video Conversion\n\n"
                                    f" 📥 : ✅ Video downloaded.\n"
                                    f" 📤 : ✅ Video is being sent.</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    await bot.send_video(call.message.chat.id,
                                         video=open(new_file, 'rb'),
                                         caption=f"💾 {file_size},  📟 {form},  @FilesConversionBot")

                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    try:
                        await bot_message.delete()

                    except:
                        pass

                    os.remove(file_name)
                    os.remove(new_file)

            if 'aud ' in call.data:
                msg = None

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={"en": '<b>💤 You got in line, wait.</b>',
                                                            "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                       db.get_language(call.message.chat.id)])
                except MessageCantBeEdited:
                    msg = await bot.send_message(call.message.chat.id,
                                                 {"en": '<b>💤 You got in line, wait.</b>',
                                                  "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                     db.get_language(call.message.chat.id)])

                async with async_lock:
                    bot_message = msg

                    user_language = db.get_language(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Конвертирование аудио\n\n"
                                    f"📥: ◻️ Аудио скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ Audio Conversion\n\n"
                                    f" 📥 : ◻️ Audio is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    form = call.data
                    form = form[4:]

                    file_id = db.get_file_id(call.message.chat.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    file_name = db.get_file_title(call.message.chat.id)

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Конвертирование аудио\n\n"
                                    f"📥: ✅ Аудио скачано.\n"
                                    f"📤: ◻️ Аудио конвертируется...</b>",

                              'en': f"<b> ♻️ Audio Conversion\n\n"
                                    f" 📥 : ✅ Audio downloaded.\n"
                                    f" 📤 : ◻️ Audio is being converted...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    convert_in_audio(call.message.chat.id, file_name, form)
                    new_file = db.get_new_file_title(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Конвертирование аудио\n\n"
                                    f"📥: ✅ Аудио скачано.\n"
                                    f"📤: ✅ Аудио отправляется.</b>",

                              'en': f"<b> ♻️ Audio Conversion\n\n"
                                    f" 📥 : ✅ Audio downloaded.\n"
                                    f" 📤 : ✅ Audio is being sent.</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])
                    await bot.send_audio(call.message.chat.id,
                                         audio=open(new_file, 'rb'),
                                         caption=f"@FilesConversionBot")

                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    try:
                        await bot_message.delete()

                    except:
                        pass

                    os.remove(file_name)
                    os.remove(new_file)

            if 'remove_snd' in call.data:
                msg = None

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={"en": '<b>💤 You got in line, wait.</b>',
                                                            "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                       db.get_language(call.message.chat.id)])
                except MessageCantBeEdited:
                    msg = await bot.send_message(call.message.chat.id,
                                                 {"en": '<b>💤 You got in line, wait.</b>',
                                                  "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                     db.get_language(call.message.chat.id)])

                async with async_lock:
                    bot_message = msg

                    user_language = db.get_language(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Редактирование видео\n\n"
                                    f"📥: ◻️ Видео скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ Video Editing\n\n"
                                    f" 📥 : ◻️ Video is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    form = call.data
                    form = form[4:]

                    file_id = db.get_file_id(call.message.chat.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    file_name = db.get_file_title(call.message.chat.id)

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Редактирование видео\n\n"
                                    f"📥: ✅ Видео скачано.\n"
                                    f"📤: ◻️ Видео редактируется...</b>",

                              'en': f"<b> ♻️ Video Editing\n\n"
                                    f" 📥 : ✅ Video downloaded.\n"
                                    f" 📤 : ◻️ Video is being edited...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    form = call.data[call.data.find('/') + 1:].lower()
                    file_title = file_name[:file_name.find('.')]
    
                    file_remove_sound(call.message.chat.id, file_title, form)
                    new_file = db.get_new_file_title(call.message.chat.id)

                    file_size = os.stat(new_file).st_size
                    file_size = "{}{}".format(
                        round(file_size / sets.file_size_format[len(str(file_size))][0], 1),
                        sets.file_size_format[len(str(file_size))][1]
                    )

                    answer = {'ru': f"<b>♻️ Редактирование видео\n\n"
                                    f"📥: ✅ Видео скачано.\n"
                                    f"📤: ✅ Видео отправляется.</b>",

                              'en': f"<b> ♻️ Video Editing\n\n"
                                    f" 📥 : ✅ Video downloaded.\n"
                                    f" 📤 : ✅ Video is being sent.</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    await bot.send_video(call.message.chat.id,
                                         video=open(new_file, 'rb'),
                                         caption=f"💾 {file_size},  @FilesConversionBot")

                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    try:
                        await bot_message.delete()

                    except:
                        pass

                    os.remove(file_name)
                    os.remove(new_file)

            if 'load_photo ' in call.data:
                msg = None

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={"en": '<b>💤 You got in line, wait.</b>',
                                                            "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                       db.get_language(call.message.chat.id)])
                except MessageCantBeEdited:
                    msg = await bot.send_message(call.message.chat.id,
                                                 {"en": '<b>💤 You got in line, wait.</b>',
                                                  "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                     db.get_language(call.message.chat.id)])

                async with async_lock:
                    bot_message = msg

                    user_language = db.get_language(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Конвертирование изображения\n\n"
                                    f"📥: ◻️ Изображение скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ Image Conversion\n\n"
                                    f" 📥 : ◻️ Image is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    form = call.data
                    form = form[11:]

                    file_id = db.get_file_id(call.message.chat.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    file_name = db.get_file_title(call.message.chat.id)

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Конвертирование изображения\n\n"
                                    f"📥: ✅ Изображение скачано.\n"
                                    f"📤: ◻️ Изображение конвертируется...</b>",

                              'en': f"<b> ♻️ Image Conversion\n\n"
                                    f" 📥 : ✅ Image downloaded.\n"
                                    f" 📤 : ◻️ Image is being converted...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    convert_in_photo(call.message.chat.id, file_name, form)
                    new_file = db.get_new_file_title(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Конвертирование изображения\n\n"
                                    f"📥: ✅ Изображения скачано.\n"
                                    f"📤: ✅ Изображения отправляется.</b>",

                              'en': f"<b> ♻️ Image Conversion\n\n"
                                    f" 📥 : ✅ Image downloaded.\n"
                                    f" 📤 : ✅ Image is being sent.</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    await bot.send_document(call.message.chat.id,
                                            document=open(new_file, 'rb'),
                                            caption="@FilesConversionBot")

                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    try:
                        await bot_message.delete()

                    except:
                        pass

                    os.remove(file_name)
                    os.remove(new_file)

            if 'no_background' in call.data:
                msg = None

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={"en": '<b>💤 You got in line, wait.</b>',
                                                            "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                       db.get_language(call.message.chat.id)])
                except MessageCantBeEdited:
                    msg = await bot.send_message(call.message.chat.id,
                                                 {"en": '<b>💤 You got in line, wait.</b>',
                                                  "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                     db.get_language(call.message.chat.id)])

                async with async_lock:
                    bot_message = msg

                    user_language = db.get_language(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Редактирование изображения\n\n"
                                    f"📥: ◻️ Изображение скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ Image Editing\n\n"
                                    f" 📥 : ◻️ Image is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    file_id = db.get_file_id(call.message.chat.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    file_name = db.get_file_title(call.message.chat.id)

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Редактирование изображения\n\n"
                                    f"📥: ✅ Изображение скачано.\n"
                                    f"📤: ◻️ Изображение редактируется...</b>",

                              'en': f"<b> ♻️ Image Editing\n\n"
                                    f" 📥 : ✅ Image downloaded.\n"
                                    f" 📤 : ◻️ Image is being edited...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    await remove_background(file_name)

                    answer = {'ru': f"<b>♻️ Редактирование изображения\n\n"
                                    f"📥: ✅ Изображения скачано.\n"
                                    f"📤: ✅ Изображения отправляется.</b>",

                              'en': f"<b> ♻️ Image Editing\n\n"
                                    f" 📥 : ✅ Image downloaded.\n"
                                    f" 📤 : ✅ Image is being sent.</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    await bot.send_document(call.message.chat.id,
                                            document=open("no_background_image.png", 'rb'),
                                            caption="@FilesConversionBot")

                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    try:
                        await bot_message.delete()

                    except:
                        pass

                    os.remove(file_name)
                    os.remove("no_background_image.png")

            if 'degrees_rotate' in call.data or 'reflect_' in call.data:
                msg = None

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={"en": '<b>💤 You got in line, wait.</b>',
                                                            "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                       db.get_language(call.message.chat.id)])
                except MessageCantBeEdited:
                    msg = await bot.send_message(call.message.chat.id,
                                                 {"en": '<b>💤 You got in line, wait.</b>',
                                                  "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                     db.get_language(call.message.chat.id)])

                async with async_lock:
                    bot_message = msg

                    user_language = db.get_language(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Искажение файла\n\n"
                                    f"📥: ◻️ Файл скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ File Distortion\n\n"
                                    f" 📥 : ◻️ File is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    file_id = db.get_file_id(call.message.chat.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    file_name = db.get_file_title(call.message.chat.id)

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Искажение файла\n\n"
                                    f"📥: ✅ Файл скачан.\n"
                                    f"📤: ◻️ Файл искажается...</b>",

                              'en': f"<b> ♻️ File Distortion\n\n"
                                    f" 📥 : ✅ File downloaded.\n"
                                    f" 📤 : ◻️ File is being distorted...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    form = call.data[call.data.find('/') + 1:].lower()
                    file_title = file_name[:file_name.find('.')]

                    if 'degrees' in call.data:
                        degrees = call.data[call.data.find('rotate') + 6:call.data.find('|')]

                        distort_media_gradus(call.message.chat.id, file_title, form, degrees)

                    elif 'reflect' in call.data:
                        flip = ''
                        if 'vertical' in call.data:
                            flip = 'vflip'

                        elif 'horizontal' in call.data:
                            flip = 'hflip'

                        flip_file(call.message.chat.id, file_title, form, flip)

                    new_file = db.get_new_file_title(call.message.chat.id)

                    answer = {'ru': f"<b>♻️ Искажение файла\n\n"
                                    f"📥: ✅ Файл скачан.\n"
                                    f"📤: ✅ Файл отправляется.</b>",

                              'en': f"<b> ♻️ File Distortion\n\n"
                                    f" 📥 : ✅ File downloaded.\n"
                                    f" 📤 : ✅ File is being sent.</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    await bot.send_document(call.message.chat.id,
                                            document=open(new_file, 'rb'),
                                            caption="@FilesConversionBot")

                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    try:
                        await bot_message.delete()

                    except:
                        pass

                    os.remove(file_name)
                    os.remove(new_file)

            if call.data == 'vid GIF':
                user_language = db.get_language(call.message.chat.id)
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(f"{i} fps", callback_data='load_gif ' + str(i)) for i in [2, 4, 6]],
                        [InlineKeyboardButton(f"{i} fps", callback_data='load_gif ' + str(i)) for i in [8, 10]],
                        [InlineKeyboardButton({'ru': 'Назад', 'en': 'Back'}[user_language] + ' ↩',
                                              callback_data='cancel')]
                    ])

                answer = {"en": 'Frame rate per second ↓',
                          "ru": 'Частота кадров в секунду ↓'}

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=answer[user_language],
                                                   reply_markup=markup)

                except MessageCantBeEdited:
                    await bot.edit_message_reply_markup(chat_id=call.message.chat.id,
                                                        message_id=call.message.message_id, reply_markup=markup)

            if 'load_gif' in call.data:
                msg = None

                try:
                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption={"en": '<b>💤 You got in line, wait.</b>',
                                                            "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                       db.get_language(call.message.chat.id)])
                except MessageCantBeEdited:
                    msg = await bot.send_message(call.message.chat.id,
                                                 {"en": '<b>💤 You got in line, wait.</b>',
                                                  "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                     db.get_language(call.message.chat.id)])

                async with async_lock:
                    bot_message = msg

                    user_language = db.get_language(call.message.chat.id)

                    speed = call.data[9:]
                    speed = int(speed)

                    answer = {'ru': f"<b>♻️ Конвертирование GIF\n\n"
                                    f"📥: ◻️ GIF скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ GIF Conversion\n\n"
                                    f" 📥 : ◻️ GIF is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    file_id = db.get_file_id(call.message.chat.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    file_name = db.get_file_title(call.message.chat.id)

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Конвертирование GIF\n\n"
                                    f"📥: ✅ GIF скачано.\n"
                                    f"📤: ◻️ GIF конвертируется...</b>",

                              'en': f"<b> ♻️ GIF Conversion\n\n"
                                    f" 📥 : ✅ GIF downloaded.\n"
                                    f" 📤 : ◻️ GIF is being converted...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    convert_in_gif(call.message.chat.id, file_name, speed)
                    new_file = db.get_new_file_title(call.message.chat.id)

                    file_size = os.stat(new_file).st_size
                    file_size = "{}{}".format(
                        round(file_size / sets.file_size_format[len(str(file_size))][0], 1),
                        sets.file_size_format[len(str(file_size))][1]
                    )

                    answer = {'ru': f"<b>♻️ Конвертирование GIF\n\n"
                                    f"📥: ✅ GIF скачано.\n"
                                    f"📤: ✅ GIF отправляется.</b>",

                              'en': f"<b> ♻️ GIF Conversion\n\n"
                                    f" 📥 : ✅ GIF downloaded.\n"
                                    f" 📤 : ✅ GIF is being sent.</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                       caption=answer[user_language])

                    except MessageCantBeEdited:
                        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=bot_message.message_id,
                                                    text=answer[user_language])

                    await bot.send_animation(call.message.chat.id,
                                             animation=open(new_file, 'rb'),
                                             caption=f"💾 {file_size},  📟 GIF,  @FilesConversionBot")

                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    try:
                        await bot_message.delete()

                    except:
                        pass

                    os.remove(file_name)
                    os.remove(new_file)

            if 'audio_mp3' in call.data:
                await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                               caption={"en": '<b>💤 You got in line, wait.</b>',
                                                        "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                                   db.get_language(call.message.chat.id)])

                async with async_lock:
                    user_language = db.get_language(call.message.chat.id)

                    bitrate = call.data[call.data.find('/') + 1:]

                    answer = {'ru': f"<b>♻️ Редактирование аудио\n\n"
                                    f"📥: ◻️ Аудио скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ Audio Editing\n\n"
                                    f" 📥 : ◻️ Audio is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=answer[user_language])

                    file_id = db.get_file_id(call.message.chat.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    file_name = db.get_file_title(call.message.chat.id)

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Редактирование аудио\n\n"
                                    f"📥: ✅ Аудио скачано.\n"
                                    f"📤: ◻️ Аудио редактируется...</b>",

                              'en': f"<b> ♻️ Audio Editing\n\n"
                                    f" 📥 : ✅ Audio downloaded.\n"
                                    f" 📤 : ◻️ Audio is being edited...</b>"}

                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=answer[user_language])

                    new_file = file_name[:file_name.find('.')] + '_.mp3'
                    reconvert_mp3(call.message.chat.id, file_name, new_file, bitrate)

                    answer = {'ru': f"<b>♻️ Редактирование аудио\n\n"
                                    f"📥: ✅ Аудио скачано.\n"
                                    f"📤: ✅ Аудио отправляется.</b>",

                              'en': f"<b> ♻️ Audio Editing\n\n"
                                    f" 📥 : ✅ Аудио downloaded.\n"
                                    f" 📤 : ✅ Аудио is being sent.</b>"}

                    await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                                   caption=answer[user_language])

                    await bot.send_audio(call.message.chat.id,
                                         audio=open(new_file, 'rb'),
                                         caption=f"📻 {bitrate} kbps,  @FilesConversionBot")

                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

                    os.remove(file_name)
                    os.remove(new_file)

            if call.data == 'close':
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

        except (FileIsTooBig, aiogram.utils.exceptions.NetworkError):

            answer = {'ru': "<b>🛑 Процесс конвертирования провалился.\n\n"
                            "Файл превысил лимит загрузки в 20МБ.</b>",

                      'en': "<b> 🛑 The conversion process failed.\n\n"
                            "The file has exceeded the download limit of 20MB.</b>"}

            user_language = db.get_language(call.message.chat.id)

            try:
                await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                               caption=answer[user_language])

            except MessageCantBeEdited:
                await bot.send_message(call.message.chat.id, answer[user_language])

            try:
                file_name = db.get_file_title(call.message.chat.id)
                new_file = db.get_new_file_title(call.message.chat.id)

                # os.remove(file_name)
                # os.remove(new_file)
            except:
                pass

        except subprocess.CalledProcessError:
            answer = {'ru': "<b>🛑 Процесс конвертирования провалился.\n\n"
                            "При конвертировании файла произошла ошибка, повторите попытку позже.</b>",

                      'en': "<b> 🛑 The conversion process failed.\n\n"
                            "An error occurred while converting the file, please try again later.</b>"}

            user_language = db.get_language(call.message.chat.id)

            try:
                await bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                               caption=answer[user_language])

            except MessageCantBeEdited:
                await bot.send_message(call.message.chat.id, answer[user_language])

            try:
                file_name = db.get_file_title(call.message.chat.id)
                new_file = db.get_new_file_title(call.message.chat.id)

                os.remove(file_name)
                os.remove(new_file)
            except:
                pass
