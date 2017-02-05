"""A simple sample program that accumulates tweets for the query \"#haiku\"
"""

import twitterpastcrawler

crawler = twitterpastcrawler.TwitterCrawler(query="#haiku",
                                        output_file="haiku.csv"
                                        )

crawler.crawl()
