import aiogram.utils.exceptions
from download_media import set_file_name, change_file_quality, merging_video_and_audio

from callback import *


@dp.message_handler(commands=['start', 'restart'])
async def start(message: Message):
    if db.get_user_id(message.from_user.id) is False and message.from_user.id != 2051400423:
        await bot.send_message(2051400423,
                               f'🔆 <b>{message.from_user.full_name}</b> впервые запустил бота!')

    user_id = message.from_user.id

    db.add_user_id(user_id)
    db.add_user_name(user_id, message.from_user.full_name)
    db.add_language(user_id, 'en')

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton('🇬🇧 English', callback_data='startlangeng'),
                          InlineKeyboardButton('🇷🇺 Русский',
                                               callback_data='startlangrus')]])

    await bot.send_message(message.chat.id, '<b>🌎 Choose your language.</b>', reply_markup=markup)
    await message.delete()


@dp.message_handler(commands=['language'])
async def language(message: Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton('🇬🇧 English', callback_data='eng'),
                                                    InlineKeyboardButton('🇷🇺 Русский',
                                                                         callback_data='rus')]])

    await bot.send_message(message.from_user.id,
                           {"en": "🌎 Choose your language",
                            "ru": "🌎 Выберите язык"}[db.get_language(message.from_user.id)],
                           reply_markup=markup)

    await message.delete()


@dp.message_handler(commands=['info', 'help'])
async def info(message: Message):
    user_language = db.get_language(message.from_user.id)

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton('🔺 ' + {'en': 'Hide', "ru": 'Скрыть'}[user_language],
                                  callback_data='close')]])

    info_message = {"en": "<b>ℹ️ About the bot</b>\n\n"
                          "FileConverterBot is capable of converting video, audio, "
                          "documents, images, video notes and voice messages to any formats.\n\n"
                          "The quality can be changed for all video files, images and audio files in MP3 format.\n\n"
                          'To rename a file, add the description "name: filename" to it. \n\n',

                    "ru": "<b>ℹ️ О боте</b>\n\n"
                          "FileConverterBot способен конвертировать видео, аудио, документы, "
                          "изображения, видеокружки и голосовые сообщения в любые форматы.\n\n"
                          "Качество может быть изменено для всех видеофайлов, изображений и аудиофайлов в "
                          "формате MP3.\n\n"
                          'Чтобы переименовать файл, добавьте к нему описание "name: название". \n\n'}[user_language]

    await bot.send_photo(message.from_user.id, photo=open(f'hello_stickers/fileconverterbot.png', 'rb'),
                         caption=info_message, protect_content=True,
                         reply_markup=markup)

    await message.delete()


@dp.message_handler(content_types=['video'])
async def send_video_file(message: Message):
    user_id = message.from_user.id

    wait_audiotrack = db.get_audiotrack(user_id)
    user_language = db.get_language(user_id)
    wait_quality = db.get_wait_quality(user_id)

    if wait_audiotrack != 'True' and wait_quality != 'True':
        file_id = message.video.file_id

        video_type = message.video.mime_type

        video_format = video_type[video_type.find('/') + 1:]
        video_format = {'quicktime': 'MOV', 'x-matroska': 'MKV', 'mp4': 'MP4', 'avi': 'AVI',
                        'webm': 'WEBM', 'gif': 'GIF'}[video_format]

        db.add_user_name(user_id, message.from_user.full_name)

        db.add_user_id(user_id)
        db.add_file_id(user_id, file_id)
        db.add_file_type(user_id, 'video')
        db.add_file_format(user_id, video_format)

        own_file_name = message.video.file_name
        m_caption = message.caption

        set_file_name(user_id, m_caption, video_format, own_file_name, 'video')

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                      callback_data='edit_file_video/' + video_format)],
                [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                      callback_data='change_format_video/' + video_format)]])

        start_menu = await bot.send_video(user_id,
                                          video=file_id,
                                          caption={'ru': 'Выберите нужный раздел', 'en': 'Select the desired section'}[
                                                      user_language] + ' ↓',
                                          reply_markup=markup)

        sets.user_menu[user_id] = start_menu

        await message.delete()

    elif wait_audiotrack == 'True':
        answer = {'ru': '<b>🛑 Ошибка при получении информации.</b>\n\n'
                        'Отправьте аудиофайл!',

                  'en': '<b>🛑 Error receiving information.</b>\n\n'
                        "Send the audio file!"}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()

    elif wait_quality == 'True':
        answer = {'ru': '<b>🛑 Неправильный формат ввода</b>.\n\n'
                        'Примеры правильного формата: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>',

                  'en': '<b> 🛑 Incorrect input format</b>.\n\n'
                        'Examples of the correct format: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>'}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()


