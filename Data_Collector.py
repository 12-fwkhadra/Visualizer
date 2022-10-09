import twitter as sntwitter
import pandas as pd
import time
import json
import os


def path_finder():
    '''
        This function returns the full path of a csv file
        The csv file stores the topics to be fetched later
        add the topics to the csv file
        don't apply changes to this function
    '''
    csv_path = os.path.abspath(r'topics.csv')
    return csv_path


def fetcher():
    '''
        this function gets the data for the targeted hashtags using the TwitterHashtagScrapper method of snscrape library
        add your hashtag title to the csv file
        only change the since and until dates which can be omitted too and number of tweets to be collected
        the results will be saved in json files in the same directory
    '''
    csv_path = path_finder()
    topics = pd.read_csv(fr'%s' % csv_path, names=['Topic', 'number'])
    for topic, nb in zip(topics['Topic'], topics['number']):
        tweets = []
        for i, tweet in enumerate(
                sntwitter.TwitterHashtagScraper(f'{topic} since:2018-06-01 until:2019-11-30').get_items()):
            if i > nb:  # nb of tweets to be collected
                break
            tweets.append(tweet.json())

        with open(f'{topic}.json', 'w') as file:
            for item in tweets:
                file.write(item + '\n')

        time.sleep(1)

fetcher()
