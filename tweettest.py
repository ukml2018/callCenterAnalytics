import tweepy
 
import pandas as pd
import csv
import re 
import string
import preprocessor as p

 


consumer_key="qJYpiQ44d6wAkSeR8EAHVhwHG"
consumer_secret="v562i2Od4xPu6LMUQb9y6qvaOeZ7pjyooi0GEPlQ726pYanXqK"
access_key="1572554059743363072-KxImdCAfcibBN8X5thKBcyrSAmldi9"
access_secret="UbGRZJrH0DOElm9nVAjbN7wL2Q3011uQZYJJ8rdw8D6CL"

 
# Authenticate to Twitter
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
 
api = tweepy.API(auth,wait_on_rate_limit=True)

csvFile = open('file-name', 'a')
csvWriter = csv.writer(csvFile)
 
search_words = "#"      # enter your words
new_search = search_words + " -filter:retweets"
for tweet in tweepy.Cursor(api.search_30_day,query=new_search,label='information').items():
    csvWriter.writerow([tweet.created_at, tweet.text.encode('utf-8'),tweet.user.screen_name.encode('utf-8'), tweet.user.location.encode('utf-8')])
   