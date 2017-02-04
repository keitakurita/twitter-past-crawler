from setuptools import setup


setup(
    name='twitterpastcrawler',

    version='0.0.6',

    description='A crawler that can crawl and accumulate past tweets without using the official API.',

    url='https://github.com/keitakurita/twitter_past_crawler',

    author='Keita Kurita',

    license='MIT',

    keywords='twitter crawler',

    packages=["twitterpastcrawler"],

    # requirements
    install_requires=['requests', 'beautifulsoup4', 'lxml'],

    # data files
    package_data={
        '': ['useragents_mac.dat', 'useragents_linux.dat', 'useragents_windows.dat'],
    },

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ]

)
