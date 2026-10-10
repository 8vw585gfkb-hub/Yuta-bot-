import os
import discord
from discord.ext import commands
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

YDL_OPTS = {'format': 'bestaudio', 'noplaylist': True}
FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f'البوت {bot.user.name} جاهز!')

# أمر التشغيل المختصر: !ش
@bot.command(name='ش')
async def play(ctx, *, search):
    if not ctx.author.voice:
        return await ctx.send("ادخل روم صوتي أولاً!")

    channel = ctx.author.voice.channel
    vc = ctx.voice_client or await channel.connect()

    async with ctx.typing():
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                url, title = info['url'], info['title']
            except Exception:
                return await ctx.send("ما قدرت أجيب الصوت!")

            vc.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTS))
    
    await ctx.send(f'🎵 شغّلت: **{title}**')

# أمر الخروج المختصر: !ط
@bot.command(name='ط')
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send('🛑 تم الخروج.')

# حط التوكن حقك هنا مكان الجملة بين القوسين
bot.run('MTU10DYwMzQ2NDk2Njl3OTlwOQ.G1Zgr9.PQKbUXWovpPIZ1DPa4C8uS28_bGe_fLF0mlХs0')
