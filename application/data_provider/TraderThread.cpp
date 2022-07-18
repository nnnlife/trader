#include "TraderThread.h"

#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>
#include <google/protobuf/util/time_util.h>
#include <google/protobuf/timestamp.pb.h>
#include <QDebug>


using grpc::ClientContext;
using google::protobuf::Empty;
using grpc::ClientReader;
using grpc::Status;

using stock_api::TradeMsg;
using stock_api::TradeMsgType;
using stock_api::OrderType;


TraderThread::TraderThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0){
    stub_ = stub;
}


void TraderThread::order(const QString &code, int price, int quantity, int percentage, OrderMethod m, bool isBuy) {
    ClientContext context;
    TradeMsg msg;
    msg.set_msg_type(TradeMsgType::ORDER_MSG);
    OrderMsg *orderMsg = new OrderMsg;
    orderMsg->set_code(code.toStdString());
    orderMsg->set_is_buy(isBuy);
    orderMsg->set_price(price);
    orderMsg->set_quantity(quantity);
    orderMsg->set_percentage(percentage);
    orderMsg->set_method(m);
    orderMsg->set_order_type(OrderType::NEW);
    msg.set_allocated_order_msg(orderMsg);

    Empty empty;
    stub_->RequestToTrader(&context, msg, &empty);
}


void TraderThread::run() {
    ClientContext context;
    Empty empty;
    OrderResult data;
    std::unique_ptr<ClientReader<OrderResult> > reader(
        stub_->ListenOrderResult(&context, empty));
    while (reader->Read(&data)) {
        emit orderResultArrived(new OrderResult(data));        
    }
    Status status = reader->Finish();
    if (status.ok()) {
        std::cout << "OrdeResult succeeded" << std::endl;
    } else {
        std::cout << "OrderResult Failed " << status.error_message() << std::endl;
    }

}
