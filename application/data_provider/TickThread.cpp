#include "TickThread.h"

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


TickThread::TickThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0){
    stub_ = stub;
}


void TickThread::run() {
    ClientContext context;
    Empty empty;
    CybosTickData data;
    std::unique_ptr<ClientReader<CybosTickData> > reader(
        stub_->ListenCybosTickData(&context, empty)); 
    while (reader->Read(&data)) {
        emit tickArrived(new CybosTickData(data));
        //std::cout << "Tick Data" << "current price: " << data.current_price() << "\tcum_volume: " << data.cum_volume() << std::endl;
    }
    Status status = reader->Finish();
    if (status.ok()) {
        std::cout << "Tick succeeded" << std::endl;
    } else {
        std::cout << "Tick Failed " << status.error_message() << std::endl;
    }

}
