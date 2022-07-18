import uuid
import pickle
import gevent
from gevent.event import Event
import threading
import socket
import errno
import select
import traceback
import sys

from gevent.queue import Queue
from krosslib import message

READ_PACKET_SIZE=8192
HEADER_SIZE=8
HEADER_ID=b'\x02\x03'
CLIENT_NAME=''

# use ReadBuf class for keeping current buf since bytes class is immutable
class ReadBuffer:
    buf = b''    



class MessageReader(gevent.Greenlet):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.clients = dict()
        self.subscribers = dict()
        self.trade_subscriber = None
        self.subscriber_queue = Queue()
        self._stop_event = Event()
        gevent.spawn(self.subscribe_broadcast)

    def block_write(self, header, body):
        msg_id = header['_id']
        self.clients[msg_id] = [Event(), None]
        write(self.sock, header, body)
        self.clients[msg_id][0].wait()
        obj = self.clients[msg_id][1]
        self.clients.pop(msg_id, None)
        return obj

    def subscribe_broadcast(self):
        while True:
            data = self.subscriber_queue.get(True)
            data[0](data[1], data[2])

    def subscribe_write(self, header, body, code, handler):
        if code in self.subscribers:
            print('Already subscribe code', code)
        else:
            self.subscribers[code] = handler
            header['code'] = code
            write(self.sock, header, body)

    def stop_subscribe_write(self, header, body, code):
        if code in self.subscribers:
            self.subscribers.pop(code, None)
            header['code'] = code
            write(self.sock, header, body)
        else:
            print('Not subscribing code', code)

    def subscribe_trade_write(self, header, body, handler):
        # multiple listener?
        if self.trade_subscriber is None:
            self.trade_subscriber = handler
            write(self.sock, header, body)
        else:
            print('Already subscribe trade')

    def stop_subscribe_trade_write(self, header, body):
        if self.trade_subscriber is not None:
            self.trade_subscriber = None
            write(self.sock, header, body)
        else:
            print('Not subscribe trade')

    def _run(self):
        read_buf = ReadBuffer()
        while True:
            try:
                msgs = read(self.sock, read_buf)
            except:
                raise

            for packet in msgs:
                msg_id = packet['header']['_id'] 
                header_type = packet['header']['type']
                if msg_id in self.clients:
                    self.clients[msg_id][1] = packet['body']
                    self.clients[msg_id][0].set()
                elif header_type == message.SUBSCRIBE_RESPONSE:
                    code = packet['header']['code']
                    #gevent.spawn(self.subscribers[code], code, packet['body'])
                    self.subscriber_queue.put_nowait((self.subscribers[code], code, packet['body']))
                    #self.subscribers[code](code, packet['body'])
                elif header_type == message.TRADE_SUBSCRIBE_RESPONSE:
                    if self.trade_subscriber is not None:
                        gevent.spawn(self.trade_subscriber, packet['body'])
                        #self.trade_subscriber(packet['body'])


def create_header(header_type, market_type, method_name, vendor='cybos'):
    return {'type': header_type, 
            'market': market_type,
            'method': method_name,
            'vendor': vendor,
            '_id': str(uuid.uuid4())}


def write(sock, header, body):
    msg = {'header': header, 'body': body}
    msg = pickle.dumps(msg)
    msg = HEADER_ID + (len(msg)).to_bytes(HEADER_SIZE, byteorder='big') + msg
    total_len = len(msg)
    while True:
        try:
            sent = sock.send(msg)
            total_len -= sent
            if total_len == 0:
                break
            else:
                msg = msg[sent:]
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                print(CLIENT_NAME, 'ERROR) EAGAIN or EWOULDBLOCK(write) sent message len', e)
                select.select([], [sock], [])
                continue
            else:
                print(CLIENT_NAME, 'ERROR) write socket error, reraise')
                print(header, body)
                print(sys.exc_info())
                print(traceback.format_exc())
                raise Exception('ERROR) socket write error', sock)
        except Exception as e:
            print(CLIENT_NAME, 'ERROR) write error, reraise', e)
            print(header, body)
            print(sys.exc_info())
            print(traceback.format_exc())
            raise


