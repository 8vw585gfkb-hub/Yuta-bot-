import os
import discord
from discord.ext import commands
import yt_dlp
import imageio_ffmpeg

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTS = {'format': 'bestaudio', 'noplaylist': True}
FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f'البوت {bot.user.name} جاهز وشغال تمام!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # أمر التشغيل المباشر
    if message.content.startswith('ش '):
        search = message.content[2:].strip()
        
        # البحث عن العضو في الرومات الصوتية بالسيرفر
        user_channel = None
        for channel in message.guild.voice_channels:
            if message.author in channel.members:
                user_channel = channel
                break

        if not user_channel:
            try:
                member = message.guild.get_member(message.author.id) or await message.guild.fetch_member(message.author.id)
                if member.voice and member.voice.channel:
                    user_channel = member.voice.channel
            except Exception:
                pass

        if not user_channel:
            await message.channel.send("يا غالي، ادخل أي روم صوتي عشان أجيك ونطرب مع بعض!")
            return

        vc = message.guild.voice_client

        try:
            if vc and vc.is_connected():
                if vc.channel != user_channel:
                    await vc.move_to(user_channel)
            else:
                vc = await user_channel.connect()
        except Exception as e:
            await message.channel.send("ما قدرت أدخل الروم الصوتي! تأكد من صلاحيات البوت.")
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
                    await message.channel.send("ما قدرت أجيب الصوت من اليوتيوب يا غالي!")
                    return

        if vc.is_playing():
            vc.stop()

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_executable()
        vc.play(discord.FFmpegPCMAudio(executable=ffmpeg_path, source=url, **FFMPEG_OPTS))
        await message.channel.send(f'🎶 أبشر، جيت معك في روم **{user_channel.name}** وشغلت: **{title}**')
        return

    # أمر الخروج
    if message.content == 'ط':
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            await message.channel.send('🔴 أبشر، طلعت من الروم.')
        return

    await bot.process_commands(message)

bot.run(os.getenv('DISCORD_TOKEN'))