@dp.message_handler(content_types=['audio'])
async def send_video_file(message: Message):
    user_id = message.from_user.id
    file_id = message.audio.file_id

    wait_audiotrack = db.get_audiotrack(user_id)

    if wait_audiotrack == 'False':

        audio_type = message.audio.mime_type
        audio_format = (audio_type[audio_type.find('/') + 1:])

        user_language = db.get_language(user_id)

        if 'aac' in audio_format:
            audio_format = 'AAC'

        if 'mp' in audio_format:
            audio_format = 'MP3'

        if 'wav' in audio_format:
            audio_format = 'WAV'

        if 'flac' in audio_format:
            audio_format = 'FLAC'

        if 'ogg' in audio_format:
            audio_format = 'OGG'

        if audio_format == 'MP3':
            keyboard_buttons = [
                [InlineKeyboardButton({'ru': 'Качество', 'en': 'Quality'}[user_language],
                                      callback_data=F'change_quality_audio/' + audio_format)],
                [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                      callback_data=F'change_format_audio/' + audio_format)]]
            audio_caption = {'ru': 'Выберите нужный раздел', 'en': 'Select the desired section'}[
                                user_language] + ' ↓'


        else:
            if audio_format != 'OGG':
                audio_formats = ['MP3', 'AAC', 'WAV', 'FLAC']

                keyboard_buttons = [
                    [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[0:3]],
                    [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[3:]],
                    [InlineKeyboardButton(f"🗣 Голосовое сообщение", callback_data='aud OGG')],
                ]


            else:
                audio_formats = ['MP3', 'AAC', 'WAV', 'FLAC']

                keyboard_buttons = [
                    [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[0:3]],
                    [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[3:]],
                ]

            audio_caption = {'ru': 'Форматы для конвертирования', 'en': 'Formats for conversion'}[
                                user_language] + ' ↓'

        db.add_user_name(user_id, message.from_user.full_name)

        db.add_user_id(user_id)
        db.add_user_name(user_id, message.from_user.full_name)
        db.add_file_id(user_id, file_id)
        db.add_file_type(user_id, 'audio')
        db.add_file_format(user_id, audio_format)

        own_file_name = message.audio.file_name
        m_caption = message.caption

        set_file_name(user_id, m_caption, audio_format, own_file_name, 'audio')

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        start_menu = await bot.send_audio(user_id, audio=file_id,
                                          caption=audio_caption,
                                          reply_markup=markup)

        sets.user_menu[user_id] = start_menu

        await message.delete()

    else:
        msg = sets.user_menu[message.from_user.id]

        try:
            await bot.edit_message_caption(chat_id=message.chat.id, message_id=msg.message_id,
                                           caption={"en": '<b>💤 You got in line, wait.</b>',
                                                    "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                               db.get_language(message.chat.id)])

        except MessageCantBeEdited:
            msg = await bot.send_message(message.chat.id,
                                         {"en": '<b>💤 You got in line, wait.</b>',
                                          "ru": '<b>💤 Вы вошли в очередь, ожидайте.</b>'}[
                                             db.get_language(message.chat.id)])

        async with async_lock:
            new_msg = None
            user_language = db.get_language(message.from_user.id)

            try:
                answer = {'ru': f"<b>♻️ Добавление аудио дорожки</b>\n\n"
                                f"<b>📹: ◻️ Видео скачивается...\n"
                                f"🔊: ◻️ ...\n"
                                f"📤: ◻️ ...</b>",

                          'en': f"<b> ♻️ Adding an audio track</b>\n\n"
                                f"<b>📹 : ◻️ Video is being downloaded...\n"
                                f"🔊: ◻️ ...\n"
                                f"📤: ◻️ ...</b>"}

                try:
                    await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                   caption=answer[user_language])

                except BadRequest:
                    new_msg = await bot.send_message(message.from_user.id, answer[user_language])

                await message.delete()

                video_name = db.get_file_title(message.from_user.id)

                video_file_id = db.get_file_id(message.from_user.id)
                video_file = await bot.get_file(video_file_id)
                video_file_path = video_file.file_path

                await bot.download_file(video_file_path, video_name)

                answer = {'ru': f"<b>♻️ Добавление аудио дорожки</b>\n\n"
                                f"<b>📹: ✅ Видео скачано.\n"
                                f"🔊: ◻️ Аудио скачивается...\n"
                                f"📤: ◻️ ...</b>",

                          'en': f"<b> ♻️ Adding an audio track</b>\n\n"
                                f"<b>📹 : ✅ Video downloaded.\n"
                                f"🔊: ◻️ Audio is being downloaded...\n"
                                f"📤: ◻️ ...</b>"}

                try:
                    await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                   caption=answer[user_language])

                except BadRequest:
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=new_msg.message_id,
                                                text=answer[user_language])

                audio_file_id = message.audio.file_id
                audio_file = await bot.get_file(audio_file_id)
                audio_file_path = audio_file.file_path

                audio_type = message.audio.mime_type
                audio_format = (audio_type[audio_type.find('/') + 1:]).lower()
                audio_name = 'audio.' + audio_format

                await bot.download_file(audio_file_path, audio_name)

                answer = {'ru': f"<b>♻️ Добавление аудио дорожки</b>\n\n"
                                f"<b>📹: ✅ Видео скачано.\n"
                                f"🔊: ✅ Аудио скачано.\n"
                                f"📤: ◻️ Файлы объединяются...</b>",

                          'en': f"<b> ♻️ Adding an audio track</b>\n\n"
                                f"<b>📹 : ✅ Video downloaded.\n"
                                f" 🔊 : ✅ Audio downloaded.\n"
                                f" 📤 : ◻️ Files are merged...</b>"}

                try:
                    await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                   caption=answer[user_language])

                except BadRequest:
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=new_msg.message_id,
                                                text=answer[user_language])

                video_format = video_name[video_name.find('.'):].lower()
                new_file_name = video_name[:video_name.find('.')] + '_' + video_format

                try:
                    merging_video_and_audio(message.from_user.id, video_name, audio_name, new_file_name)

                    answer = {'ru': f"<b>♻️ Добавление аудио дорожки</b>\n\n"
                                    f"<b>📹: ✅ Видео скачано.\n"
                                    f"🔊: ✅ Аудио скачано.\n"
                                    f"📤: ✅ Файл отправляется.</b>",

                              'en': f"<b> ♻️ Adding an audio track</b>\n\n"
                                    f"<b>📹 : ✅ Video downloaded.\n"
                                    f" 🔊 : ✅ Audio downloaded.\n"
                                    f" 📤 : ✅ File is being sent.</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                       caption=answer[user_language])

                    except BadRequest:
                        await bot.edit_message_text(chat_id=message.from_user.id,
                                                    message_id=new_msg.message_id,
                                                    text=answer[user_language])

                    file_size = os.stat(new_file_name).st_size
                    file_size = "{}{}".format(
                        round(file_size / sets.file_size_format[len(str(file_size))][0], 1),
                        sets.file_size_format[len(str(file_size))][1]
                    )

                    if new_msg is None:
                        await bot.send_document(message.from_user.id, document=open(new_file_name, 'rb'),
                                                caption=f"💾 {file_size},  @FilesConversionBot")

                    else:
                        await bot.send_video_note(message.from_user.id, video_note=open(new_file_name, 'rb'))
                        await new_msg.delete()

                    try:
                        sets.user_menu.pop(message.from_user.id, None)
                    except KeyError:
                        pass

                    await msg.delete()

                    db.add_audiotrack(message.from_user.id, 'False')

                    os.remove(video_name)
                    os.remove(audio_name)
                    os.remove(new_file_name)

                except:
                    db.add_audiotrack(message.from_user.id, 'False')

                    answer = {'ru': f"<b>🛑 Ошибка при редактировании файла.</b>\n\n"
                                    f"Проверьте целостность файлов.",

                              'en': f"<b> 🛑 Error when editing the file.</b>.\n\n"
                                    f"Check the integrity of the files."}

                    try:
                        await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                       caption=answer[user_language])

                    except BadRequest:
                        await bot.edit_message_text(chat_id=message.from_user.id,
                                                    message_id=new_msg.message_id,
                                                    text=answer[user_language])

                        await msg.delete()

                    os.remove(video_name)
                    os.remove(audio_name)
                    os.remove(new_file_name)

            except (FileIsTooBig, aiogram.utils.exceptions.NetworkError):
                db.add_audiotrack(message.from_user.id, 'False')

                answer = {'ru': '<b>🛑 Скачивание файла провалилось.</b>\n\n'
                                'Файл превысил лимит загрузки в 20МБ.',

                          'en': '<b> 🛑 The file download failed.</b>\n\n'
                                "The file has exceeded the download limit of 20 MB."}

                try:
                    await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                   caption=answer[user_language])

                except BadRequest:
                    await bot.edit_message_text(chat_id=message.from_user.id,
                                                message_id=new_msg.message_id,
                                                text=answer[user_language])
                await message.delete()


