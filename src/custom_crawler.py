from bs4 import BeautifulSoup
import requests
import argparse
import re
import os
import sys
import time
import random

parser = argparse.ArgumentParser(
    description="""Crawler for past twitter tweets.
    """, formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("-q", "--query", type=str,
                    default="@realDonaldTrump", help="""The query to search twitter feed for.
                    """)

parser.add_argument("-d", "--depth", type=int,
                    default=100000, help="The maximum depth to crawl to.")

parser.add_argument("-o", "--output", type=str,
                    default="tweet_data.csv", help="The output file. Must be in csv format.")

parser.add_argument("-m", "--maxitems", type=int,
                    default=100000, help="The maximum number of outputs.")

parser.add_argument("-s", "--seed", type=str,
                    default="hoge", help="The initial tweet id to start searching from.")

args = parser.parse_args()


base_url = "https://twitter.com/i/search/timeline"
parameters = ["time", "date", "url", "title", "description", "sitename", "retweeted", "favorited", "verified"]

cookies = {"guest_id": "v1%3A148056296358739303",
            # "pid": "v3:1480562968174939891586266",
            "eu_cn": "1",
            "kdt": "j1sEqw2FNitpCBax0YwVm2tzjtWkros2IrFNO61g",
            "dnt": "1",
            "netpu": "FriHoKuIVgA=",
            "twitter_ads_id": "v1_20576059376353223",
            "external_referer": "padhuUp37zjgzgv1mFWxJ1GGR6w5wXXNb61MrkCjQoc=|0",
            "lang": "en",
            "_gat": "1",
            "_ga": "GA1.2.761636380.1480562969",
            # "_twitter_sess": "_twitter_sess=BAh7CSIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCIT0bbhYAToMY3NyZl9p%250AZCIlNzUwZTI4ZjBmNzE2NDVhMTlhYjA0Yjk2MjEzZGIxNmY6B2lkIiU1YzY0%250AZjg5YWEwYmUzNTZmN2YyYTU2NWNhYzQ2ZGE0YQ%253D%253D--a1c8903b78b39665abacc120aaeab7c11c855188"
        }

ualist = []

def parse_html(html, status):
    """The function for parsing html and retrieving wanted data. Outputs to output file specified by command line"""

    if "num_items" not in status:
        status["num_items"] = 0

    soup = BeautifulSoup(html, "lxml")
    shared_links = soup.find_all("a", attrs={"class": ["twitter-timeline-link", "u-hidden"]})
    output = {}
    for link in shared_links:
        # get the date from the DOM element
        # check to see if tweeted from an official account
        # get favorited and retweeted count
        output["verified"] = False
        output["favorited"] = None
        output["retweeted"] = None
        output["date"] = "NaN"
        output["time"] = "Nan"
        output["title"] = None
        output["description"] = None
        output["sitename"] = None
        output["query"] = args.query

        for element in link.findParents():
            if "class" in element.attrs and "content" in element["class"]:
                for child in element.findChildren():
                    # the timestamp object
                    if "class" in child.attrs and "tweet-timestamp" in child["class"]:
                        if "title" in child.attrs:
                            # datetime should be in following format: 1:52 - 2016年11月19日
                            datetime = child["title"]
                            output["time"] = datetime.split("-")[0].strip()
                            output["date"] = datetime.split("-")[1].strip()

                    # check if verified
                    if "class" in child.attrs and "Icon--verified" in child["class"]:
                        output["verified"] = True

                    # check for retweeted count
                    if "class" in child.attrs and "ProfileTweet-action--retweet" in child["class"]:
                        for grandchild in child.findChildren():
                            if "data-tweet-stat-count" in grandchild.attrs:
                                output["retweeted"] = grandchild["data-tweet-stat-count"]

                    # check for favorited count
                    if "class" in child.attrs and "ProfileTweet-action--favorite" in child["class"]:
                        for grandchild in child.findChildren():
                            if "data-tweet-stat-count" in grandchild.attrs:
                                output["favorited"] = grandchild["data-tweet-stat-count"]

        # get the url and the domain
        if "data-expanded-url" in link.attrs:
            url = link["data-expanded-url"]
            output["url"] = url
            m = re.match("https?://([^/]+)/.*", url)
            if m is not None:
                output["domain"] = m.group(1)
            else:
                output["domain"] = url.split("/")[0]

            # exclude twitter shares
            if "twitter" not in output["domain"].split("."):
                # access the page to get the title, sitename and description
                try:
                    r = requests.get(url)
                    article = BeautifulSoup(r.text, "lxml")

                    title = article.find("meta", attrs={"property": "og:title"})
                    if title is not None and "content" in title.attrs:
                        output["title"] = title["content"].replace(",", "").split("\n")[0]

                    description = article.find("meta", attrs={"property": "og:description"})
                    if description is not None and "content" in description.attrs:
                        output["description"] = description["content"].replace(",", "").split("\n")[0]

                    sitename = article.find("meta", attrs={"property": "og:site_name"})
                    if sitename is not None and "content" in sitename.attrs:
                        output["sitename"] = sitename["content"].replace(",", "")

                    with open(args.output, "at") as f:
                        # write in following format: time,date,url,retweeted,favorited,domain,verified,query
                        # output = "{},{},{},{},{},{},{},{}\n".format(time, date, url, retweeted, favorited, domain, verified, args.query)
                        f.write(",".join(str(output[a]) for a in parameters))
                        f.write("\n")
                        status["num_items"] += 1
                except:
                    pass


def finished(status):
    """Dictates when to finish search."""

    if "number_of_crawl_times" not in status:
        status["number_of_crawl_times"] = 1
    else:
        status["number_of_crawl_times"] += 1

    if status["number_of_crawl_times"] > args.depth or status["num_items"] > args.maxitems:
        return True
    else:
        return False


def get_max_pos_from_html_and_url(html, url):
    soup = BeautifulSoup(html, "lxml")
    id_items = soup.find_all(id=re.compile("stream-item-tweet-[0-9]+"))
    maxid_matcher = re.match("stream-item-tweet-([0-9]+)", id_items[-1]["id"])
    max_id = maxid_matcher.group(1)

    minid_matcher = re.match("^.*&max_position=TWEET-([0-9]+)-([^&]+)&?.*", url)
    if minid_matcher is None:
        return None
        print("could not get max pos from html and url")
    else:
        min_id = minid_matcher.group(2)
        max_pos = "TWEET-" + max_id + "-" + min_id
        return max_pos


def crawl_twitter_recursively(response, parser=parse_html, finish_func=finished, status={}):
    """Actual crawl function. Written as a relatively general interface in case of future updates."""
    connection_cut = False

    while True:
        data = response.json()

        # data is a python dictionary
        # data should come with keys ['new_latent_count', 'items_html', 'min_position', 'focused_refresh_interval', 'has_more_items']
        min_pos = data["min_position"]

        if "last_min_pos" in status:
            if not connection_cut and min_pos == status["last_min_pos"]:
                print("Starting to loop! Exitting with status:")
                print(status)
                sys.exit(1)

        status["last_min_pos"] = min_pos
        html = data["items_html"]
        parser(html, status)
        # testing = get_max_pos_from_html_and_url(html, response.url)
        # assert(testing is None or testing == min_pos)

        # log for debugging
        with open("log" + args.query + ".txt", "at") as f:
            f.write(min_pos + "\n")

        if not finish_func(status):
            # &src=typd&include_available_features=1&include_entities=1&lang=ja
            ua = random.choice(ualist)
            headers = {"User-Agent": ua}
            try:
                r = requests.get(base_url, params={"q": args.query,
                                                          "vertical": "default",
                                                          "max_position": min_pos,
                                                          "src": "typd",
                                                          "include_entities": "1",
                                                          "include_available_features": "1",
                                                          "lang": "en"
                                                        }, headers=headers)
            except:
                connection_cut = True
                continue
            response = r
            connection_cut = False
            # crawl_twitter_recursively(response, parser=parser, status=status)
        else:
            if not data["has_more_items"]:
                status["end_reason"] = "no more items"
            elif finish_func(status):
                status["end_reason"] = "finish condition met"
            else:
                status["end_reason"] = "terminated for some unintended reason"
            print("Crawl ended successfuly with following status:")
            print(status)
            break


if __name__ == '__main__':
    if os.path.exists(args.output):
        pass
    else:
        with open(args.output, "wt") as f:
            f.write(",".join(parameters))
            f.write("\n")
    print("Beginning crawl...")

    global ualist
    if sys.platform == "linux" or sys.platform == "linux2":
        uafile = "useragentslinux.txt"
    elif sys.platform == "darwin":
        uafile = "useragents.txt"
    elif sys.platform == "win32":
        uafile = "useragentwindows.txt"

    with open(uafile, "rt") as f:
        ualist = f.read().split("\n")

    ua = random.choice(ualist)
    headers = {"User-Agent": ua}
    initial_response = requests.get(base_url,
                                    params={"q": args.query,
                                            "vertial": "default",
                                            "max_position": args.seed,
                                            "src": "typd",
                                            "include_entities": "1",
                                            "include_available_features": "1",
                                            "lang": "en"
                                            }, headers=headers)
    crawl_twitter_recursively(initial_response)
