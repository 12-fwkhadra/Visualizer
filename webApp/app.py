import json
import re
import nltk
import pandas as pd
from bson import SON
from flask import Flask, render_template, jsonify, request, redirect, url_for
from jedi.inference import analysis
from nltk.sentiment import SentimentIntensityAnalyzer
from pymongo import MongoClient
from textblob import TextBlob
import pycountry

app = Flask(__name__)


client = MongoClient("mongodb+srv://fk1:mongodb22@cluster0.7mt03q2.mongodb.net/?retryWrites=true&w=majority")

database = client["tester"]

col = database["khashoggi"]
# names = database.get_collectionNames()



class myClass:
    def __init__(self, name):
        self.name = name

    # for name in names:
    #     col = name


@app.route('/')
@app.route('/home')
def home():
    return render_template('main.html')

@app.route('/Dashboard')
def dashboard():
    return render_template('Dashboard.html')

# @app.route('/Dashboard', methods=['POST'])
# def dashboard():
#     n=request.form.get('topic_to_select')
#     nn=myClass(n)
#     return render_template('Dashboard.html', names)

@app.route('/sentimentals')
def sentiments():
    return render_template('Sentiments.html')

@app.route('/Languages')
def languages_page():
    return render_template('Languages.html')

@app.route('/Hashtags')
def hashtags_page():
    return render_template('Hashtags.html')

@app.route('/Countries')
def countries_page():
    return render_template('countries.html')

@app.route('/totalcount')
def total_count():
    total = col.count_documents({})
    return jsonify(total)


@app.route('/nbofusers')
def nb_of_users():
    nb_of_users = len(col.distinct('user.id'))
    pipeline = [
        {
            u"$match": {
                u"$and": [
                    {
                        u"inReplyToTweetId": None
                    },
                    {
                        u"quotedTweet.id": None
                    }
                ]
            }
        },
        {
            u"$group": {
                u"_id": u"$user.url",
                u"count": {
                    u"$sum": 1.0
                }
            }
        },
        {
            u"$project": {
                u"user.name": 1.0,
                u"user.url": 1.0,
                u"count": 1.0
            }
        },
        {
            u"$sort": SON([(u"count", -1)])
        },
        {
            u"$limit": 1.0
        }
    ]
    cursor = col.aggregate(pipeline)
    for c in cursor:
        link = c['_id']
    return jsonify(nb_of_users, link)


@app.route('/latestDate')
def latest_date():
    collection = database["changeformatofdate"]
    pipeline = [
        {
            u"$group": {
                u"_id": {
                    u"year": {
                        u"$year": u"$updatedate"
                    },
                    u"month": {
                        u"$month": u"$updatedate"
                    },
                    u"day": {
                        u"$dayOfMonth": u"$updatedate"
                    }
                },
                u"count": {
                    u"$sum": 1
                }
            }},
        {
            u"$sort": SON([(u"count", 1)])
        },
        {
            u"$limit": 1.0
        }
    ]
    cursor = collection.aggregate(pipeline)
    for l in cursor:
        date = str(l['_id']['year']) + '-' + str(l['_id']['month']) + '-' + str(l['_id']['day'])
    return jsonify(date)


@app.route('/languages')
def languages():
    pipeline = [
        {
            u"$group": {
                u"_id": u"$lang",
                u"count": {
                    u"$sum": 1.0
                }
            }
        },
        {
            u"$project": {
                u"lang": 1.0,
                u"count": 1.0
            }
        },
        {
            u"$sort": SON([(u"count", -1)])
        },
        {
            "$limit": 10
        }
    ]
    cursor = col.aggregate(pipeline)
    list = []
    total = 0
    terms = ["und", "qct", "qme", "qam", "qht", "qst", "zxx"]
    for l in cursor:
        dict = {}
        if l['_id'] not in terms:
            dict['category'] = l['_id']
            total += l['count']
            dict['value'] = l['count']
            dict['full'] = 100
            dict['columnSettings'] = {'fill': 'chart.get("colors").getIndex(2)'}
            list.append(dict)
    for j in list:
        j['value'] = (j['value']/total)*100
    return jsonify(list)


@app.route('/countries')
def countries():
    pipeline = [
        {
            u"$group": {
                u"_id": u"$user.location",
                u"count": {
                    u"$sum": 1.0
                }
            }
        },
        {
            u"$project": {
                u"user.location": 1.0,
                u"count": 1.0
            }
        },
        {
            u"$sort": SON([(u"count", -1)])
        },
        {
            "$limit": 10
        }
    ]
    cursor = col.aggregate(pipeline)
    list = []
    results = []
    for country in pycountry.countries:
        results.append({
            "key": country.alpha_2,
            "text": "{}".format(country.name),
        })
    for l in cursor:
        for k in results:
            for country in pycountry.countries:
                if country.name in l['_id']:
                    list.append({"id": country.alpha_2, "name": country.name,
                                 "value": l["count"], "circleTemplate": {'fill': 'chart.get("colors").getIndex(2)'}})
    return jsonify(list)