@dp.message_handler(content_types=['document'])
async def send_video_file(message: Message):
    user_id = message.from_user.id

    wait_audiotrack = db.get_audiotrack(user_id)
    user_language = db.get_language(user_id)
    wait_quality = db.get_wait_quality(user_id)

    if wait_audiotrack != 'True' and wait_quality != 'True':
        file_id = message.document.file_id

        document_type = message.document.mime_type
        document_format = document_type[document_type.find('/') + 1:]

        print(document_type)

        try:
            if 'image' not in document_type and 'application' not in document_type:
                document_format = {'quicktime': 'MOV', 'x-matroska': 'MKV', 'mp4': 'MP4', 'x-msvideo': 'AVI',
                                   'webm': 'WEBM', 'gif': 'GIF'}[document_format]

                file_type = 'video'

                keyboard_button = [
                    [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                          callback_data=F'edit_file_video/' + document_format)],
                    [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                          callback_data=F'change_format_video/' + document_format)]]

            else:
                if 'gif' not in document_type.lower():
                    document_format = {'vnd.adobe.photoshop': 'PSD', 'jpg': 'JPG', 'jpeg': 'JPG', 'png': 'PNG',
                                       'x-icon': 'ICO', 'webp': 'WEBP'}[document_format.lower()]

                    keyboard_button = [
                        [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                              callback_data=F'edit_file_photo/' + document_format)],
                        [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                              callback_data='change_format_photo/' + document_format)]]
                    file_type = 'photo'

                else:
                    file_type = 'GIF'

                    keyboard_button = [
                        [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                              callback_data='edit_file_gif/gif')],
                        [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                              callback_data='change_format_gif')]]

            markup = InlineKeyboardMarkup(
                inline_keyboard=keyboard_button)

            start_menu = await bot.send_document(user_id,
                                                 document=file_id,
                                                 caption=
                                                 {'ru': 'Выберите нужный раздел', 'en': 'Select the desired section'}[
                                                     user_language] + ' ↓',
                                                 reply_markup=markup)

            sets.user_menu[user_id] = start_menu

            await message.delete()

            db.add_user_name(user_id, message.from_user.full_name)

            db.add_user_id(user_id)
            db.add_user_name(user_id, message.from_user.full_name)
            db.add_file_id(user_id, file_id)
            db.add_file_type(user_id, file_type)
            db.add_file_format(user_id, document_format)

            own_file_name = message.document.file_name
            m_caption = message.caption

            set_file_name(user_id, m_caption, document_format, own_file_name, file_type)

        except Exception:
            answer = {'ru': '<b>🛑 Ошибка при получении информации</b>.\n\n'
                            f'<b>{document_format.upper()}</b>-файлы на данный момент не поддерживаются.',

                      'en': '<b>🛑 Error receiving information</b>.\n\n'
                            f'<b>{document_format.upper()}</b>-files are not supported at the moment.'}

            await bot.send_message(user_id, answer[user_language])
            await message.delete()

    elif wait_audiotrack == 'True':
        answer = {'ru': '<b>🛑 Ошибка при получении информации.</b>\n\n'
                        'Отправьте аудиофайл!',

                  'en': '<b>🛑 Error receiving information.</b>\n\n'
                        "Send the audio file!"}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()

    elif wait_quality == 'True':
        answer = {'ru': '<b>🛑 Неправильный формат ввода</b>.\n\n'
                        'Примеры правильного формата: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>',

                  'en': '<b> 🛑 Incorrect input format</b>.\n\n'
                        'Examples of the correct format: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>'}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()


