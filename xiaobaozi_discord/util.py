from sqlite3 import Connection, connect
import json, os
from datetime import datetime
from collections import Counter
import bible
import shelve

water_tracking_fmt = {
    "user": "TEXT",
    "channel": "TEXT",
    "date": "TEXT",
    "time": "TEXT",
}

def setup_data_file_headers(
    out: str
):
    if os.path.exists(out):
        return connect(out)
    
    # If directory doesn't exist, can't connect
    # Don't check disk for in-memory database
    if out != ":memory:":
        os.makedirs(os.path.dirname(out), exist_ok = True)

    # only if database doesn't exist 
    table = ""
    for key in water_tracking_fmt.keys():
        table += f"{key} {water_tracking_fmt[key]}, "
    
    create_db = f"CREATE TABLE water ({table[:-2]});"
    database = connect(out)  
    database.execute(create_db)
    database.commit()
    return database
    
def add_one_water_table(user:str, channel, db: Connection):
    insert = f"INSERT INTO water VALUES ({ ('?,' * len(water_tracking_fmt))[:-1]})"
    db.execute(insert, (user,  channel, get_date(), get_time()))
    db.commit()

def get_date():
    return datetime.now().strftime("%Y/%m/%d")

def get_time():
    return datetime.now().strftime("%Y/%m/%d %H:%M:%S")

def water_summary(db, date):
    select = f"SELECT * FROM water WHERE date='{date}'"
    print(select)
    cur = db.cursor()
    result = cur.execute(select).fetchall()
    cleaned_result = Counter([(user, channel) for user, channel, date, time in result])
    if cleaned_result != Counter():
        winner, winner_value = cleaned_result.most_common()[0]
        return winner, winner_value



"""Register user to the bibleReading database"""
def register_user_to_bible_reading(user_id, book, chapter, channel_id):
    if chapter <= bible.chapters_of_book[book]:
        with shelve.open('data/bibleReading') as db:
            db[user_id] = [book, chapter, channel_id]
        print("sucessfully register!")
        return "Welcome to Bible reading daily plan! \nI will remind you every 24 hours!\n Please remember to read {} Chapter {} today!".format(book, chapter)
    else:
        return "Please enter a valid chapter number"
   
"""after user has finished the reading plan of the day,
update the bible reading plan in the data base for next day's reading plan"""
def updateBibleReadingPlan(user_id, num_chapters=1):
    with shelve.open('data/bibleReading') as db:
        [book, chapter, channel] = db[user_id]
        nextBook, nextChapter = ("",0)
        for i in range(num_chapters):
            nextBook, nextChapter = getNextBookAndChapter(book, int(chapter))
            book = nextBook
            chapter = nextChapter 
        
        db[user_id] = [nextBook, nextChapter, channel]
        print("bible reading plan updated")
        return nextBook, nextChapter

"""a helper function for updateBileReadingPlan, to get the book
to read for the next day. If there are more chapters left in the book, 
the next book is the same book. If there is no more chapter left to read,
the next day's book is the next book in the bible. If there are no more
book in the bible, the next book is genesis"""
def getNextBookAndChapter(book, chapter):
    last_chapter = bible.chapters_of_book[book]
    if last_chapter > chapter:
        nextbook = book
        nextChapter = chapter + 1
    else:
        if book == 'Revelation':
            nextbook = 'Genesis'
        else:
            nextbook = bible.books_list[bible.books_list.index(book)+1]
        nextChapter = 1
    return nextbook, nextChapter