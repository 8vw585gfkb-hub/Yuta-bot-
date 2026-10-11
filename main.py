import os
import discord
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTS = {'format': 'bestaudio', 'noplaylist': True}
FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

current_vc = None

@bot.event
async def on_ready():
    global current_vc
    print(f'البوت {bot.user.name} جاهز!')
    
    # أول ما يشتغل البوت، يدخل أول روم صوتي يلاقيه ويجلس فيه للأبد
    for guild in bot.guilds:
        for channel in guild.voice_channels:
            try:
                if not guild.voice_client:
                    current_vc = await channel.connect()
                    print(f'دخلت روم الصوت الجلسة الدائمة: {channel.name}')
                    break
            except Exception as e:
                print(f'خطأ في دخول الروم: {e}')
        if current_vc:
            break

@bot.event
async def on_message(message):
    global current_vc
    if message.author.bot:
        return
    
    # أمر التشغيل المباشر من الشات
    if message.content.startswith('ش '):
        search = message.content[2:].strip()
        
        # لو لأي سبب طلع من الروم، يرجع يدخل تلقائياً
        if not current_vc or not current_vc.is_connected():
            for channel in message.guild.voice_channels:
                try:
                    current_vc = await channel.connect()
                    break
                except Exception:
                    pass

        if not current_vc:
            await message.channel.send("يا غالي ما لقيت روم صوتي أدخله!")
            return

        async with message.channel.typing():
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                try:
                    info = ydl.extract_info(f"ytsearch:{search}", download=False)
                    if 'entries' in info and info['entries']:
                        info = info['entries'][0]
                    url = info.get('url')
                    title = info.get('title', 'مقطع صوتي')
                except Exception:
                    await message.channel.send("ما قدرت أجيب الصوت يا غالي!")
                    return

        if current_vc.is_playing():
            current_vc.stop()

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_executable()
        current_vc.play(discord.FFmpegPCMAudio(executable=ffmpeg_path, source=url, **FFMPEG_OPTS))
        await message.channel.send(f'🎶 أبشر، شغلت لك: **{title}**')
        return

    await bot.process_commands(message)

bot.run(os.getenv('DISCORD_TOKEN'))
