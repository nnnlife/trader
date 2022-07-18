#include "TimeThread.h"

#include <grpc/grpc.h>
#include <grpcpp/channel.h>
#include <grpcpp/client_context.h>
#include <grpcpp/create_channel.h>
#include <grpcpp/security/credentials.h>
#include <google/protobuf/util/time_util.h>
#include <google/protobuf/timestamp.pb.h>
#include <QDebug>


using grpc::Channel;
using grpc::ClientContext;
using grpc::ClientReader;
using grpc::ClientReaderWriter;
using grpc::ClientWriter;
using grpc::Status;
using google::protobuf::Timestamp;
using google::protobuf::Empty;



TimeThread::TimeThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0){
    stub_ = stub;
}


void TimeThread::run() {
    ClientContext context;
    Empty empty;
    Timestamp data;
    std::unique_ptr<ClientReader<Timestamp> > reader(
        stub_->ListenCurrentTime(&context, empty)); 
    while (reader->Read(&data)) {
        emit timeInfoArrived(new Timestamp(data));
    }
    Status status = reader->Finish();
    if (!status.ok()) {
        std::cout << "TimeInfo Failed " << status.error_message() << std::endl;
    }
}
