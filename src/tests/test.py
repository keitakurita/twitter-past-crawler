import unittest
import sys
sys.path.append("..")
import twitterpastcrawler
import os


class CrawlerTest(unittest.TestCase):

    def setUp(self):
        self.crawler = twitterpastcrawler.TwitterCrawler(
                        query="foo",
                        output_file="foo.csv",
                        max_depth=2
                    )
        if os.path.exists("foo.csv"):
            os.remove("foo.csv")

    def test_request_getter(self):
        response = self.crawler.get_request_from_last_position("hoge")
        data = response.json()
        self.assertIn("items_html", data)
        self.assertIn("min_position", data)

    def test_twitter_parser(self):
        response = self.crawler.get_request_from_last_position("hoge")
        data = response.json()
        elements = twitterpastcrawler.parse_html(twitterpastcrawler.html_to_tweet_object, data["items_html"])
        for element in elements:
            if not hasattr(element, "tweet_id"):
                return unittest.skip("{!r} doesn't have an id".format(element))

    def test_parser(self):
        response = self.crawler.get_request_from_last_position("hoge")
        data = response.json()

        def pass_parser(tweet):
            return 1

        parsed_elements = list(twitterpastcrawler.parse_html(twitterpastcrawler.html_to_tweet_object, data["items_html"]))
        raw_elements = list(twitterpastcrawler.parse_html(pass_parser, data["items_html"]))
        self.assertEqual(len(parsed_elements), len(raw_elements))


if __name__ == '__main__':
    unittest.main()
