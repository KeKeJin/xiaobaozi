### Usage
provide a file called `ids.py` that has the following fields:
```
water_drinking_contest_channels = [
    ... # a list of channel ids
]

server_id  # the id of your server

token # the token of your discord bot
```
run the bot:

`
python3 main.py
`

### Track Water Consumption 

Create a channel for water drinking contest. Once you drink a glass of water, send a :cup with straw: ':cup_with_straw:' emoji to the channel. Xiao Baozi keeps track of all the users in the server, and annouces the winner of the day to the channel (record the channel id in `ids.py`).

### Bible Reading Plan

Everyday, Baozi send a reminder to read a bible chapter.

#### Create a Plan

The user will text "[Bb]ible reading plan" in the server, with the name of a book, and the chapter. The name can be shortened.

For example:
`bible reading plan at Gen 50`. Baozi will register the user at Genesis Chapter 50. This marks the starting place of Baozi's reminders.


#### Done with the Daily Plan

The user will text "done read" in the server. If the user is super on track and reads more than one chapters a day, text the number of chapters along in the message.

For example:
`done read 5`. Baozi will update the record of the user accordingly.

