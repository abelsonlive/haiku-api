import nltk
import tweepy
import re, time, string, random, json, yaml
from collections import defaultdict
from nltk.corpus import cmudict
import sys, os
from thready import threaded

class HaikuDetector(object):
    
  def __init__(
    self, 
    screen_name,
    n_pages = 10):

    # number to word lookup
    self.n2w = self.gen_n2w()

    # syllable dict
    self.cmu = cmudict.dict()

    # initialize haiku_list
    self.haikus = []

    # initialize list of tweets
    self.tweets = []

    # twitter stuff
    self.screen_name  = screen_name
    self.n_pages = n_pages
    self.consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
    self.consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
    self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

    # connect to twitter.
    self.api = self.connect_to_twitter()

  def connect_to_twitter(self):
    auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
    auth.set_access_token(self.access_token, self.access_token_secret)
    return tweepy.API(auth)

  def gen_n2w(self):
    # generate number lookup for 0 - 99
    n2w = "zero one two three four five six seven eight nine".split()
    n2w.extend("ten eleven twelve thirteen fourteen fifteen sixteen".split())
    n2w.extend("seventeen eighteen nineteen".split())
    n2w.extend(tens if ones == "zero" else (tens + " " + ones) 
        for tens in "twenty thirty forty fifty sixty seventy eighty ninety".split()
        for ones in n2w[0:10])
    return n2w

  def number_of_syllables(self, word):
    return [len(list(y for y in x if y[-1].isdigit())) for x in self.cmu[word]]

  def remove_urls(self, string):
    pattern = r'((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?'
    return re.sub(pattern, ' ', string)

  def detect_potential_haiku(self, tweet):
    tweet = tweet.encode('utf-8')

    # remove urls
    tweet = self.remove_urls(tweet)
    
    # ignore tweets with @s, RT's and MT's and numbers greater than 3 digits
    if re.search(r'@|#|MT|RT|[0-9]{3,}', tweet):
        return None

    # swap ampersand with and
    tweet = re.sub("&", " and ", tweet)

    # remove punctuation
    tweet = tweet.translate(string.maketrans("",""), string.punctuation)

    # strip and lower text
    tweet = tweet.strip().lower()

    # split tweet into a list of words
    words = [w.strip() for w in tweet.split() if w != '']

    # replace numbers with words
    words = [self.n2w[int(w)] if re.search(r"0-9+", w) else w for w in words]

    # detect suitable tweets, annotate words with each words' number of syllables
    n_syllables = []
    clean_words = []

    for word in words:
        try:
            n_syllable = self.number_of_syllables(word)[0]
        except KeyError:
            return None
        if n_syllable > 7:
            return None
        else:
            n_syllables.append(n_syllable)
            clean_words.append(word.strip().lower())

    # remove tweekus that are really long
    clean_tweet = ' '.join(clean_words)
    if len(clean_tweet) > 125:
        return None

    # make sure tweets have the proper number of syllables
    total_syllables = sum(n_syllables)
    if total_syllables == 17:
        return {"words" : clean_words, "syllables" : n_syllables }
    else:
        return None

  def is_proper_haiku(self, haiku_dict):
    words = haiku_dict['words']
    syllables = haiku_dict['syllables']

    # make sure lines break at 5 and 12
    syllable_cum_sum = []
    syllables_so_far = 0
    for syllable in syllables:
        syllables_so_far += syllable
        syllable_cum_sum.append(syllables_so_far)
    if 5 in syllable_cum_sum and 12 in syllable_cum_sum:
        return True
    else:
        return False

  def format_haiku(self, haiku_dict):
    words = haiku_dict['words']
    syllables = haiku_dict['syllables']
    syllable_count = 0
    haiku = ''
    for i, word in enumerate(words):
        if syllable_count == 5:
            haiku += " / "
        if syllable_count == 12:
            haiku += " / "
        syllable_count += syllables[i]
        haiku += word.strip() + " "
    return haiku.strip()

  def detect_haiku(self, tweet):
    h = self.detect_potential_haiku(tweet.text)
    if h is not None:
      if self.is_proper_haiku(h):
        h_text = self.format_haiku(h)
        haiku = {
            "haiku_text": h_text,
            "status_id": tweet.id_str,
            "user": tweet.user.screen_name
        }

        self.haikus.append(haiku)

  def get_tweets_for_page(self, page):
    tweet_list = self.api.user_timeline(
      screen_name = self.screen_name,
      count = 200,
      page = page
    )
    self.tweets.extend(tweet_list)

  def go(self):

    # find some tweets
    threaded(range(1, self.n_pages), self.get_tweets_for_page, 10, 20)
    threaded(self.tweets, self.detect_haiku, 20, 200)

    # if we find a haiku, post it on twitter and tumblr
    if len(self.haikus)>0:
      return self.haikus
    else:
      return ""