@dp.message_handler(content_types=['animation'])
async def send_video_file(message: Message):
    user_id = message.from_user.id

    wait_audiotrack = db.get_audiotrack(user_id)
    user_language = db.get_language(user_id)
    wait_quality = db.get_wait_quality(user_id)

    if wait_audiotrack != 'True' and wait_quality != 'True':
        file_id = message.animation.file_id

        animation_format = 'GIF'

        db.add_user_name(user_id, message.from_user.full_name)

        db.add_user_id(user_id)
        db.add_user_name(user_id, message.from_user.full_name)
        db.add_file_id(user_id, file_id)
        db.add_file_type(user_id, 'GIF')
        db.add_file_format(user_id, animation_format)

        print('GIF')

        own_file_name = message.animation.file_name
        m_caption = message.caption

        set_file_name(user_id, m_caption, animation_format, own_file_name, 'GIF')

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                      callback_data='edit_file_gif/gif')],
                [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                      callback_data='change_format_gif')]])

        start_menu = await bot.send_animation(user_id,
                                              animation=file_id,
                                              caption=
                                              {'ru': 'Выберите нужный раздел', 'en': 'Select the desired section'}[
                                                  user_language] + ' ↓',
                                              reply_markup=markup)

        sets.user_menu[user_id] = start_menu

        await message.delete()

    elif wait_audiotrack == 'True':
        answer = {'ru': '<b>🛑 Ошибка при получении информации.</b>\n\n'
                        'Отправьте аудиофайл!',

                  'en': '<b>🛑 Error receiving information.</b>\n\n'
                        "Send the audio file!"}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()

    elif wait_quality == 'True':
        answer = {'ru': '<b>🛑 Неправильный формат ввода</b>.\n\n'
                        'Примеры правильного формата: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>',

                  'en': '<b> 🛑 Incorrect input format</b>.\n\n'
                        'Examples of the correct format: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>'}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()


