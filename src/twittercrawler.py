from bs4 import BeautifulSoup
import requests
import sys
import random
import os

# global constants that should never be modified at runtime.
base_url = "https://twitter.com/i/search/timeline"
if sys.platform == "linux" or sys.platform == "linux2":
    uafile = "useragents_linux.dat"
elif sys.platform == "darwin":
    uafile = "useragents_mac.dat"
elif sys.platform == "win32":
    uafile = "useragent_windows.dat"

with open(uafile, "rt") as f:
    ualist = f.read().split("\n")


# tweet related class and functions
class Tweet:
    """A class that represents a single tweet. After parsing with the default parser, the following attributes will be present.
        Attributes:
            tweet_id(int): The unique id of the tweet itself.
            account_name(str): The name of the user tweeting this tweet.
            user_id(int): The id of the user tweeting this tweet.
            timestamp(str): The time at which this tweet was tweeted.
            text(str): The text of the tweet.
            links(list): Any external links within the tweet.
            replies(int): The number of replies to this tweet.
            retweets(int): The number of times this tweet has been retweeted.
            favorites(int): The number of favorites this tweet has recieved."""
    def __init__(self):
        self.links = []

    def __str__(self):
        return str(self.__dict__)


# functions for processing the html of the tweet
def clean_text(text):
    """Cleans raw text so that it can be written into a csv file without causing any errors."""
    temp = text
    temp = temp.replace("\n", " ")
    temp = temp.replace("\r", " ")
    temp = temp.replace(",", " ")
    temp.strip()
    return temp


def has_class(element, class_):
    """Checks if an html element (a bs4.element.Tag element) has a certain class.
        Args:
            element(bs4.element.Tag): The element to inspect.
            class_(str): The class that you want to check the element for.
        Returns:
            bool: True if the class exists, False otherwise."""
    return "class" in element.attrs and class_ in element.attrs["class"]


# actual sample parsers
def parse_html(tweet_parser, html):
    """Parses the entire html from the twitter response and generates tweet objects to be passed to the handler.
        This is the default parser for the twitter crawler.
        Args:
            tweet_parser(function): The function to convert the html of individual tweets to tweet objects.
            html(str): The entire html to parse as a string.
        Yields:
            Tweet: The set of tweets that are found and generated from the html response."""
    soup = BeautifulSoup(html, "lxml")
    all_tweets = soup.find_all("li", attrs={"class": "stream-item"})

    for raw_tweet in all_tweets:
        tweet = tweet_parser(raw_tweet)
        yield tweet


def html_to_tweet_object(element):
    """Parses the html of a single tweet from the response, and creates a tweet object.
        This is the default tweet_parser for the twitter crawler.
        Args:
            element(bs4.element.Tag): The html of a single tweet.
        Returns:
            Tweet: The tweet object that represents the html of the tweet."""
    tweet = Tweet()
    tweet_container = list(element.children)[1]
    attributes = tweet_container.attrs

    # add attributes to Tweet object
    tweet.tweet_id = attributes["data-tweet-id"]
    tweet.account_name = attributes["data-name"]
    tweet.user_id = attributes["data-user-id"]

    # find the contents of the tweet
    contents = None
    for c in tweet_container.findChildren():
        if has_class(c, "content"):
            contents = c
            break

    # parse the contents of the tweet for relevant information
    if contents is not None:
        for c in contents.findChildren():

            # parse the time of the tweet
            if has_class(c, "stream-item-header"):
                header = c
                for small in header.findChildren():
                    if has_class(small, "tweet-timestamp"):
                        tweet.timestamp = small.attrs["title"]
                        break

            # parse the text, links of the tweet
            if has_class(c, "js-tweet-text-container"):
                text = c
                for p in text.findChildren():
                    if has_class(p, "tweet-text"):
                        if hasattr(p, "contents") and not isinstance(p.contents[0], type(p)):
                            tweet.text = clean_text(p.contents[0])

                    if has_class(p, "twitter-timeline-link"):
                        if "data-expanded-url" in p.attrs:
                            url = p.attrs["data-expanded-url"]
                            if url not in tweet.links:
                                tweet.links.append(url)

            # parse the stats of the tweet
            if has_class(c, "stream-item-footer"):
                for span in c.findChildren():
                    if has_class(span, "ProfileTweet-action--reply"):
                        for grandchild in span.findChildren():
                            if "data-tweet-stat-count" in grandchild.attrs:
                                tweet.replies = grandchild.attrs["data-tweet-stat-count"]
                                break

                    if has_class(span, "ProfileTweet-action--retweet"):
                        for grandchild in span.findChildren():
                            if "data-tweet-stat-count" in grandchild.attrs:
                                tweet.retweets = grandchild.attrs["data-tweet-stat-count"]
                                break

                    if has_class(span, "ProfileTweet-action--favorite"):
                        for grandchild in span.findChildren():
                            if "data-tweet-stat-count" in grandchild.attrs:
                                tweet.favorites = grandchild.attrs["data-tweet-stat-count"]
                                break

    return tweet


