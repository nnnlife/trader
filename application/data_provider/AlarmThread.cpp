#include "AlarmThread.h"

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


AlarmThread::AlarmThread(std::shared_ptr<stock_api::Stock::Stub> stub)
: QThread(0){
    stub_ = stub;
}


void AlarmThread::run() {
    ClientContext context;
    Empty empty;
    CybosStockAlarm data;
    std::unique_ptr<ClientReader<CybosStockAlarm> > reader(
        stub_->ListenCybosAlarm(&context, empty)); 
    while (reader->Read(&data)) {
        emit alarmArrived(new CybosStockAlarm(data));
    }
    Status status = reader->Finish();
    if (status.ok()) {
        std::cout << "Alarm succeeded" << std::endl;
    } else {
        std::cout << "Alarm Failed " << status.error_message() << std::endl;
    }

}
