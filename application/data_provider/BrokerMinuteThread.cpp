#include "BrokerMinuteThread.h"

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


BrokerMinuteThread::BrokerMinuteThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0){
    stub_ = stub;
}


void BrokerMinuteThread::run() {
    ClientContext context;
    Empty empty;
    BrokerMinuteTick data;
    std::unique_ptr<ClientReader<BrokerMinuteTick> > reader(
        stub_->ListenBrokerMinuteTick(&context, empty)); 

    while (reader->Read(&data)) {
        emit brokerMinuteTickArrived(new BrokerMinuteTick(data));
    }
    Status status = reader->Finish();
    if (status.ok()) {
        std::cout << "BrokerMinuteThread succeeded" << std::endl;
    } else {
        std::cout << "BrokerMinuteThread Failed " << status.error_message() << std::endl;
    }

}
