import twittercrawler

crawler = twittercrawler.TwitterCrawler(query="@realDonaldTrump",
                                        max_depth=3,
                                        parser=twittercrawler.parse_articles,
                                        output_file="DonaldTrump.csv"
                                        )

crawler.crawl()
