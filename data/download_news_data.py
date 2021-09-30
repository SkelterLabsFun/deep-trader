"""Download news data from naver finance news.

NOTE: This is not build by bazel. Only running locally is tested and
you need to install requirements manually.


NOTE: (When use sentiment analytics)
This module need kubernetes pod port-forwarding to text_analytics pod in
just-dev2. Follow below processes before run this module.

1. Find pod that has name starts with 'text-analytics-classifier-api'
    >> `kubectl get pods --namespace text-analytics -o wide`
2. Remember its full name.
    >> For example | text-analytics-classifier-api-df4df4666-p75qq |
3. Port forward with this pod. The remote pod port is '8580'.
    >> `kubectl port-forward \
            --context gke_epo-just-dev2_asia-northeast3-c_epo-just-dev2-sec2 \
            --namespace text-analytics \
            pods/text-analytics-classifier-api-d9d7db669-p75qq 8580:8580`


Example usage:

    python download_news_data.py --outfile ./result.txt \
                                 --code 005930 \
                                 --max_page 2000 \
                                 --interval_sleep_secs 0.05
                                 --use_sentiment_analytics

    results are saved as plain text file formed as
    `YYYY.MM.DD\tTitle of news\tsentiment_value`
"""
import re
import requests
import time
from typing import List, Tuple

from absl import app
from absl import flags
from absl import logging
from bs4 import BeautifulSoup
import grpc

import service_pb2
import service_pb2_grpc

flags.DEFINE_string('code', None, 'Stock code to search.')
flags.DEFINE_float('interval_sleep_secs', None,
                   '(Optional)The secs to sleep after each searching.')
flags.DEFINE_integer('max_page', None, 'The number of pages to search.')
flags.DEFINE_string('outfile', None, 'Output file path.')
flags.DEFINE_boolean(
    'use_sentiment_analytics', False, 'If True, use sentiment'
    ' analytics for each news. But it makes overall process very slow.')
flags.DEFINE_integer('port', 8580,
                     'Local port-forwarded port for sentiment analytics.')

FLAGS = flags.FLAGS


class SentimentClassifierClient:
    """For separate from Bazel build system, below code is copied from
    ClassifierClient in //cabinet/iris/text_analytics/nlp/classfier_client.py"""

    def __init__(self, address, positive_label='1'):
        self.address = address
        self.positive_label = positive_label

    def get_sentiment_score(self, text, timeout=60):
        try:
            with grpc.insecure_channel(self.address) as channel:
                stub = service_pb2_grpc.PredictServiceStub(channel)
                request = service_pb2.ClassificationRequest(text=text)
                response = stub.Classify(request, timeout=timeout)
        except Exception:
            logging.error(f'Error occurred while processing text: {text}')
            raise
        else:
            for class_result in response.classes:
                if class_result.label == self.positive_label:
                    return class_result.score
            logging.warning(f'Positive label {self.positive_label} missing '
                            'in classifier result.')
            return -1


class NaverNewsCrawler:

    def _make_url(self, code, page):
        return ('https://finance.naver.com/item/news_news.nhn?code=%s'
                '&page=%s&sm=title_entity_id.basic&clusterId=') % (code,
                                                                   str(page))

    def get_titles(
        self,
        code: str,
        max_page: int,
        interval_sleep_secs: float = None,
        sentiment_classifier_client: SentimentClassifierClient = None
    ) -> List[List]:
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
                real_max_page = int(re.findall(r'page=(\d+)', last_page_url)[0])

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
                    record = [date, title]
                    if sentiment_classifier_client:
                        try:
                            record.append(
                                str(
                                    sentiment_classifier_client.
                                    get_sentiment_score(title)))
                        except grpc.RpcError as ex:
                            logging.error(
                                'Sentimet analytics error occured. Skip it. %s',
                                str(ex))
                            continue
                    results.append(record)
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
    scc = None
    if FLAGS.use_sentiment_analytics:
        scc = SentimentClassifierClient(f'localhost:{FLAGS.port}')

    results = nnc.get_titles(FLAGS.code, FLAGS.max_page,
                             FLAGS.interval_sleep_secs, scc)

    with open(FLAGS.outfile, 'w') as f:
        for record in results:
            value = '\t'.join(record)
            f.write(f'{value}\n')


if __name__ == '__main__':
    flags.mark_flags_as_required([
        'code',
        'max_page',
        'outfile',
    ])
    app.run(main)