def tweets_to_csv(crawler, tweet):
    """Receives a Tweet object, and outputs the profile of the tweets to a csv file specified by the crawler.
        Args:
            crawler:(TwitterCrawler): The crawler that is calling this function.
            tweet(Tweet): The tweet object to output the stats of."""

    # initialize the output_file
    if crawler.depth == 1:
        if os.path.exists(crawler.output_file):
            pass
        else:
            with open(crawler.output_file, "wt") as f:
                f.write(",".join(crawler.parameters))
                f.write("\n")

    parameters = crawler.parameters

    with open(crawler.output_file, "at") as f:
        for (i, parameter) in enumerate(parameters):
            if hasattr(tweet, parameter):
                if type(getattr(tweet, parameter)) == list:
                    f.write(" ".join(getattr(tweet, parameter)))
                else:
                    f.write(str(getattr(tweet, parameter)))
            else:
                f.write("Null")
            if i < len(parameters) - 1:
                f.write(",")
            else:
                f.write("\n")


class TwitterCrawler:
    """The crawler. Intialized according to user settings.
        Attributes:
            query(str): The search query to run. The query should be formed according to the Twitter Search API.
            max_depth(int): The maximum number of times this crawler will send requests to twitter.
            parser(generator): A generator that takes a crawler and the entire inner HTML of the tweet stream from the response as input and yields a bs4.element.Tag object for each tweet.
            tweet_parser(function): A function that takes a crawler and bs4.element.Tag object for a single tweet as input and outputs a twittercrawler.Tweet object.
            handler(function): A function that takes a crawler and twittercrawler.Tweet object as input and performs some functionality using it.
                The default handler outputs the details of the tweet to a csv file.
            init_min_pos(str): The position to start crawling at within the infinite stream of tweets.
            output_file(str): The file to output the results of the crawl to, in the case that the user uses the default handler.
            parameters(list): The parameters that will be output to the csv file in the case that the user uses the default handler.
        """

    def __init__(self, query="hoge", max_depth=None, parser=parse_html, tweet_parser=html_to_tweet_object, handler=tweets_to_csv, init_min_pos=None, output_file="output",
                 parameters=["tweet_id", "account_name", "user_id", "timestamp", "text", "links", "repiles", "retweets", "favorites"]):
        self.query = query
        self.max_depth = max_depth
        self.parser = lambda x, y: parser(x.tweet_parser, y)
        self.tweet_parser = tweet_parser
        self.handler = handler
        self.last_min_pos = init_min_pos
        self.output_file = output_file
        self.parameters = parameters

        self.depth = None
        self.end_reason = None

    def crawl(self):
        """Actual crawl function. Crawls according to the initialization of the crawler."""
        connection_cut = False
        seed = self.last_min_pos if self.last_min_pos is not None else "hoge"
        response = self.get_request_from_last_position(seed)

        self.depth = 0

        while True:
            self.depth += 1

            data = response.json()

            # data is a python dictionary
            # data should come with keys ['new_latent_count', 'items_html', 'min_position', 'focused_refresh_interval', 'has_more_items']
            min_pos = data["min_position"]

            if self.last_min_pos is not None:
                if not connection_cut and min_pos == self.last_min_pos:
                    print("Starting to loop! Exitting with status:")
                    self.dump()
                    sys.exit(1)

            self.last_min_pos = min_pos
            html = data["items_html"]

            # parse the html
            for item in self.parser(self, html):
                self.handler(self, item)

            # log for debugging
            with open("log" + self.query + ".txt", "at") as f:
                f.write(min_pos + "\n")

            if not self.check_if_finished():
                try:
                    r = self.get_request_from_last_position(min_pos)
                except:
                    connection_cut = True
                    continue
                response = r
                connection_cut = False
                # crawl_twitter_recursively(response, parser=parser, status=status)
            else:
                if not data["has_more_items"]:
                    self.end_reason = "no more items"
                elif self.check_if_finished():
                    self.end_reason = "finish condition met"
                else:
                    self.end_reason = "terminated for some unintended reason"
                print("Crawl ended successfuly with following status:")
                self.dump()
                break

    def check_if_finished(self):
        """Returns true if the finish conditions are met."""
        if self.max_depth is not None and self.depth >= self.max_depth:
            return True
        else:
            return False

    def get_request_from_last_position(self, seed):
        ua = random.choice(ualist)
        headers = {"User-Agent": ua}
        return requests.get(base_url, params={"q": self.query,
                                              "vertical": "default",
                                              "max_position": seed,
                                              "src": "typd",
                                              "include_entities": "1",
                                              "include_available_features": "1",
                                              "lang": "en"
                                            }, headers=headers)

    def dump(self):
        """Print the status of the crawler to stdout."""
        print("""
            last min pos: {}
            Finish reason: {}
            """.format(self.last_min_pos, self.end_reason))

    def restart(self):
        """Attempts to resume crawling from the last position that was found.
        Requires the log file for the query to work."""
        try:
            with open("log" + self.query + ".txt", "rt") as f:
                seed = f.read().split("\n")[-1]
                self.last_min_pos = seed
                self.crawl()
        except FileNotFoundError:
            print("Error: Failed to find log file for restart.")
