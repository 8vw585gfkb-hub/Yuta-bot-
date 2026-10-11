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
    print(f'البوت {bot.user.name} جاهز!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content.startswith('ش '):
        search = message.content[2:].strip()
        
        try:
            member = message.guild.get_member(message.author.id) or await message.guild.fetch_member(message.author.id)
            if not member.voice or not member.voice.channel:
                await message.channel.send("يا غالي، ادخل روم صوتي عشان أجيك ونطرب مع بعض!")
                return
            user_channel = member.voice.channel
        except Exception:
            await message.channel.send("ما قدرت أعرف وين أنت قاعد، تأكد من الصلاحيات!")
            return

        vc = message.guild.voice_client
        
        # إذا البوت متصل بس بروم ثاني، ينقل معك تلقائياً لرومك الجديد
        if vc and vc.is_connected():
            if vc.channel != user_channel:
                await vc.move_to(user_channel)
        else:
            try:
                vc = await user_channel.connect()
            except Exception:
                await message.channel.send("ما قدرت أدخل الروم الصوتي!")
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

        if vc.is_playing():
            vc.stop()

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_executable()
        vc.play(discord.FFmpegPCMAudio(executable=ffmpeg_path, source=url, **FFMPEG_OPTS))
        await message.channel.send(f'🎶 أبشر، جيت معك روم **{user_channel.name}** وشغلت: **{title}**')
        return

    # أمر الخروج لو حبيت تطلعه يدوياً
    if message.content == 'ط':
        if message.guild.voice_client:
            await message.guild.voice_client.disconnect()
            await message.channel.send('🔴 أبشر، طلعت من الروم.')
        return

    await bot.process_commands(message)

bot.run(os.getenv('DISCORD_TOKEN'))
