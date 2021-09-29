from concurrent import futures

from absl import app
from absl import flags
from absl import logging
from google.protobuf import text_format
import grpc
import pythoncom
from win32com import client as win32client

import deep_trader_pb2
import deep_trader_pb2_grpc

flags.DEFINE_integer('port', 11231, 'Port to listen.')
flags.DEFINE_boolean('block_submit_order', True, 'Block submit order rpc.')

FLAGS = flags.FLAGS


class CybosException(Exception):
    def __init__(self, status: grpc.StatusCode, message: str):
        super().__init__(message)
        self.status = status


class CybosWrapper(object):
    def __init__(self):
        self.cybos_status = win32client.Dispatch('CpUtil.CpCybos')
        self.cybos_code_util = win32client.Dispatch('CpUtil.CpCodeMgr')
        self.cybos_chart = win32client.Dispatch('CpSysDib.StockChart')
        self.cybos_order_util = win32client.Dispatch('CpTrade.CpTdUtil')
        self.cybos_order = win32client.Dispatch('CpTrade.CpTd0311')

    def _is_cybos_connect_alive(self):
        return self.cybos_status.IsConnect == 1

    def get_candle(self, code, cycle_type, cycle, count):
        if not self._is_cybos_connect_alive():
            raise CybosException(
                grpc.StatusCode.INTERNAL,
                f'Cybos is disconnected. Check cybos plus login status.')

        if cycle_type not in ['D', 'W', 'M', 'm', 'T']:
            raise CybosException(
                grpc.StatusCode.INVALID_ARGUMENT,
                f'Improper cycle type {cycle_type} is given.')

        self.cybos_chart.SetInputValue(0, code)
        self.cybos_chart.SetInputValue(1, ord('2'))
        self.cybos_chart.SetInputValue(4, count)
        self.cybos_chart.SetInputValue(5, [0, 1, 2, 3, 4, 5, 8])
        self.cybos_chart.SetInputValue(6, ord(cycle_type))
        self.cybos_chart.SetInputValue(7, cycle)
        self.cybos_chart.SetInputValue(9, ord('1'))

        logging.info('Sending get candle data request to Cybos.')
        self.cybos_chart.BlockRequest()

        if self.cybos_chart.GetDibStatus() != 0:
            raise CybosException(
                grpc.StatusCode.INTERNAL,
                f'Error in cybos. {self.cybos_chart.GetDibMsg1}')
        logging.info('Get candle data request is completed.')

        results = []
        for i in range(self.cybos_chart.GetHeaderValue(3)):
            results.append(
                deep_trader_pb2.CandleData(
                    date=self.cybos_chart.GetDataValue(0, i),
                    time=self.cybos_chart.GetDataValue(1, i),
                    open=self.cybos_chart.GetDataValue(2, i),
                    high=self.cybos_chart.GetDataValue(3, i),
                    low=self.cybos_chart.GetDataValue(4, i),
                    close=self.cybos_chart.GetDataValue(5, i),
                    volume=self.cybos_chart.GetDataValue(6, i)))

        return deep_trader_pb2.GetCandleResponse(
            name=self.cybos_code_util.CodeToName(code), candle_data=results)

    def submit_order(self, code, order_type, count, price):
        if FLAGS.block_submit_order:
            raise CybosException(
                grpc.StatusCode.UNAVAILABLE,
                f'submit order rpc is blocked by server config.')

        if not self._is_cybos_connect_alive():
            raise CybosException(
                grpc.StatusCode.INTERNAL,
                f'Cybos is disconnected. Check cybos plus login status.')

        if order_type not in ['L', 'S']:
            raise CybosException(
                grpc.StatusCode.INVALID_ARGUMENT,
                f'Improper cycle type {order_type} is given.')

        if self.cybos_order_util.TradeInit(0) != 0:
            raise CybosException(grpc.StatusCode.INTERNAL,
                                 f'Cybos order initialize is failed.')

        account_number = self.cybos_order_util.AccountNumber[0]
        account_flag = self.cybos_order_util.GoodsList(account_number, 1)

        self.cybos_order.SetInputValue(0, '1' if order_type == 'S' else '2')
        self.cybos_order.SetInputValue(1, account_number)
        self.cybos_order.SetInputValue(2, account_flag[0])
        self.cybos_order.SetInputValue(3, code)
        self.cybos_order.SetInputValue(4, count)
        self.cybos_order.SetInputValue(7, '0')
        if price > 0:
            self.cybos_order.SetInputValue(8, "01")
            self.cybos_order.SetInputValue(5, price)
        else:
            self.cybos_order.SetInputValue(8, "03")

        order_result = self.cybos_order.BlockRequest()
        if order_result == 4:
            raise CybosException(grpc.StatusCode.INTERNAL,
                                 f'Cybos order request limit exceeded.')
        elif order_result != 0:
            raise CybosException(
                grpc.StatusCode.INTERNAL,
                f'Cybos order request is failed with unknown error.')

        if self.cybos_order.GetDibStatus() != 0:
            raise CybosException(
                grpc.StatusCode.INTERNAL,
                f'Error in cybos. {self.cybos_chart.GetDibMsg1}')

        return deep_trader_pb2.SubmitOrderResponse()


class Cybos5WrapperService(deep_trader_pb2_grpc.DeepTraderServicer):
    def GetCandle(self, request, context):
        logging.info('GetCandle: %s',
                     text_format.MessageToString(request, as_utf8=True))
        pythoncom.CoInitialize()
        try:
            return CybosWrapper().get_candle(request.code, request.cycle_type,
                                             request.cycle, request.count)
        except CybosException as ex:
            context.abort(ex.status, str(ex))
        finally:
            pythoncom.CoUninitialize()

    def SubmitOrder(self, request, context):
        logging.info('SubmitOrder: %s',
                     text_format.MessageToString(request, as_utf8=True))
        pythoncom.CoInitialize()
        try:
            return CybosWrapper().submit_order(request.code,
                                               request.order_type,
                                               request.count, request.price)
        except CybosException as ex:
            context.abort(ex.status, str(ex))
        finally:
            pythoncom.CoUninitialize()


def main(unused_args):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    servicer = Cybos5WrapperService()
    deep_trader_pb2_grpc.add_DeepTraderServicer_to_server(servicer, server)
    server.add_insecure_port(f'[::]:{FLAGS.port}')
    server.start()
    logging.info('Cybor5 wrapping server has started on port %d', FLAGS.port)
    server.wait_for_termination()


if __name__ == '__main__':
    app.run(main)
