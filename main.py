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

@bot.event
async def on_ready():
    print(f'البوت {bot.user.name} جاهز!')

@bot.command(name='ش')
async def play(ctx, *, search):
    if not ctx.author.voice:
        return await ctx.send("ادخل روم صوتي أولاً!")
    
    channel = ctx.author.voice.channel
    vc = ctx.voice_client or await channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)
                if 'entries' in info and info['entries']:
                    info = info['entries'][0]
                url = info.get('url')
                title = info.get('title', 'مقطع صوتي')
            except Exception:
                return await ctx.send("ما قدرت أجيب الصوت!")

    if vc.is_playing():
        vc.stop()

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_executable()
    vc.play(discord.FFmpegPCMAudio(executable=ffmpeg_path, source=url, **FFMPEG_OPTS))
    await ctx.send(f'🎶 شغلت: **{title}**')

@bot.command(name='ط')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send('🔴 تم الخروج.')

bot.run(os.getenv('DISCORD_TOKEN'))