@dp.message_handler(content_types=['photo'])
async def send_video_file(message: Message):
    user_id = message.from_user.id

    wait_audiotrack = db.get_audiotrack(user_id)
    user_language = db.get_language(user_id)
    wait_quality = db.get_wait_quality(user_id)

    if wait_audiotrack != 'True' and wait_quality != 'True':
        file_id = message.photo[-1].file_id

        photo_info = await bot.get_file(file_id)
        photo_path = photo_info.file_path
        photo_format = photo_path[photo_path.find('.') + 1:]

        own_file_name = photo_path[photo_path.find('/') + 1:]
        m_caption = message.caption

        db.add_user_name(user_id, message.from_user.full_name)

        db.add_user_id(user_id)
        db.add_user_name(user_id, message.from_user.full_name)
        db.add_file_id(user_id, file_id)
        db.add_file_type(user_id, 'photo')
        db.add_file_format(user_id, photo_format)

        if 'adobe.photoshop' in photo_format.lower():
            photo_format = 'PSD'

        if 'jp' in photo_format.lower():
            photo_format = 'JPG'

        if 'png' in photo_format.lower():
            photo_format = 'PNG'

        if 'web' in photo_format.lower():
            photo_format = 'WEBP'

        print(photo_format)

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                      callback_data=F'edit_file_photo/' + photo_format)],
                [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                      callback_data='change_format_photo/' + photo_format)]])

        set_file_name(user_id, m_caption, photo_format, own_file_name, 'photo')

        start_menu = await bot.send_photo(user_id,
                                          photo=file_id,
                                          caption={'ru': 'Выберите нужный раздел', 'en': 'Select the desired section'}[
                                                      user_language] + ' ↓',
                                          reply_markup=markup)

        sets.user_menu[user_id] = start_menu

        await message.delete()

    elif wait_audiotrack == 'True':
        answer = {'ru': '<b>🛑 Ошибка при получении информации.</b>\n\n'
                        'Отправьте аудиофайл!',

                  'en': '<b>🛑 Error receiving information.</b>\n\n'
                        "Send the audio file!"}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()

    elif wait_quality == 'True':
        answer = {'ru': '<b>🛑 Неправильный формат ввода</b>.\n\n'
                        'Примеры правильного формата: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>',

                  'en': '<b> 🛑 Incorrect input format</b>.\n\n'
                        'Examples of the correct format: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>'}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()


