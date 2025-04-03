import discord
from discord.ext import commands
import asyncio
import youtube_dl
from youtube_search import YoutubeSearch

bot = commands.Bot(command_prefix='-')

global loop
playlist = [] # n, 0 : 타이틀
                # n, 1 : URL
global i

def set_Embed(title = '', description = ''):
    #embed = discord.Embed(title="메인 제목", description="설명", color=0x62c1cc)
    return discord.Embed(title=title, description=description)

async def song_start(voice, i):
    try:
        if not voice.is_playing() and not voice.is_paused():
            ydl_opts = {'format': 'bestaudio'}
            FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f'https://www.youtube.com{playlist[i][1]}', download=False)
                URL = info['formats'][0]['url']
            
            voice.play(discord.FFmpegPCMAudio(URL, **FFMPEG_OPTIONS))
        #voice.play(discord.FFmpegPCMAudio(executable = './ffmpeg-4.4-full_build-shared/bin/ffmpeg.exe', source='./song.mp3'))

        while voice.is_playing() or voice.is_paused():
            await asyncio.sleep(0.1)
    except:
        return

@bot.event
async def on_ready():
    global loop
    loop = False
    print('봇 시작 완료')


@bot.command(aliases = ['abc'])
async def Qwe(ctx):
    try:
        channel = ctx.author.voice.channel
        if bot.voice_clients == []:
            await channel.connect()
            #await ctx.send("connected to the voice channel, " + str(bot.voice_clients[0].channel))
        voice = bot.voice_clients[0]

        voice.play(discord.FFmpegPCMAudio(executable = './ffmpeg-4.4-full_build-shared/bin/ffmpeg.exe', source='./song.mp4'))


        while voice.is_playing() or voice.is_paused():
            await asyncio.sleep(0.1)
    except:
        pass

@bot.command(aliases = ['q', 'ㅂ'])
async def Que(ctx):
    try:
        queText = ''
        for title in range(len(playlist)):
            try:
                queText = f'{queText}\n' + f'{title + 1}. {playlist[title][0]}'
            except:
                del playlist[title]
        await ctx.send(embed=set_Embed(title='플레이리스트',description=f"{queText}"))
    except:
        pass

@bot.command(aliases = ['remove'])
async def Remove(ctx, arg):
    try:
        global playlist
        remove_song = playlist[int(arg)- 1][0]
        del(playlist[int(arg)- 1])
        global i
        i = i - 1
        if (i + 1) == int(arg) - 1:
            bot.voice_clients[0].stop()
        await ctx.send(embed=set_Embed(title='노래 삭제',description=f"{remove_song}"))
    except:
        await ctx.send('노래 제거중 오류 발생!')

@bot.command(aliases = ['play', 'p', 'ㅔ'])
async def Play(ctx,*,  keyword):
    try:
        results = YoutubeSearch(keyword, max_results=1).to_dict()

        global playlist
        playlist.append([results[0]['title'], results[0]['url_suffix']])
        await ctx.send(embed=set_Embed(title='노래 추가',description=f"{results[0]['title']}"))

        channel = ctx.author.voice.channel
        if bot.voice_clients == []:
            await channel.connect()
            #await ctx.send("connected to the voice channel, " + str(bot.voice_clients[0].channel))
        voice = bot.voice_clients[0]

        if not voice.is_playing() and not voice.is_paused():
            global i
            i = 0
            while True:
                await song_start(voice, i)
                if loop:
                    if i < len(playlist) - 1:
                        i = i + 1 
                    else:
                        i = 0
                    continue
                elif i < len(playlist) - 1:
                    i = i + 1
                    continue
                playlist = [[]]
                break
        #await voice.disconnect()
    except:
        await ctx.send("Play Error")

@bot.command(aliases = ['loop', 'l', 'ㅣ'])
async def Loop(ctx):
    try:
        global loop
        loop = True if loop == False else False # true false 서로 변경
        await ctx.send(f"현재 LOOP 상태: {loop}")
    except:
        await ctx.send("Loop Error")

@bot.command(aliases = ['leave'])
async def Leave(ctx):
    try:
        await bot.voice_clients[0].disconnect()
    except:
        await ctx.send('Leave Error')

@bot.command(aliases = ['skip', 's'])
async def Skip(ctx):
    try:
        bot.voice_clients[0].stop()
    except:
        await ctx.send("Skip Error")

@bot.command(aliases = ['pause'])
async def Pause(ctx):
    try:
        bot.voice_clients[0].pause()
    except:
        await ctx.send("Pause Error")

@bot.command(aliases = ['resume'])
async def Resume(ctx):
    try:
        bot.voice_clients[0].resume()
    except:
        await ctx.send("Resume Error")

@bot.command(aliases = ['save'])
async def Save(ctx, * , arg):
    try:
        with open(f'{arg}.txt','w',encoding='UTF-8') as f:
            global playlist
            f.write(str(playlist))
    except:
        await ctx.send("Save Error") 

@bot.command(aliases = ['open'])
async def Open(ctx, * , arg):
    try:
        with open(f'./{arg}.txt','r',encoding='UTF-8') as f:
            global playlist
            playlist = eval(f.read())

        global i
        await ctx.send(f"플레이리스트 추가 완료\n{arg}")

        channel = ctx.author.voice.channel
        if bot.voice_clients == []:
            await channel.connect()

        voice = bot.voice_clients[0]
        if voice.is_playing() or voice.is_paused():
            i = -1
            bot.voice_clients[0].stop()
        else:
            i = 0
            while True:
                await song_start(voice, i)
                if loop:
                    if i < len(playlist) - 1:
                        i = i + 1 
                    else:
                        i = 0
                    continue
                elif i < len(playlist) - 1:
                    i = i + 1
                    continue
                playlist = [[]]
                break
    

    except:
        await ctx.send("Open Error")

bot.run('')