@app.route('/hashtags')
def top_hashtags():
    tweets = []
    data = open(
        r'F:\Al Maaref Uni\Second Year 2021-2022\Summer 21-22\Practical Training\myFinal\khashoggi.json',
        "r", encoding="utf8")
    for line in data:
        tweets.append(json.loads(line))
    dict = {}
    for tweet in tweets:
        if tweet["hashtags"] is None or tweet["hashtags"] == "null":
            continue
        for hashtags in tweet["hashtags"]:
            if hashtags in dict:
                dict[hashtags] += 1
            else:
                dict[hashtags] = 1
    sort_orders = sorted(dict.items(), key=lambda x: x[1], reverse=True)
    top_20 = sort_orders[0:20]
    list = []
    for l in top_20:
        dict3 = {}
        dict3['name'] = l[0]
        dict3['weight'] = l[1]
        list.append(dict3)
    return jsonify(list)


def tweets_content():
    cursor = col.find({}, {"_id": 0, "rawContent": 1})
    tweets_text, positive_tweets, negative_tweets, neutral_tweets = [], [], [], []
    for tweet in cursor:
        text = tweet["rawContent"]
        tweets_text.append(text)
    tweets_text = pd.DataFrame(tweets_text)
    neutral_tweets = pd.DataFrame(neutral_tweets)
    negative_tweets = pd.DataFrame(negative_tweets)
    positive_tweets = pd.DataFrame(positive_tweets)
    #save in csv
    tw_list = pd.DataFrame(tweets_text)
    tw_list["text"] = tw_list[0]
    remove_rt = lambda x: re.sub('RT @\w+: ', " ", x)
    rt = lambda x: re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", x)
    tw_list["text"] = tw_list.text.map(remove_rt).map(rt)
    tw_list["text"] = tw_list.text.str.lower()
    tw_list[['polarity', 'subjectivity']] = tw_list['text'].apply(lambda Text: pd.Series(TextBlob(Text).sentiment))
    for index, row in tw_list['text'].iteritems():
        score = SentimentIntensityAnalyzer().polarity_scores(row)
        neg = score['neg']
        neu = score['neu']
        pos = score['pos']
        if neg > pos:
            tw_list.loc[index, 'sentiment'] = "negative"
        elif pos > neg:
            tw_list.loc[index, 'sentiment'] = "positive"
        else:
            tw_list.loc[index, 'sentiment'] = "neutral"
        tw_list.loc[index, 'neg'] = neg
        tw_list.loc[index, 'neu'] = neu
        tw_list.loc[index, 'pos'] = pos
    tw_list_negative = tw_list[tw_list["sentiment"] == "negative"]
    tw_list_positive = tw_list[tw_list["sentiment"] == "positive"]
    tw_list_neutral = tw_list[tw_list["sentiment"] == "neutral"]
    per = count_values_in_column(tw_list, "sentiment")
    per.to_csv('F:\Al Maaref Uni\Second Year 2021-2022\Summer 21-22\Practical Training\myFinal\webApplication\data.csv')

def count_values_in_column(data,feature):
    total=data.loc[:,feature].value_counts(dropna=False)
    percentage=round(data.loc[:,feature].value_counts(dropna=False,normalize=True)*100,2)
    return pd.concat([total,percentage],axis=1,keys=['Total','Percentage'])

@app.route('/percentages')
def reader():
    df = pd.read_csv('F:\Al Maaref Uni\Second Year 2021-2022\Summer 21-22\Practical Training\myFinal\webApplication\data.csv')
    pos_percentage = df.iat[2, 2]
    neg_percentage = df.iat[0, 2]
    neu_percentage = df.iat[1, 2]
    df2 = pd.read_csv('F:\Al Maaref Uni\Second Year 2021-2022\Summer 21-22\Practical Training\myFinal\webApplication\positive.csv')
    terms = ['neg', 'pos', 'neu']
    g = globals()
    list = []
    for x in terms:
        dict = {}
        if x == 'neu':
            s = df2[df2[f'{x}'] == df2[f'{x}'].max()]['0']
            g[f'{x}'] = s[0]
            dict[f'{x}'] = g[f'{x}']
            list.append(dict)
        else:
            g[f'{x}'] = (df2[df2[f'{x}'] == df2[f'{x}'].max()]['0']).values.tolist()
            dict[f'{x}'] = g[f'{x}']
            list.append(dict)
    return jsonify(pos_percentage, neg_percentage, neu_percentage, list)


@app.route('/verified')
def verified_users():
    query = {}
    query["user.verified"] = True
    projection = {}
    projection["_id"] = 0.0
    projection["user.id"] = 1.0
    cursor = col.find(query, projection=projection)
    count = 0
    for l in cursor:
        count += 1
    percentage_of_verified = (count / 100000) * 100 #make this dynamic
    return jsonify(percentage_of_verified)

@app.route('/topliked')
def top_liked():
    pipeline = [
        {
            u"$project": {u"rawContent": 1, u"likeCount": 1, u"user.id": 1, u"_id": 0, u"url": 1}
        },
        {
            u"$sort": {u"likeCount": -1}
        },
        {
            "$limit": 1
        }
    ]
    cursor = col.aggregate(pipeline)
    list = []
    for l in cursor:
        list.append(l)
    return jsonify(list)

@app.route('/topshared')
def top_shared():
    pipeline = [
        {
            u"$project": {u"rawContent": 1, u"retweetCount": 1, u"user.id": 1, u"_id": 0, u"url": 1}
        },
        {
            u"$sort": {u"retweetCount": -1}
        },
        {
            "$limit": 1
        }
    ]
    cursor = col.aggregate(pipeline)
    list = []
    for l in cursor:
        list.append(l)
    return jsonify(list)


if __name__ == '__main__':
    app.run()
