## SI 206 Winter 2017
## Project 3
## Building on HW6, HW7 (and some previous material!)

## NOTE: There are tests for this project, but the tests are NOT exhaustive -- you should pass them, but ONLY passing them is not necessarily sufficient to get 100% on the project. The caching must work correctly, the queries/manipulations must follow the instructions and work properly. You can ensure they do by testing just the way we always do in class -- try stuff out, print stuff out, use the SQLite DB Browser and see if it looks ok!

## You may turn the project in late as a comment to the project assignment at a deduction of 10 percent of the grade per day late. This is SEPARATE from the late assignment submissions available for your HW.

import unittest
import itertools
import collections
import tweepy
import twitter_info # same deal as always...
import json
import sqlite3


## Your name:
## The names of anyone you worked with on this project:

#####

##### TWEEPY SETUP CODE:
# Authentication information should be in a twitter_info file...
consumer_key = twitter_info.consumer_key
consumer_secret = twitter_info.consumer_secret
access_token = twitter_info.access_token
access_token_secret = twitter_info.access_token_secret
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Set up library to grab stuff from twitter with your authentication, and return it in a JSON format 
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

##### END TWEEPY SETUP CODE

## Task 1 - Gathering data

## Define a function called get_user_tweets that gets at least 20 Tweets from a specific Twitter user's timeline, and uses caching. The function should return a Python object representing the data that was retrieved from Twitter. (This may sound familiar...) We have provided a CACHE_FNAME variable for you for the cache file name, but you must write the rest of the code in this file.

CACHE_FNAME = "SI206_project3_cache.json"
# Put the rest of your caching setup here:
try:
	cache_file = open(CACHE_FNAME,'r')
	cache_contents = cache_file.read()
	cache_file.close()
	CACHE_DICTION = json.loads(cache_contents)
except:
	CACHE_DICTION = {}



# Define your function get_user_tweets here:
def get_user_tweets(user_handle):
	unique_identifier = "twitter_{}".format(user_handle) 
	if unique_identifier in CACHE_DICTION: # if it is...
		print('using cached data for', user_handle)
		pass
	else:
		print('getting data from internet for', user_handle)
		twitter_results = api.user_timeline(user_handle) # get it from the internet
		CACHE_DICTION[unique_identifier] = twitter_results
		# but also, save in the dictionary to cache it
		
		f = open(CACHE_FNAME,'w') # open the cache file for writing
		f.write(json.dumps(CACHE_DICTION)) # make the whole dictionary holding data and unique identifiers into a json-formatted string, and write that wholllle string to a file so you'll have it next time!
		f.close()

	return CACHE_DICTION[unique_identifier]



# Write an invocation to the function for the "umich" user timeline and save the result in a variable called umich_tweets:

umich_tweets = get_user_tweets("umich")



## Task 2 - Creating database and loading data into database

# You will be creating a database file: project3_tweets.db
# Note that running the tests will actually create this file for you, but will not do anything else to it like create any tables; you should still start it in exactly the same way as if the tests did not do that! 
# The database file should have 2 tables, and each should have the following columns... 
conn = sqlite3.connect('project3_tweets.db')
cur = conn.cursor()

# table Tweets, with columns:
# - tweet_id (containing the string id belonging to the Tweet itself, from the data you got from Twitter -- note the id_str attribute) -- this column should be the PRIMARY KEY of this table
# - text (containing the text of the Tweet)
# - user_id (an ID string, referencing the Users table, see below)
# - time_posted (the time at which the tweet was created)
# - retweets (containing the integer representing the number of times the tweet has been retweeted)

cur.execute('DROP TABLE IF EXISTS Tweets')
statement = 'CREATE TABLE IF NOT EXISTS '
statement += 'Tweets (tweet_id TEXT PRIMARY_KEY, tweet_text TEXT, user_id TEXT, time_posted TIMESTAMP, retweets INTEGER)'
cur.execute(statement)

# table Users, with columns:
# - user_id (containing the string id belonging to the user, from twitter data -- note the id_str attribute) -- this column should be the PRIMARY KEY of this table
# - screen_name (containing the screen name of the user on Twitter)
# - num_favs (containing the number of tweets that user has favorited)
# - description (text containing the description of that user on Twitter, e.g. "Lecturer IV at UMSI focusing on programming" or "I tweet about a lot of things" or "Software engineer, librarian, lover of dogs..." -- whatever it is. OK if an empty string)
cur.execute('DROP TABLE IF EXISTS Users')
statement = 'CREATE TABLE IF NOT EXISTS '
statement += 'Users (user_id INTEGER PRIMARY_KEY, screen_name TEXT, num_favs INTEGER, description TEXT)'
cur.execute(statement)

