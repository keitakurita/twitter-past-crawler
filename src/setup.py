from setuptools import setup


setup(
    name='twitter_past_crawler',

    version='0.0.1',

    description='A crawler that can crawl and accumulate past tweets without using the official API.',

    url='https://github.com/keitakurita/twitter_past_crawler',

    author='Keita Kurita',

    license='MIT',

    keywords='twitter crawler',

    # requirements
    install_requires=['requests', 'beautifulsoup4'],

    # data files
    package_data={
        '': ['useragents_mac.txt', 'useragents_linux.txt', 'useragents_windows.txt'],
    },

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Programming Language :: Python :: 3.4',
    ]

)
