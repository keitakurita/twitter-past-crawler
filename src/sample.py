import twitter_past_crawler

crawler = twitter_past_crawler.TwitterCrawler(query="#haiku",
                                        output_file="haiku.csv"
                                        )

crawler.crawl()
