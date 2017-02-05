# twitter_past_crawler
## Description
A crawler that can search accumulate past tweets, by emulating the infinite scroll on the search page.
The official twitter API as of now is very limiting in the access it provides to past tweets. This crawler attempts to provide users the ability to collect past tweets beyond those limitations.

## Requirements
The following packages are required:
- requests
- Beautiful Soap 4

## Installation
`$ pip install twitterpastcrawler`

## Usage
See samples/ for more examples. Below is an example of how to use this crawler:

```python
import twitterpastcrawler

crawler = twitterpastcrawler.TwitterCrawler(
							query="#haiku", # searches for tweets that respond to the query, "#haiku"
							output_file="haiku.csv" # outputs results to haiku.csv
						)

crawler.crawl() # commences the crawl
```

The following attributes can be specified upon initialization:
* query(str): The search query to run. The query should be formed according to the Twitter Search API.
* max_depth(int): The maximum number of times this crawler will send requests to twitter.
* parser(generator): A generator that takes a crawler and the entire inner HTML of the tweet stream from the response as input and yields a bs4.element.Tag object for each tweet.
* tweet_parser(function): A function that takes a crawler and bs4.element.Tag object for a single tweet as input and outputs a twittercrawler.Tweet object.
* handler(function): A function that takes a crawler and twittercrawler.Tweet object as input and performs some functionality using it. The default handler outputs the details of the tweet to a csv file.
* init_min_pos(str): The position to start crawling at within the infinite stream of tweets.
* output_file(str): The file to output the results of the crawl to, in the case that the user uses the default handler.
* parameters(list): The parameters that will be output to the csv file in the case that the user uses the default handler.

See the following link for information regarding the search API of twitter: <https://dev.twitter.com/rest/public/search>

## License
Copyright (c) 2017 by Keita Kurita
Released under the MIT license
https://opensource.org/licenses/mit-license.php