@dp.message_handler(content_types=['sticker'])
async def send_video_file(message: Message):
    user_id = message.from_user.id

    wait_audiotrack = db.get_audiotrack(user_id)
    user_language = db.get_language(user_id)
    wait_quality = db.get_wait_quality(user_id)

    if wait_audiotrack != 'True' and wait_quality != 'True':
        file_id = message.sticker.file_id

        sticker_info = await bot.get_file(file_id)
        sticker_path = sticker_info.file_path
        sticker_format = sticker_path[sticker_path.find('.') + 1:]

        own_file_name = sticker_path[sticker_path.find('/') + 1:]
        m_caption = message.caption

        db.add_user_name(user_id, message.from_user.full_name)

        db.add_user_id(user_id)
        db.add_user_name(user_id, message.from_user.full_name)
        db.add_file_id(user_id, file_id)
        db.add_file_type(user_id, 'sticker')
        db.add_file_format(user_id, sticker_format)

        if 'webp' in sticker_format.lower():
            print('ok')

            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                          callback_data=F'edit_file_photo/' + sticker_format)],
                    [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                          callback_data='change_format_photo/' + sticker_format)]])

        else:

            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                          callback_data=f'edit_file_video/{sticker_format}')],
                    [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                          callback_data=F'change_format_video/' + sticker_format)]])

        set_file_name(user_id, m_caption, sticker_format, own_file_name, 'sticker')

        start_menu = await bot.send_sticker(user_id,
                                            sticker=file_id,
                                            reply_markup=markup)

        sets.user_menu[user_id] = start_menu

        await message.delete()

    elif wait_audiotrack == 'True':
        answer = {'ru': '<b>🛑 Ошибка при получении информации.</b>\n\n'
                        'Отправьте аудиофайл!',

                  'en': '<b>🛑 Error receiving information.</b>\n\n'
                        "Send the audio file!"}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()

    elif wait_quality == 'True':
        answer = {'ru': '<b>🛑 Неправильный формат ввода</b>.\n\n'
                        'Примеры правильного формата: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>',

                  'en': '<b> 🛑 Incorrect input format</b>.\n\n'
                        'Examples of the correct format: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>'}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()


@dp.message_handler(content_types=['voice'])
async def send_video_file(message: Message):
    user_id = message.from_user.id

    user_language = db.get_language(user_id)
    wait_audiotrack = db.get_audiotrack(user_id)
    wait_quality = db.get_wait_quality(user_id)

    if wait_audiotrack != 'True' and wait_quality != 'True':
        file_id = message.voice.file_id

        audio_formats = [i for i in ['MP3', 'AAC', 'WAV', 'FLAC']]
        keyboard_buttons = [
            [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[0:3]],
            [InlineKeyboardButton(f"📟 {i}", callback_data='aud ' + i) for i in audio_formats[3:]]
        ]

        audio_caption = {'ru': 'Форматы для конвертирования', 'en': 'Formats for conversion'}[
                            user_language] + ' ↓'

        db.add_user_name(user_id, message.from_user.full_name)

        db.add_user_id(user_id)
        db.add_user_name(user_id, message.from_user.full_name)
        db.add_file_id(user_id, file_id)
        db.add_file_type(user_id, 'voice')
        db.add_file_format(user_id, 'ogg')

        own_file_name = 'voice.ogg'
        m_caption = message.caption

        set_file_name(user_id, m_caption, 'ogg', own_file_name, 'voice')

        markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        start_menu = await bot.send_audio(user_id, audio=file_id,
                                          caption=audio_caption, reply_markup=markup)

        sets.user_menu[user_id] = start_menu

        await message.delete()

    elif wait_audiotrack == 'True':
        answer = {'ru': '<b>🛑 Ошибка при получении информации.</b>\n\n'
                        'Отправьте аудиофайл!',

                  'en': '<b>🛑 Error receiving information.</b>\n\n'
                        "Send the audio file!"}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()

    elif wait_quality == 'True':
        answer = {'ru': '<b>🛑 Неправильный формат ввода</b>.\n\n'
                        'Примеры правильного формата: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>',

                  'en': '<b> 🛑 Incorrect input format</b>.\n\n'
                        'Examples of the correct format: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>'}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()


