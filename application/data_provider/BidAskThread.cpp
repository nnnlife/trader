#include "BidAskThread.h"

#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>
#include <google/protobuf/util/time_util.h>
#include <google/protobuf/timestamp.pb.h>


using grpc::Channel;
using grpc::ClientContext;
using grpc::ClientReader;
using grpc::ClientReaderWriter;
using grpc::ClientWriter;
using grpc::Status;
using google::protobuf::util::TimeUtil;
using google::protobuf::Timestamp;
using google::protobuf::Empty;

using stock_api::Stock;
using stock_api::StockCodeQuery;
using stock_api::StockQuery;
using stock_api::CybosDayDatas;
using stock_api::CybosDayData;
using stock_api::CybosTickData;


BidAskThread::BidAskThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0){
    stub_ = stub;
}


void BidAskThread::run() {
    ClientContext context;
    Empty empty;
    CybosBidAskTickData data;
    std::unique_ptr<ClientReader<CybosBidAskTickData> > reader(
        stub_->ListenCybosBidAsk(&context, empty)); 
    while (reader->Read(&data)) {
        emit tickArrived(new CybosBidAskTickData(data));
        //std::cout << "BidAsk Data" << "first ask: " << data.first_ask_price() << "\tfirst_bid: " << data.first_bid_price() << std::endl;
    }
    Status status = reader->Finish();
    if (status.ok()) {
        std::cout << "BidAsk Tick succeeded" << std::endl;
    } else {
        std::cout << "BidAsk Tick Failed " << status.error_message() << std::endl;
    }
}
