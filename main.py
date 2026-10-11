import os
import asyncio
import discord
import yt_dlp
import imageio_ffmpeg

from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("BOT_OWNER_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch1",
}

FFMPEG_OPTIONS = {
    "before_options": (
        "-reconnect 1 "
        "-reconnect_streamed 1 "
        "-reconnect_delay_max 5"
    ),
    "options": "-vn",
}

ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
play_locks = {}


def is_owner(message):
    return message.author.id == OWNER_ID and OWNER_ID != 0


def get_voice_channel(member):
    if member.voice:
        return member.voice.channel
    return None


async def connect_to(channel):
    guild = channel.guild
    vc = guild.voice_client

    if vc and vc.is_connected():
        if vc.channel != channel:
            await vc.move_to(channel)
        return vc

    return await channel.connect(self_deaf=True, reconnect=True)


async def search_song(query):
    loop = asyncio.get_running_loop()

    def extract():
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            data = ydl.extract_info(
                f"ytsearch1:{query}",
                download=False
            )

            entries = data.get("entries") or []
            if not entries:
                return None

            item = entries[0]
            return {
                "title": item.get("title", "أغنية"),
                "url": item.get("url"),
                "webpage": item.get("webpage_url"),
            }

    return await loop.run_in_executor(None, extract)


@bot.event
async def on_ready():
    print(f"البوت جاهز: {bot.user}")
    print("البوت يعمل وينتظر الأوامر.")


@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    # أوامر التحكم لصاحب البوت فقط
    if not is_owner(message):
        await bot.process_commands(message)
        return

    content = message.content.strip()
    guild = message.guild
    vc = guild.voice_client

    # تشغيل أغنية: ش اسم الأغنية
    if content.startswith("ش "):
        query = content[2:].strip()

        if not query:
            await message.channel.send(
                "اكتب اسم الأغنية بعد الأمر ش"
            )
            return

        channel = get_voice_channel(message.author)

        if not channel:
            await message.channel.send(
                "ادخل روم صوتي أولًا عشان أجيك."
            )
            return

        try:
            vc = await connect_to(channel)

            async with message.channel.typing():
                song = await search_song(query)

            if not song or not song["url"]:
                await message.channel.send(
                    "ما لقيت الأغنية المطلوبة."
                )
                return

            if vc.is_playing() or vc.is_paused():
                vc.stop()

            source = discord.FFmpegPCMAudio(
                song["url"],
                executable=ffmpeg_path,
                **FFMPEG_OPTIONS
            )

            vc.play(source)

            await message.channel.send(
                f"🎶 شغّلت **{song['title']}** "
                f"في روم **{channel.name}**"
            )

        except Exception as error:
            await message.channel.send(
                f"تعذر تشغيل الأغنية: {error}"
            )

        return

    # الدخول إلى رومك الصوتي: تعال
    if content == "تعال":
        channel = get_voice_channel(message.author)

        if not channel:
            await message.channel.send(
                "ادخل الروم الصوتي أولًا."
            )
            return

        try:
            await connect_to(channel)
            await message.channel.send(
                f"دخلت روم **{channel.name}** وببقى فيه."
            )
        except Exception as error:
            await message.channel.send(
                f"تعذر دخول الروم: {error}"
            )

        return

    # الانتقال إلى روم بالاسم: روح اسم الروم
    if content.startswith("روح "):
        channel_name = content[4:].strip()

        channel = discord.utils.find(
            lambda c: c.name.casefold() == channel_name.casefold(),
            guild.voice_channels
        )

        if not channel:
            await message.channel.send(
                "ما لقيت روم صوتي بهذا الاسم."
            )
            return

        try:
            await connect_to(channel)
            await message.channel.send(
                f"انتقلت إلى روم **{channel.name}**."
            )
        except Exception as error:
            await message.channel.send(
                f"تعذر الانتقال: {error}"
            )

        return

    # إيقاف مؤقت مع البقاء في الروم
    if content == "وقف":
        if vc and vc.is_playing():
            vc.pause()
            await message.channel.send(
                "⏸️ وقفت الأغنية مؤقتًا وباقي في الروم."
            )
        else:
            await message.channel.send(
                "ما فيه أغنية شغالة حاليًا."
            )
        return

    # استئناف الأغنية
    if content == "كمل":
        if vc and vc.is_paused():
            vc.resume()
            await message.channel.send("▶️ رجعنا نسمع!")
        else:
            await message.channel.send(
                "ما فيه أغنية متوقفة مؤقتًا."
            )
        return

    # إيقاف الصوت دون الخروج
    if content == "اسكت":
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await message.channel.send(
                "⏹️ انتهى التشغيل وبقيت في الروم."
            )
        return

    # الخروج بأمر منك
    if content == "ط":
        if vc:
            await vc.disconnect(force=True)
            await message.channel.send(
                "👋 طلعت من الروم بأمرك."
            )
        else:
            await message.channel.send(
                "أنا مو داخل أي روم صوتي."
            )
        return

    await bot.process_commands(message)


if not TOKEN:
    raise RuntimeError("أضف DISCORD_TOKEN في متغيرات البيئة.")

bot.run(TOKEN)
