import discord
from discord.ext import commands, tasks
import util
import ids
import re
import sys
sys.path.insert(1, '../')
import bible
import shelve

GREETING_REGEX = "^([Hh]ello.*|[Hh]i.*)$"

BIBLE_READING_REGEX = ".*[Bb]ible reading plan.*"

BIBLE_DONE_READING_REGEX = ".*[Dd]one\s[Rr]ead.*"

WATER_SUMMARY = ".*water.*summary.*"

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

database = util.setup_data_file_headers('data/water.db')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    content = message.content
    member_id = message.author.id
    uni_key = str(member_id)+" "+str(message.guild.id)

    if content.startswith('\N{CUP WITH STRAW}'):
        await message.add_reaction('\N{CUP WITH STRAW}')
        util.add_one_water_table( message.author.name, message.channel.id,  database )
        
    
    if re.search(GREETING_REGEX, content):
        await message.channel.send('Hello!')

    if re.search(BIBLE_READING_REGEX, content):
        request = content.split()
        book_list = set(bible.complete_books_list)
        intersection = list(book_list.intersection(request))
        if intersection != []:
            book = intersection[0]
            if book not in bible.books_list:
                book = bible.shorted_to_key[book]
        else:
            await message.channel.send('Please try again with the book name! Use - in place of space. For example, 1st-Samuel')
        
        chapters = [int(word) for word in request if word.isdigit()]
        if chapters != []:
            chapter = chapters[0]
        else:
            await message.channel.send('Please try again! Please do not include any punctuations')
        if book != [] and chapters != []:
            respond = util.register_user_to_bible_reading(uni_key, book, int(chapter), message.channel.id)
            await message.channel.send(respond)


    if re.search(BIBLE_DONE_READING_REGEX, content):
        request = content.split()
        
        chapters = [int(word) for word in request if word.isdigit()]
        if chapters != []:
            chapter_num = chapters[0]
        else: chapter_num = 1
        with shelve.open('data/bibleReading') as db:
            if uni_key in db:
                next_book, next_chapter= util.updateBibleReadingPlan(uni_key, chapter_num)
                respond = f"Nice job! Tomorrow you will read Book {next_book} Chapter {next_chapter}"
            else:
                respond = "You have not registered your bible reading plan. Type 'bible reading plan' + book + chapter to start!"
        await message.channel.send(respond)

    if re.search(WATER_SUMMARY, content):
        date = util.get_date()
        try:
            result = util.water_summary_to_list(database, date)
            respond = f"The leader is {result[0][0]} with {result[0][1]} cups of water! \n Here is a complete list of all contestants "
            for user, value in result:
                respond += f"\n {user} with {value} cups"
            await message.channel.send(respond)
        except:
            pass
@tasks.loop(hours=24)
async def called_once_a_day():
    date = util.get_date()
    try:
        (winner, _), winner_value = util.water_summary_find_winner(database, date)
        for channel_id in ids.water_drinking_contest_channels:
            message_channel = client.get_channel(channel_id)
            await message_channel.send(f"The \N{CUP WITH STRAW}winner of {date} is {winner} with {winner_value} cups of water \N{CONFETTI BALL}")
    except:
        pass
        
    try:
        with shelve.open('data/bibleReading') as db:
            for user_data in db.keys():
                book, chapter, channel = db[user_data]
                user = user_data.split()[0]
                reminder = f"Remember to read Book {book} Chapter {chapter}! <@{user}>"
                channel = client.get_channel(channel)
                await channel.send(reminder)
    except: print('oops')

@called_once_a_day.before_loop
async def before():
    await client.wait_until_ready()

called_once_a_day.start()

client.run(ids.token)
