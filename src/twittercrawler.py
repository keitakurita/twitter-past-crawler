from bs4 import BeautifulSoup
import requests
import re
import sys
import random

base_url = "https://twitter.com/i/search/timeline"
if sys.platform == "linux" or sys.platform == "linux2":
    uafile = "useragentslinux.txt"
elif sys.platform == "darwin":
    uafile = "useragents.txt"
elif sys.platform == "win32":
    uafile = "useragentwindows.txt"

with open(uafile, "rt") as f:
    ualist = f.read().split("\n")


def parse_html(crawler, html, output_file):
    soup = BeautifulSoup(html, "lxml")


parameters = ["time", "date", "url", "title", "description", "sitename", "retweeted", "favorited", "verified"]


def parse_articles(crawler, html, output_file):
    """The function for parsing html and retrieving wanted data. Outputs to output file specified by command line"""

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

                    with open(output_file, "at") as f:
                        # write in following format: time,date,url,retweeted,favorited,domain,verified,query
                        # output = "{},{},{},{},{},{},{},{}\n".format(time, date, url, retweeted, favorited, domain, verified, args.query)
                        f.write(",".join(str(output[a]) for a in parameters))
                        f.write("\n")
                except:
                    pass


class TwitterCrawler:

    def __init__(self, query="hoge", max_depth=None, parser=parse_html, init_min_pos=None, output_file="output"):
        self.query = query
        self.max_depth = max_depth
        self.parser = lambda x, y: parser(x, y, output_file)
        self.last_min_pos = init_min_pos

        self.depth = None
        self.end_reason = None

    def crawl(self):
        """Actual crawl function. Written as a relatively general interface in case of future updates."""
        connection_cut = False
        seed = self.last_min_pos if self.last_min_pos is not None else ""
        ua = random.choice(ualist)
        headers = {"User-Agent": ua}
        response = requests.get(base_url,
                                params={"q": self.query,
                                        "vertial": "default",
                                        "max_position": seed,
                                        "src": "typd",
                                        "include_entities": "1",
                                        "include_available_features": "1",
                                        "lang": "en"
                                        }, headers=headers)

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
            self.parser(self, html)

            # log for debugging
            with open("log" + self.query + ".txt", "at") as f:
                f.write(min_pos + "\n")

            if not self.check_if_finished():
                # &src=typd&include_available_features=1&include_entities=1&lang=ja
                ua = random.choice(ualist)
                headers = {"User-Agent": ua}
                try:
                    r = requests.get(base_url, params={"q": self.query,
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
                    self.end_reason = "no more items"
                elif self.check_if_finished():
                    self.end_reason = "finish condition met"
                else:
                    self.end_reason = "terminated for some unintended reason"
                print("Crawl ended successfuly with following status:")
                self.dump()
                break

    def check_if_finished(self):
        if self.max_depth is not None and self.depth >= self.max_depth:
            return True
        else:
            return False

    def dump(self):
        print("last min pos: {}".format(self.last_min_pos))

    def restart(self):
        try:
            with open("log" + self.query + ".txt", "rt") as f:
                seed = f.read().split("\n")[-1]
                self.last_min_pos = seed
                self.crawl()
        except FileNotFoundError:
            print("Error: Failed to find log file for restart.")