@dp.message_handler(content_types=['video_note'])
async def send_video_file(message: Message):
    user_id = message.from_user.id

    user_language = db.get_language(user_id)
    wait_audiotrack = db.get_audiotrack(user_id)
    wait_quality = db.get_wait_quality(user_id)

    if wait_audiotrack != 'True' and wait_quality != 'True':
        file_id = message.video_note.file_id

        file = await bot.get_file(file_id)
        file_path = file.file_path
        own_file_name = file_path[file_path.find('/') + 1:]
        video_note_format = file_path[file_path.find('.') + 1:]

        db.add_user_name(user_id, message.from_user.full_name)

        db.add_user_id(user_id)
        db.add_file_id(user_id, file_id)
        db.add_file_type(user_id, 'video_note')
        db.add_file_format(user_id, video_note_format)

        set_file_name(user_id, '', video_note_format, own_file_name, 'video_note')

        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton({'ru': 'Редактирование', 'en': 'Editing'}[user_language],
                                      callback_data=f'edit_file_video_note/{video_note_format}')],
                [InlineKeyboardButton({'ru': 'Конвертирование', 'en': 'Conversion'}[user_language],
                                      callback_data=f'change_format_video_note/{video_note_format}')]])

        start_menu = await bot.send_video_note(user_id,
                                               video_note=file_id,
                                               reply_markup=markup)

        sets.user_menu[user_id] = start_menu

        await message.delete()

    elif wait_audiotrack == 'True':
        answer = {'ru': '<b>🛑 Ошибка при получении информации.</b>\n\n'
                        'Отправьте аудиофайл!',

                  'en': '<b>🛑 Error receiving information.</b>\n\n'
                        "Send the audio file!"}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()

    elif wait_quality == 'True':
        answer = {'ru': '<b>🛑 Неправильный формат ввода</b>.\n\n'
                        'Примеры правильного формата: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>',

                  'en': '<b> 🛑 Incorrect input format</b>.\n\n'
                        'Examples of the correct format: <b>100x100</b>, '
                        '<b>1920x1080</b>, '
                        '<b>1280x720.</b>'}

        await bot.send_message(message.from_user.id, answer[user_language])
        await message.delete()


