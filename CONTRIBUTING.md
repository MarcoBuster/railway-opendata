# Contribution guide

Contributions/forks are welcome and appreciated!
For instance, you can:
- improve the scraper;
- add more tests and documentation;
- improve or add more statistics and visualizations.

## Development environment

Before starting, install the development requirements by running this command:

```bash
$ pip install -r requirements-dev.txt
```

This project has set up some [pre-commit](https://pre-commit.com/) hooks (like `black` and `isort`) to ensure code readability and consistency: please use them before submitting patches.

Due to the inability to redistribuite scraped train data (see [Licensing](#licensing) section), there are tests ([pytest](https://pytest.org)) only for the scraping module: run them with

```bash
$ pytest .
```

## Debug logging

You can enable debug logging using the `-d` (or `--debug`) command line flag.
