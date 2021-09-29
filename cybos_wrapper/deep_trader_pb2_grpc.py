# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import deep_trader_pb2 as deep__trader__pb2


class DeepTraderStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetCandle = channel.unary_unary(
                '/deeptrader.DeepTrader/GetCandle',
                request_serializer=deep__trader__pb2.GetCandleRequest.SerializeToString,
                response_deserializer=deep__trader__pb2.GetCandleResponse.FromString,
                )
        self.SubmitOrder = channel.unary_unary(
                '/deeptrader.DeepTrader/SubmitOrder',
                request_serializer=deep__trader__pb2.SubmitOrderRequest.SerializeToString,
                response_deserializer=deep__trader__pb2.SubmitOrderResponse.FromString,
                )


class DeepTraderServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetCandle(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SubmitOrder(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DeepTraderServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetCandle': grpc.unary_unary_rpc_method_handler(
                    servicer.GetCandle,
                    request_deserializer=deep__trader__pb2.GetCandleRequest.FromString,
                    response_serializer=deep__trader__pb2.GetCandleResponse.SerializeToString,
            ),
            'SubmitOrder': grpc.unary_unary_rpc_method_handler(
                    servicer.SubmitOrder,
                    request_deserializer=deep__trader__pb2.SubmitOrderRequest.FromString,
                    response_serializer=deep__trader__pb2.SubmitOrderResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'deeptrader.DeepTrader', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class DeepTrader(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetCandle(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/deeptrader.DeepTrader/GetCandle',
            deep__trader__pb2.GetCandleRequest.SerializeToString,
            deep__trader__pb2.GetCandleResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SubmitOrder(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/deeptrader.DeepTrader/SubmitOrder',
            deep__trader__pb2.SubmitOrderRequest.SerializeToString,
            deep__trader__pb2.SubmitOrderResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