@dp.message_handler(content_types=['text'])
async def get_user_answer(message: Message):
    message_text = message.text

    if message_text not in ['/start', '/restart', '/info', '/language']:
        wait_quality = db.get_wait_quality(message.from_user.id)
        wait_audiotrack = db.get_audiotrack(message.from_user.id)

        if wait_quality == 'True':
            async with async_lock:
                new_msg = None

                user_language = db.get_language(message.from_user.id)

                try:
                    file_quality = str(message.text)

                    if 'x' in file_quality or 'х' in file_quality:
                        for i in message.text:
                            if i not in '1234567890xх-.':
                                raise TypeError

                            if i == 'х':
                                file_quality.replace('х', 'x')
                    else:
                        raise TypeError

                    msg = sets.user_menu[message.from_user.id]

                    answer = {'ru': f"<b>♻️ Редактированиe файла</b>\n\n"
                                    f"Разрешение: <b>{file_quality}</b>\n\n"
                                    f"<b>📥: ◻️ Файл скачивается...\n"
                                    f"📤: ◻️ ...</b>",

                              'en': f"<b> ♻️ File Editing</b>\n\n"
                                    f"Resolution: <b>{file_quality}</b>\n\n"
                                    f"<b> 📥 : ◻️ File is being downloaded...\n"
                                    f" 📤 : ◻️ ...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                       caption=answer[user_language])

                    except BadRequest:
                        new_msg = await bot.send_message(message.from_user.id, answer[user_language])

                    await message.delete()

                    file_name = db.get_file_title(message.from_user.id)

                    file_id = db.get_file_id(message.from_user.id)
                    file = await bot.get_file(file_id)
                    file_path = file.file_path

                    await bot.download_file(file_path, file_name)

                    answer = {'ru': f"<b>♻️ Редактирование файла</b>\n\n"
                                    f"Разрешение: <b>{file_quality}</b>\n\n"
                                    f"<b>📥: ✅ Файл скачан.\n"
                                    f"📤: ◻️ Файл редактируется...</b>",

                              'en': f"<b> ♻️ File Editing</b>\n\n"
                                    f"Resolution: <b>{file_quality}</b>\n\n"
                                    f"<b> 📥 : ✅ File downloaded.\n"
                                    f" 📤 : ◻️ File is being edited...</b>"}

                    try:
                        await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                       caption=answer[user_language])

                    except BadRequest:
                        await bot.edit_message_text(chat_id=message.from_user.id,
                                                    message_id=new_msg.message_id,
                                                    text=answer[user_language])

                    file_format = file_name[file_name.find('.'):].lower()
                    new_file_name = file_name[:file_name.find('.')] + '_' + file_format
                    quality = file_quality.replace('x', ':')

                    try:
                        change_file_quality(message.from_user.id, file_name, new_file_name, quality)

                        answer = {'ru': f"<b>♻️ Редактирование файла</b>\n\n"
                                        f"Разрешение: <b>{file_quality}</b>\n\n"
                                        f"<b>📥: ✅ Файл скачан.\n"
                                        f"📤: ✅ Файл отправляется.</b>",

                                  'en': f"<b> ♻️ File Editing</b>\n\n"
                                        f"Resolution: <b>{file_quality}</b>\n\n"
                                        f"<b> 📥 : ✅ File downloaded.\n"
                                        f" 📤 : ✅ File is being sent.</b>"}

                        try:
                            await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                           caption=answer[user_language])

                        except BadRequest:
                            await bot.edit_message_text(chat_id=message.from_user.id,
                                                        message_id=new_msg.message_id,
                                                        text=answer[user_language])

                        file_size = os.stat(new_file_name).st_size
                        file_size = "{}{}".format(
                            round(file_size / sets.file_size_format[len(str(file_size))][0], 1),
                            sets.file_size_format[len(str(file_size))][1]
                        )

                        if new_msg is None:
                            await bot.send_document(message.from_user.id, document=open(new_file_name, 'rb'),
                                                    caption=f"💾 {file_size},  @FilesConversionBot")

                        else:
                            if 'webp' in file_name or 'webm' in file_name or 'tgs' in file_name:
                                await bot.send_sticker(message.from_user.id, sticker=open(new_file_name, 'rb'))

                            else:
                                await bot.send_video_note(message.from_user.id, video_note=open(new_file_name, 'rb'))

                            await new_msg.delete()

                        try:
                            sets.user_menu.pop(message.from_user.id, None)
                        except KeyError:
                            pass

                        await msg.delete()

                        db.add_wait_quality(message.from_user.id, 'False')

                        os.remove(file_name)
                        os.remove(new_file_name)

                    except:
                        db.add_wait_quality(message.from_user.id, 'False')

                        answer = {'ru': f"<b>🛑 Ошибка при редактировании файла.</b>\n\n"
                                        f"Файл не поддерживает данное разрешение.",

                                  'en': f"<b> 🛑 Error when editing the file.</b>.\n\n"
                                        f"The file does not support this resolution."}

                        try:
                            await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                           caption=answer[user_language])

                        except BadRequest:
                            await bot.edit_message_text(chat_id=message.from_user.id,
                                                        message_id=new_msg.message_id,
                                                        text=answer[user_language])

                            await msg.delete()

                        os.remove(file_name)
                        os.remove(new_file_name)

                except TypeError:
                    answer = {'ru': '<b>🛑 Неправильный формат ввода</b>.\n\n'
                                    'Примеры правильного формата: <b>100x100</b>, '
                                    '<b>1920x1080</b>, '
                                    '<b>1280x720.</b>',

                              'en': '<b> 🛑 Incorrect input format</b>.\n\n'
                                    'Examples of the correct format: <b>100x100</b>, '
                                    '<b>1920x1080</b>, '
                                    '<b>1280x720.</b>'}

                    await bot.send_message(message.from_user.id, answer[user_language])
                    await message.delete()

                except (FileIsTooBig, aiogram.utils.exceptions.NetworkError):
                    db.add_wait_quality(message.from_user.id, 'False')

                    answer = {'ru': '<b>🛑 Скачивание файла провалилось.</b>\n\n'
                                    'Файл превысил лимит загрузки в 20МБ.',

                              'en': '<b> 🛑 The file download failed.</b>\n\n'
                                    "The file has exceeded the download limit of 20 MB."}

                    try:
                        await bot.edit_message_caption(chat_id=message.from_user.id, message_id=msg.message_id,
                                                       caption=answer[user_language])

                    except BadRequest:
                        await bot.edit_message_text(chat_id=message.from_user.id,
                                                    message_id=new_msg.message_id,
                                                    text=answer[user_language])
                    await message.delete()

        elif wait_audiotrack == 'True':
            user_language = db.get_language(message.from_user.id)

            answer = {'ru': '<b>🛑 Ошибка при получении информации.</b>\n\n'
                            'Отправьте аудиофайл!',

                      'en': '<b>🛑 Error receiving information.</b>\n\n'
                            "Send the audio file!"}

            await bot.send_message(message.from_user.id, answer[user_language])
            await message.delete()
