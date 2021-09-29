from absl import app
from absl import flags
from absl import logging
import grpc

import deep_trader_pb2
import deep_trader_pb2_grpc

flags.DEFINE_string('host', '39.125.76.24', 'Host to connect.')
flags.DEFINE_integer('port', 11231, 'Port to connect.')

FLAGS = flags.FLAGS


def main(unused_args):
    logging.info('Cybor5 wrapping client has started on port %d', FLAGS.port)
    
    channel = grpc.insecure_channel(f'{FLAGS.host}:{FLAGS.port}')
    stub = deep_trader_pb2_grpc.DeepTraderStub(channel)

    try:
        response = stub.GetCandle(
            deep_trader_pb2.GetCandleRequest(code='A005930',
                                             cycle_type='m',
                                             cycle=5,
                                             count=720))
        print(f'Data count: {len(response.candle_data)}')
        print(f'Date: {response.candle_data[0].date}')
        print(f'Time: {response.candle_data[0].time}')
        print(f'Open: {response.candle_data[0].open}')
        print(f'High: {response.candle_data[0].high}')
        print(f'Low: {response.candle_data[0].low}')
        print(f'Close: {response.candle_data[0].close}')
        print(f'Volume: {response.candle_data[0].volume}')
    except grpc.RpcError as ex:
        logging.error('GetCandle is failed. (%s) %s', ex.code().name, str(ex))


if __name__ == '__main__':
    app.run(main)