## You should load into the Users table:
# The umich user, and all of the data about users that are mentioned in the umich timeline. 
# NOTE: For example, if the user with the "TedXUM" screen name is mentioned in the umich timeline, that Twitter user's info should be in the Users table, etc.

## You should load into the Tweets table: 
# Info about all the tweets (at least 20) that you gather from the umich timeline.
# NOTE: Be careful that you have the correct user ID reference in the user_id column! See below hints.

## HINT: There's a Tweepy method to get user info that we've looked at before, so when you have a user id or screenname you can find alllll the info you want about the user.
## HINT #2: You may want to go back to a structure we used in class this week to ensure that you reference the user correctly in each Tweet record.
## HINT #3: The users mentioned in each tweet are included in the tweet dictionary -- you don't need to do any manipulation of the Tweet text to find out which they are! Do some nested data investigation on a dictionary that represents 1 tweet to see it!

# Constructing the Tweets table
tweet_id = []
tweet_text = []
user_id = []
time_posted = []
retweets = []

for t in umich_tweets:
	tweet_id.append(t['id_str'])
	tweet_text.append(t['text'])
	user_id.append(t['user']['id_str'])
	time_posted.append(t['created_at'])
	retweets.append(t['retweet_count'])

tweets_list = zip(tweet_id, tweet_text, user_id, time_posted, retweets)
tweet_spec = 'INSERT OR IGNORE INTO Tweets VALUES (?,?,?,?,?)'
for t in tweets_list:
	cur.execute(tweet_spec, t)
conn.commit()

# Constructing the Users table
user_id = []
screen_name = []
num_favs = []
description = []

for t in umich_tweets:
	if len(t['entities']['user_mentions']) >= 1:
		for i in t['entities']['user_mentions']:
			if i['id_str'] not in user_id:
				user_id.append(i['id_str'])
				name = i['screen_name'].lower()
				screen_name.append(name)
	if t['user']['id_str'] not in user_id:
		user_id.append(t['user']['id_str'])
		screen_name.append(t['user']['screen_name'])

for n in screen_name:
	user_object = api.get_user(n)
	num_favs.append(user_object['favourites_count'])
	description.append(user_object['description'])

users_list = zip (user_id, screen_name, num_favs, description)

table_spec = 'INSERT OR IGNORE INTO Users VALUES (?,?,?,?)'
for u in users_list:
	cur.execute(table_spec, u)
conn.commit()





## Task 3 - Making queries, saving data, fetching data

# All of the following sub-tasks require writing SQL statements and executing them using Python.

# Make a query to select all of the records in the Users database. Save the list of tuples in a variable called users_info.

q1 = 'SELECT * FROM Users'
cur.execute(q1)
users_info = cur.fetchall()


# Make a query to select all of the user screen names from the database. Save a resulting list of strings (NOT tuples, the strings inside them!) in the variable screen_names. HINT: a list comprehension will make this easier to complete!
q2 = 'SELECT screen_name FROM Users'
cur.execute(q2)
screen = cur.fetchall()
screen_names = []
for s in screen:
	screen_names.append(s[0])


# Make a query to select all of the tweets (full rows of tweet information) that have been retweeted more than 25 times. Save the result (a list of tuples, or an empty list) in a variable called more_than_25_rts.

q3 = 'SELECT * FROM Tweets WHERE retweets > 25'
cur.execute(q3)
more_than_25_rts = cur.fetchall()


# Make a query to select all the descriptions (descriptions only) of the users who have favorited more than 25 tweets. Access all those strings, and save them in a variable called descriptions_fav_users, which should ultimately be a list of strings.
q4 = 'SELECT description FROM Users WHERE num_favs > 25'
cur.execute(q4)
favs = cur.fetchall()
descriptions_fav_users = []
for f in favs:
	descriptions_fav_users.append(f[0])

# Make a query using an INNER JOIN to get a list of tuples with 2 elements in each tuple: the user screenname and the text of the tweet -- for each tweet that has been retweeted more than 50 times. Save the resulting list of tuples in a variable called joined_result.
q5 = 'SELECT Users.screen_name, Tweets.tweet_text FROM Tweets INNER JOIN Users on Tweets.user_id = Users.user_id WHERE Tweets.retweets > 10  '
cur.execute(q5)
joined_result = cur.fetchall()



