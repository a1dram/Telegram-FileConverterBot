import os
import subprocess

from converterDB import *
from PIL import Image

from rembg import remove


async def remove_background(image_pass):
    image = Image.open(image_pass)
    output = remove(image)
    output.save('no_background_image.png')


def convert_in_video(user_id, file_name, format):
    new_file = f"{file_name[:file_name.find('.')]}."

    # ffmpeg_cmd = [
    #     'ffmpeg',
    #     '-i',
    #     file_name,
    #     '-c:v', 'libx264',
    #     new_file
    # ]

    # ffmpeg_cmd = [
    #     'ffmpeg',
    #     '-i',
    #     file_name,
    #     '-vcodec', 'copy', '-acodec', 'copy',
    #     new_file
    # ]

    if format.lower() == 'webm':
        ffmpeg_cmd = [
            'ffmpeg',
            '-i',
            file_name,
            new_file + format
        ]

    elif 'tgs' in file_name:

        ffmpeg_cmd = [
            'ffmpeg',
            '-i',
            file_name,
            new_file + 'gif'
        ]

        subprocess.run(ffmpeg_cmd, check=True)

        ffmpeg_cmd = [
            'ffmpeg',
            '-i',
            new_file + 'gif',
            new_file + format
        ]

    else:
        ffmpeg_cmd = [
            'ffmpeg',
            '-i',
            file_name,
            '-vcodec', 'copy', '-acodec', 'copy',
            new_file + format
        ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)

    except subprocess.CalledProcessError:
        os.remove(new_file + format)

        ffmpeg_cmd = [
            'ffmpeg',
            '-i',
            file_name,
            '-c:v', 'libx264',
            new_file + format
        ]

        subprocess.run(ffmpeg_cmd, check=True)

    db.add_new_file_title(user_id, new_file + format)


def convert_in_gif(user_id, file_name, speed):
    new_file = f"{file_name[:file_name.find('.')]}"

    ffmpeg_cmd = [
        'ffmpeg',
        '-i',
        file_name,
        '-r', str(speed),
        '-vf', 'scale=320:-1',
        new_file + '.gif'
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    db.add_new_file_title(user_id, new_file + '.gif')


def reconvert_mp3(user_id, file_name, new_file, bitrate):
    ffmpeg_cmd = [
        'ffmpeg',
        '-i', file_name,
        '-vn',
        '-acodec', 'libmp3lame',
        '-ab', f'{bitrate}k',
        '-ar', '44100',
        '-y',
        new_file
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    db.add_new_file_title(user_id, new_file)


def convert_in_audio(user_id, file_name, format):
    new_file = f"{file_name[:file_name.find('.')]}.{format.lower()}"

    if format == 'MP3':
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', file_name,
            '-vn',
            '-acodec', 'libmp3lame',
            '-ab', '192k',
            '-ar', '44100',
            '-y',
            new_file
        ]

    else:
        ffmpeg_cmd = [
            'ffmpeg',
            '-i',
            file_name,
            new_file
        ]

    subprocess.run(ffmpeg_cmd, check=True)

    db.add_new_file_title(user_id, new_file)


def convert_in_photo(user_id, file_name, file_format):
    file_format = file_format.lower()
    new_file = f"{file_name[:file_name.find('.')]}.{file_format}"

    if file_format == 'pdf':
        Image.open(file_name).save(new_file, "PDF", resolution=100.0, save_all=True)

    elif file_format == 'ico':
        ffmpeg_cmd = [
            'ffmpeg',
            '-i',
            file_name,
            '-vf', 'scale=256:-1',
            new_file
        ]

        subprocess.run(ffmpeg_cmd, check=True)

    else:
        print(file_name, new_file)
        ffmpeg_cmd = [
            'ffmpeg',
            '-i',
            file_name,
            new_file
        ]

        subprocess.run(ffmpeg_cmd, check=True)

    db.add_new_file_title(user_id, new_file)


def set_file_name(user_id, m_caption, format_type, own_file_name, file_type):
    try:
        if 'name:' in m_caption:
            file_name = m_caption[m_caption.find('name:') + 5:]

            for i in file_name:
                if i in '\/:*?"<>|.':
                    file_name = file_name.replace(i, '_')

            spaces = ''
            for j in file_name:
                if j == ' ':
                    spaces += ' '

                else:
                    file_name.replace(spaces, '')

            file_name += '.' + format_type.lower()

            if len(file_name) > 60:
                raise TypeError

            else:
                db.add_file_title(user_id, file_name)

        else:
            raise TypeError

    except TypeError:
        file_name = own_file_name or f'{file_type}.' + format_type.lower()

        db.add_file_title(user_id, file_name)


def change_file_quality(user_id, file_name, new_file_name, quality):
    ffmpeg_cmd = [
        'ffmpeg',
        '-i',
        file_name, '-vf', f'scale={quality}',
        new_file_name
    ]

    subprocess.run(ffmpeg_cmd, check=False)

    db.add_new_file_title(user_id, new_file_name)


def distort_media_gradus(user_id, file_name, file_format, degrees):
    file_format = file_format.lower()

    ffmpeg_cmd = [
        'ffmpeg',
        '-i',
        file_name + f".{file_format}",
        '-vf', f'rotate=-{degrees}*PI/180',
        file_name + f'_.{file_format}'
    ]

    subprocess.run(ffmpeg_cmd, check=False)

    db.add_new_file_title(user_id, file_name + f'_.{file_format}')


def flip_file(user_id, file_name, file_format, flip):
    file_format = file_format.lower()

    ffmpeg_cmd = [
        'ffmpeg',
        '-i',
        file_name + f".{file_format}",
        '-vf', flip,
        file_name + f'_.{file_format}'
    ]

    subprocess.run(ffmpeg_cmd, check=False)

    db.add_new_file_title(user_id, file_name + f'_.{file_format}')


def merging_video_and_audio(user_id, video_file, audio_file, new_file_name):
    ffmpeg_cmd = [
        'ffmpeg',
        '-i',
        video_file,
        '-i',
        audio_file,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        new_file_name
    ]

    subprocess.run(ffmpeg_cmd, check=False)

    db.add_new_file_title(user_id, new_file_name)


def file_remove_sound(user_id, file_name, file_format):
    ffmpeg_cmd = [
        'ffmpeg',
        '-i',
        file_name + f".{file_format}",
        '-an', '-vcodec',
        'copy',
        file_name + f"_.{file_format}"
    ]

    subprocess.run(ffmpeg_cmd, check=False)

    db.add_new_file_title(user_id, file_name + f"_.{file_format}")
