import twitterpastcrawler

crawler = twitterpastcrawler.TwitterCrawler(query="#haiku",
                                        output_file="haiku.csv"
                                        )

crawler.crawl()
