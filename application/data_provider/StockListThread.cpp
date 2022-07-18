#include "StockListThread.h"
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

using stock_api::ListType;

using google::protobuf::util::TimeUtil;


StockListThread::StockListThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0) {
    stub_ = stub;
}


void StockListThread::run() {
    ClientContext context;
    Empty empty;
    ListType data;
    std::unique_ptr<ClientReader<ListType> > reader(
        stub_->ListenListChanged(&context, empty)); 
    while (reader->Read(&data)) {
        std::cout << "StockListChanged: " << data.type_name() << std::endl;
        emit stockListChanged(QString::fromStdString(data.type_name()));
    }

    Status status = reader->Finish();
    if (status.ok()) {
        std::cout << "StockListThread succeeded" << std::endl;
    } else {
        std::cout << "StockListThread Failed " << status.error_message() << std::endl << status.error_details() << std::endl;
    }
}