## Task 4 - Manipulating data with comprehensions & libraries

## Use a set comprehension to get a set of all words (combinations of characters separated by whitespace) among the descriptions in the descriptions_fav_users list. Save the resulting set in a variable called description_words.

# for d in descriptions_fav_users:
# 	for word in d.split():
# 		description_words.append(word)

description_words = {word for d in descriptions_fav_users for word in d.split()}


## Use a Counter in the collections library to find the most common character among all of the descriptions in the descriptions_fav_users list. Save that most common character in a variable called most_common_char. Break any tie alphabetically (but using a Counter will do a lot of work for you...).
cnt = collections.Counter()
for d in descriptions_fav_users: 
	for w in d.split():
			for a in list(w):
				cnt[a.lower()] += 1
most_common_char = cnt.most_common(1)[0][0]
print(most_common_char)



## Putting it all together...
# Write code to create a dictionary whose keys are Twitter screen names and whose associated values are lists of tweet texts that that user posted. You may need to make additional queries to your database! To do this, you can use, and must use at least one of: the DefaultDict container in the collections library, a dictionary comprehension, list comprehension(s). Y
# You should save the final dictionary in a variable called twitter_info_diction.
q7 = 'SELECT screen_name FROM Users'
cur.execute(q7)
names = cur.fetchall()
user_names = [n[0] for n in names]
# tweets = [get_user_tweets(u) for u in user_names]
# print(type(tweets))
# print(len(tweets))
# print("*****************************")
# print(type(tweets[1]))
# print(len(tweets[1]))
# print(type(tweets[1][0]))

# tweets = [i["text"] for u in user_names for i in get_user_tweets(u)]
# print(type(tweets))
# print(len(tweets))

def get_tweet_text(example):
	results = [i["text"] for i in example]
	# for i in example:
	# 	results.append(i["text"])
	return results


tweet_list = [get_tweet_text(get_user_tweets(u)) for u in user_names]





# tweet_list = []
# for u in user_names:
# 	tweets = []
# 	for user_tweet in get_user_tweets(u):
# 		tweets.append(user_tweet["text"])
# 	tweet_list.append(tweets)

twitter_info_diction = dict(zip(user_names, tweet_list))









# tweet_list = [tweet['text'] for u in user_names for user_tweet in get_user_tweets(u) for tweet in user_tweet]
# print("---------- LIST OF TWEETS -------")


### IMPORTANT: MAKE SURE TO CLOSE YOUR DATABASE CONNECTION AT THE END OF THE FILE HERE SO YOU DO NOT LOCK YOUR DATABASE (it's fixable, but it's a pain). ###


###### TESTS APPEAR BELOW THIS LINE ######
###### Note that the tests are necessary to pass, but not sufficient -- must make sure you've followed the instructions accurately! ######
print("\n\nBELOW THIS LINE IS OUTPUT FROM TESTS:\n")

class Task1(unittest.TestCase):
	def test_umich_caching(self):
		fstr = open("SI206_project3_cache.json","r").read()
		self.assertTrue("umich" in fstr)
	def test_get_user_tweets(self):
		res = get_user_tweets("umsi")
		self.assertEqual(type(res),type(["hi",3]))
	def test_umich_tweets(self):
		self.assertEqual(type(umich_tweets),type([]))
	def test_umich_tweets2(self):
		self.assertEqual(type(umich_tweets[18]),type({"hi":3}))
	def test_umich_tweets_function(self):
		self.assertTrue(len(umich_tweets)>=20)

