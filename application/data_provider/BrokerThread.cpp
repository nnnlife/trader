#include "BrokerThread.h"

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


#include <QDebug>

BrokerThread::BrokerThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0){
    stub_ = stub;
}


void BrokerThread::run() {
    ClientContext context;
    Empty empty;
    BrokerSummary data;
    std::unique_ptr<ClientReader<BrokerSummary> > reader(
        stub_->ListenBrokerSummary(&context, empty)); 

    while (reader->Read(&data)) {
        emit summaryArrived(new BrokerSummary(data));
    }
    Status status = reader->Finish();
    if (status.ok()) {
        std::cout << "BrokerThread succeeded" << std::endl;
    } else {
        std::cout << "BrokerThread Failed " << status.error_message() << std::endl;
    }

}