def read(sock, read_buf):
    msg_list = []
    while True:
        try:
            msg = sock.recv(READ_PACKET_SIZE)
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                # TODO: check whether need to handle msg if some of packet is read
                print(CLIENT_NAME + ' ERROR) EAGAIN or EWOULDBLOCK(read) receive message len', e)
                select.select([sock], [], [])
                continue
            else:
                print(CLIENT_NAME, 'ERROR) read socket error, reraise')
                print(sys.exc_info())
                print(traceback.format_exc())
                raise Exception('ERROR) socket read error', sock)
        except:
            print(CLIENT_NAME, 'ERROR) read error, reraise')
            print(sys.exc_info())
            print(traceback.format_exc())
            raise
        break

    if len(msg) == 0:
        raise Exception(CLIENT_NAME + ' Length 0 Socket error', sock)

    #print('read', len(msg))
    read_buf.buf += msg

    while True:
        #print('BUF len', len(read_buf.buf))
        if len(read_buf.buf) < HEADER_SIZE + 2:
            break
       
        if read_buf.buf[:len(HEADER_ID)] != HEADER_ID:
            for h in read_buf.buf:
                print(hex(h), end=' ')
            print('')
            read_buf.buf = b''
            #read_buf.buf = read_buf.buf[len(HEADER_ID):]
            print(CLIENT_NAME, ' ERROR) Cannot read HEADER_ID, msg len', len(read_buf.buf))
            continue
        
        header_len = int.from_bytes(read_buf.buf[len(HEADER_ID):len(HEADER_ID) + HEADER_SIZE], byteorder='big')

        #print('HEADER len', header_len)
        if len(read_buf.buf) < header_len + HEADER_SIZE + len(HEADER_ID):
            break

        data = read_buf.buf[len(HEADER_ID)+HEADER_SIZE:len(HEADER_ID)+HEADER_SIZE+header_len]
        read_buf.buf = read_buf.buf[len(HEADER_ID)+HEADER_SIZE+header_len:]
        #print('LEFT packet', len(read_buf.buf))
        data = pickle.loads(data)
        msg_list.append(data)

    return msg_list


def dispatch_message_for_collector(sock, read_buf,
                    collector_handler = None, 
                    request_handler=None, 
                    response_handler = None, 
                    subscribe_handler=None, 
                    subscribe_response_handler=None,
                    request_trade_handler=None,
                    response_trade_handler=None,
                    subscribe_trade_handler=None,
                    subscribe_trade_response_handler=None):
    try:
        msgs = read(sock, read_buf)
    except Exception as e:
        print('ERROR OCCURED', e)
        raise

    for packet in msgs:
        header_type = packet['header']['type']
        if header_type == message.REQUEST and request_handler is not None:
            request_handler(sock, packet['header'], packet['body'])
        elif header_type == message.SUBSCRIBE and subscribe_handler is not None:
            subscribe_handler(sock, packet['header'], packet['body'])
        elif header_type == message.COLLECTOR and collector_handler is not None:
            collector_handler(sock, packet['header'], packet['body'])
        elif header_type == message.RESPONSE and response_handler is not None:
            response_handler(sock, packet['header'], packet['body'])
        elif header_type == message.SUBSCRIBE_RESPONSE and subscribe_response_handler is not None:
            subscribe_response_handler(sock, packet['header'], packet['body'])
        elif header_type == message.REQUEST_TRADE and request_trade_handler is not None:
            request_trade_handler(sock, packet['header'], packet['body'])
        elif header_type == message.RESPONSE_TRADE and response_trade_handler is not None:
            response_trade_handler(sock, packet['header'], packet['body'])
        elif header_type == message.TRADE_SUBSCRIBE and subscribe_trade_handler is not None:
            subscribe_trade_handler(sock, packet['header'], packet['body']) 
        elif header_type == message.TRADE_SUBSCRIBE_RESPONSE and subscribe_trade_response_handler is not None:
            subscribe_trade_response_handler(sock, packet['header'], packet['body'])
        else:
            print('Unknown header type', packet['header'])
            

def dispatch_message(sock,
                    collector_handler = None, 
                    request_handler=None, 
                    response_handler = None, 
                    subscribe_handler=None, 
                    subscribe_response_handler=None,
                    request_trade_handler=None,
                    response_trade_handler=None,
                    subscribe_trade_handler=None,
                    subscribe_trade_response_handler=None):

    read_buf = ReadBuffer()

    while True:
        try:
            msgs = read(sock, read_buf)
        except:
            raise

        for packet in msgs:
            header_type = packet['header']['type']
            if header_type == message.REQUEST and request_handler is not None:
                request_handler(sock, packet['header'], packet['body'])
            elif header_type == message.SUBSCRIBE and subscribe_handler is not None:
                subscribe_handler(sock, packet['header'], packet['body'])
            elif header_type == message.COLLECTOR and collector_handler is not None:
                collector_handler(sock, packet['header'], packet['body'])
            elif header_type == message.RESPONSE and response_handler is not None:
                response_handler(sock, packet['header'], packet['body'])
            elif header_type == message.SUBSCRIBE_RESPONSE and subscribe_response_handler is not None:
                subscribe_response_handler(sock, packet['header'], packet['body'])
            elif header_type == message.REQUEST_TRADE and request_trade_handler is not None:
                request_trade_handler(sock, packet['header'], packet['body'])
            elif header_type == message.RESPONSE_TRADE and response_trade_handler is not None:
                response_trade_handler(sock, packet['header'], packet['body'])
            elif header_type == message.TRADE_SUBSCRIBE and subscribe_trade_handler is not None:
                subscribe_trade_handler(sock, packet['header'], packet['body'])
            elif header_type == message.TRADE_SUBSCRIBE_RESPONSE and subscribe_trade_response_handler is not None:
                subscribe_trade_response_handler(sock, packet['header'], packet['body'])
            else:
                print('Unknown header type', packet['header'])
            