class Task2(unittest.TestCase):
	def test_tweets_1(self):
		conn = sqlite3.connect('project3_tweets.db')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Tweets');
		result = cur.fetchall()
		self.assertTrue(len(result)>=20, "Testing there are at least 20 records in the Tweets database")
		conn.close()
	def test_tweets_2(self):
		conn = sqlite3.connect('project3_tweets.db')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Tweets');
		result = cur.fetchall()
		self.assertTrue(len(result[1])==5,"Testing that there are 5 columns in the Tweets table")
		conn.close()
	def test_tweets_3(self):
		conn = sqlite3.connect('project3_tweets.db')
		cur = conn.cursor()
		cur.execute('SELECT user_id FROM Tweets');
		result = cur.fetchall()
		self.assertTrue(len(result[1][0])>=2,"Testing that a tweet user_id value fulfills a requirement of being a Twitter user id rather than an integer, etc")
		conn.close()
	def test_tweets_4(self):
		conn = sqlite3.connect('project3_tweets.db')
		cur = conn.cursor()
		cur.execute('SELECT tweet_id FROM Tweets');
		result = cur.fetchall()
		self.assertTrue(result[0][0] != result[19][0], "Testing part of what's expected such that tweets are not being added over and over (tweet id is a primary key properly)...")
		if len(result) > 20:
			self.assertTrue(result[0][0] != result[20][0])
		conn.close()
	def test_users_4(self):
		conn = sqlite3.connect('project3_tweets.db')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Users');
		result = cur.fetchall()
		self.assertTrue(len(result)>=2,"Testing that there are at least 2 distinct users in the Users table")
		conn.close()
	def test_users_5(self):
		conn = sqlite3.connect('project3_tweets.db')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Users');
		result = cur.fetchall()
		self.assertTrue(len(result)<20,"Testing that there are fewer than 20 users in the users table -- effectively, that you haven't added duplicate users. If you got hundreds of tweets and are failing this, let's talk. Otherwise, careful that you are ensuring that your user id is a primary key!")
		conn.close()
	def test_users_6(self):
		conn = sqlite3.connect('project3_tweets.db')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Users');
		result = cur.fetchall()
		self.assertTrue(len(result[0])==4,"Testing that there are 4 columns in the Users database")
		conn.close()

class Task3(unittest.TestCase):
	def test_users_info(self):
		self.assertEqual(type(users_info),type([]),"testing that users_info contains a list")
	def test_users_info2(self):
		self.assertEqual(type(users_info[1]),type(("hi","bye")),"Testing that an element in the users_info list is a tuple")
	def test_track_names(self):
		self.assertEqual(type(screen_names),type([]),"Testing that track_names is a list")
	def test_track_names2(self):
		self.assertEqual(type(screen_names[1]),type(""),"Testing that an element in screen_names list is a string")
	def test_more_rts(self):
		if len(more_than_25_rts) >= 1:
			self.assertTrue(len(more_than_25_rts[0])==5,"Testing that a tuple in more_than_ten_rts has 5 fields of info (one for each of the columns in the Tweet table)")
	def test_more_rts2(self):
		self.assertEqual(type(more_than_25_rts),type([]),"Testing that more_than_ten_rts is a list")
	def test_more_rts3(self):
		if len(more_than_25_rts) >= 1:
			self.assertTrue(more_than_25_rts[0][-1]>10, "Testing that one of the retweet # values in the tweets is greater than 10")
	def test_descriptions_fxn(self):
		self.assertEqual(type(descriptions_fav_users),type([]),"Testing that descriptions_fav_users is a list")
	def test_descriptions_fxn2(self):
		self.assertEqual(type(descriptions_fav_users[0]),type(""),"Testing that at least one of the elements in the descriptions_fav_users list is a string, not a tuple or anything else")
	def test_joined_result(self):
		self.assertEqual(type(joined_result[0]),type(("hi","bye")),"Testing that an element in joined_result is a tuple")

class Task4(unittest.TestCase):
	def test_description_words(self):
		print("To help test, description words looks like:", description_words)
		self.assertEqual(type(description_words),type({"hi","Bye"}),"Testing that description words is a set")
	def test_common_char(self):
		self.assertEqual(type(most_common_char),type(""),"Testing that most_common_char is a string")
	def test_common_char2(self):
		self.assertTrue(len(most_common_char)==1,"Testing that most common char is a string of only 1 character")
	def test_twitter_info_diction(self):
		self.assertEqual(type(twitter_info_diction),type({"hi":3}))
	def test_twitter_info_diction2(self):
		self.assertEqual(type(list(twitter_info_diction.keys())[0]),type(""),"Testing that a key of the dictionary is a string")
	def test_twitter_info_diction3(self):
		self.assertEqual(type(list(twitter_info_diction.values())[0]),type([]),"Testing that a value in the dictionary is a list")
	def test_twitter_info_diction4(self):
		self.assertEqual(type(list(twitter_info_diction.values())[0][0]),type(""),"Testing that a single value inside one of those list values-in-dictionary is a string! (See instructions!)")


if __name__ == "__main__":
	unittest.main(verbosity=2)