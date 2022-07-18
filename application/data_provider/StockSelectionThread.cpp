#include "StockSelectionThread.h"
#include <google/protobuf/util/time_util.h>
#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>

using grpc::Channel;
using grpc::ClientContext;
using grpc::ClientReader;
using grpc::ClientReaderWriter;
using grpc::ClientWriter;
using grpc::Status;

using google::protobuf::Empty;
using google::protobuf::Timestamp;

using stock_api::StockCodeQuery;
using google::protobuf::util::TimeUtil;


StockSelectionThread::StockSelectionThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0) {
    stub_ = stub;
}


void StockSelectionThread::run() {
    ClientContext context;
    Empty empty;
    StockCodeQuery data;
    std::unique_ptr<ClientReader<StockCodeQuery> > reader(
        stub_->ListenCurrentStock(&context, empty)); 
    while (reader->Read(&data)) {
        emit stockCodeChanged(QString::fromStdString(data.code()));
    }
    Status status = reader->Finish();
    if (status.ok()) {
        std::cout << "StockSelectionThread succeeded" << std::endl;
    } else {
        std::cout << "StockSelectionThread Failed " << status.error_message() << std::endl << status.error_details() << std::endl;
    }
}
