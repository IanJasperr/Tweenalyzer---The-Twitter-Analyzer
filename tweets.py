#__Author__ : Shrobon Biswas

#__Description__:
#This script will use twitter api
#The necessary data will be returned to the server for parsing 
#The script will just accept the Query String
from __future__ import print_function
import tweepy
import numpy as np
import configurations 
import pandas as pd
import time 
import sys 
#from langdetect import detect

#We will be using TextBlob for Sentiment Analysis
#TextBlob is also used for text translation
from textblob import TextBlob
import googlemaps


'''
This function will help us escape the rate-limit-error we may recieve
'''
def limit_handled(cursor):

    while True:
        try:
        	#time.sleep(1)
        	yield cursor.next()

        except tweepy.RateLimitError:
            time.sleep(60*15)
            continue

        except StopIteration:
        	break



def make_maps(tweetsDataframe):
	#This function will return the data as required by google maps
	doughnut = []
	sentiment_map = []

	########################################
	#for the language plot :: dougnut chart
	doughnut.append(["Language","Tweets"])
	lang_count = tweetsDataframe["language"].value_counts()
	lang_count= lang_count.to_dict()
	for key,value in lang_count.iteritems():
		temp = [key,value]
		doughnut.append(temp)
	########################################



	########################################
	#for the sentiment_map plot :: geochart
	sentiment_map.append(['Lat', 'Long', 'Sentiments'])
	for i in range(0,len(tweetsDataframe)):

		temp= []
		latitude = tweetsDataframe['latitude'][i]
		longitude = tweetsDataframe['longitude'][i]
		sentiment = tweetsDataframe['sentiments'][i]
		if sentiment >=-1 and sentiment <=1:
			temp = [latitude,longitude,sentiment]
			sentiment_map.append(temp)

	
	########################################
	return (doughnut,sentiment_map)

def QueryTwitter(search_string):

	#Fetching the Configuration Settings
	key = configurations.consumer_key
	secret = configurations.consumer_secret
	access_token = configurations.access_token
	access_secret = configurations.access_secret

	#Authenticating ::
	#Receiving Access Tokens
	auth = tweepy.OAuthHandler(consumer_key=key,consumer_secret=secret)
	auth.set_access_token(access_token, access_secret)

	#Instantiating the API with our Access Token
	api = tweepy.API(auth)

	tweet_list = []
	for tweet in limit_handled(tweepy.Cursor(api.search,q=search_string).items(10)):
		tweet_list.append(tweet)

	#We now extract details from the tweet and get the resultant DataFrame
	tweet_Data = filter_tweets(tweet_list)


	(doughnut,sentiment_map) = make_maps(tweet_Data)
	#return tweet_Data
	return (doughnut,sentiment_map)









# Will be creating the dataframes in this function 
# Snetiment Analysis
def filter_tweets(tweets):


	id_list = [tweet.id for tweet in tweets]
	#Will contain a single column table containing all the tweet ids
	tweet_Data = pd.DataFrame(id_list,columns=['id'])
	tweet_Data["text"] = [tweet.text for tweet in tweets]
	#tweet_Data["favourite_count"] = [tweet.favourite_count for tweet in tweets]
	# Location 
	#tweet_Data["location"] = [tweet.author.location for tweet in tweets]



	Sentiments_list = []
	Sentiments_group = []

	Subjectivity_list = []
	Subjectivity_group = []

	tweet_text_list = []
	tweet_location_list = []

	tweet_language = []
	tweet_latitude = []
	tweet_longitude =[]
	tweet_country = []



	for tweet in tweets:
		raw_tweet_text = tweet.text
		message = TextBlob(unicode(tweet.text))
		location = tweet.author.location
		# location can be null :: We have to handle that too 
		if len(location) !=0:
			(latitude,longitude,country) = geocode_location(location)
			tweet_latitude.append(latitude)
			tweet_longitude.append(longitude)
			tweet_country.append(country)

		else:
			tweet_latitude.append("")
			tweet_longitude.append("")
			tweet_country.append("")




		#Detecting and Changing the language to english for sentiment analysis
		lang = message.detect_language()
		tweet_language.append(str(lang))
		try:
			if str(lang) != "en":
				message = message.translate(to="en") #Problem Here
		except:
			pass

		#### Special Character removal #####
		message = str(message)
		new_message = ""
		for letter in range(0,len(message)):
			current_read =message[letter]
			if ord(current_read) > 126:
				#this is a special character & hence will be skipped
				continue
			else:
				new_message =new_message+current_read

		message = new_message
		message = TextBlob(message)
		######################################

		#Changing the Language is important
		#Since it will help in sentiment analysis using TextBlob
		#When language is english remove special characters :: heavily affects analysis
		sentiment = message.sentiment.polarity
		if (sentiment > 0):
			#postive
			Sentiments_group.append('positive')
		elif (sentiment < 0):
			#Negative
			Sentiments_group.append('negative')
		else:
			Sentiments_group.append('neutral')



		subjectivity = message.sentiment.subjectivity
		if (subjectivity > 0.4):
			#subjective ::: Long tweet
			Subjectivity_group.append('subjective')
		else:
			Subjectivity_group.append('objective')

		Sentiments_list.append(sentiment)
		Subjectivity_list.append(subjectivity)
		tweet_text_list.append(raw_tweet_text)
		tweet_location_list.append(location)


	tweet_Data["sentiments"] = Sentiments_list
	tweet_Data["sentiments_group"] = Sentiments_group

	tweet_Data["subjectivity"]= Subjectivity_list
	tweet_Data["subjectivity_group"] = Subjectivity_group

	tweet_Data["location"] = tweet_location_list
	tweet_Data["text"] = tweet_text_list

	tweet_Data["language"] = tweet_language
	tweet_Data["latitude"] = tweet_latitude
	tweet_Data["longitude"]= tweet_longitude
	tweet_Data["country"] = tweet_country

	

	#Let us calculate the sentiment scores

	return tweet_Data

def geocode_location(loc):
	#Importing the API key for Google Geocode
	gmaps_api = configurations.google_maps_key

	#Registering our app by sending the API key 
	gm = googlemaps.Client(key=gmaps_api)

	##################################################################
	#We need to geocode this location and store it as lat and longtitude
	location_result = gm.geocode(loc)
	if len(location_result) > 0:
		#means that atleast something was returned
		latitude = location_result[0]['geometry']['location']['lat']
		longitude= location_result[0]['geometry']['location']['lng']
		country =location_result[0]['formatted_address'].split(",")
		country = country[len(country)-1]		# there arises a problem here
		return (str(latitude),str(longitude),country)
		

	else:
		#store null
		return ("","","")
	
	return
	##################################################################
