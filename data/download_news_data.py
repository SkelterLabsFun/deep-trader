"""Download news data from naver finance news.

NOTE: This is not build by bazel. Only running locally is tested and
you need to install requirements manually.

Example usage:

    python download_news_data.py --outfile ./result.txt \
                                 --code 005930 \
                                 --max_page 2000 \
                                 --interval_sleep_secs 0.05

    results are saved as plain text file formed as `YYYY.MM.DD\tTitle of news`
"""
import re
import requests
import time
from typing import List, Tuple

from absl import app
from absl import flags
from absl import logging
from bs4 import BeautifulSoup

flags.DEFINE_string('code', None, 'Stock code to search.')
flags.DEFINE_float('interval_sleep_secs', None,
                   '(Optional)The secs to sleep after each searching.')
flags.DEFINE_integer('max_page', None, 'The number of pages to search.')
flags.DEFINE_string('outfile', None, 'Output file path.')

FLAGS = flags.FLAGS


class NaverNewsCrawler:

    def _make_url(self, code, page):
        return ('https://finance.naver.com/item/news_news.nhn?code=%s'
                '&page=%s&sm=title_entity_id.basic&clusterId=') % (code,
                                                                   str(page))

    def get_titles(self,
                   code: str,
                   max_page: int,
                   interval_sleep_secs: float = None) -> List[Tuple[str, str]]:
        logging.info('Crawling naver finance news titles.')

        results = []
        cur_page = 1
        while cur_page <= max_page:
            html = BeautifulSoup(
                requests.get(self._make_url(code, cur_page)).text, 'lxml')

            if cur_page == 1:
                last_page_url = html.find('td', {
                    'class': 'pgRR'
                }).find('a').get('href')
                real_max_page = int(
                    re.findall(r'page=(\d+)', last_page_url)[0])

                if real_max_page < max_page:
                    max_page = real_max_page

            titles = [
                x.find('a').get_text()
                for x in html.findAll('td', {'class': 'title'})
            ]

            dates = [
                x.get_text().split()[0]
                for x in html.findAll('td', {'class': 'date'})
            ]

            if len(titles) == len(dates):
                for title, date in zip(titles, dates):
                    results.append((date, title))
            else:
                logging.warn(
                    'Length of title and date is different. Skip page %d',
                    cur_page)

            logging.info('Crawlled %d pages' % cur_page)
            cur_page += 1

            if interval_sleep_secs:
                time.sleep(interval_sleep_secs)

        return results


def main(unused_args):
    nnc = NaverNewsCrawler()
    results = nnc.get_titles(FLAGS.code, FLAGS.max_page,
                             FLAGS.interval_sleep_secs)

    with open(FLAGS.outfile, 'w') as f:
        for date, title in results:
            f.write(f'{date}\t{title}\n')


if __name__ == '__main__':
    flags.mark_flags_as_required([
        'code',
        'max_page',
        'outfile',
    ])
    app.run(main)