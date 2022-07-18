/****************************************************************************
** Generated QML type registration code
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <QtQml/qqml.h>
#include <QtQml/qqmlmoduleregistration.h>

#include <LongModel.h>
#include <TransactionModel.h>

void qml_register_types_order_backend()
{
    qmlRegisterTypesAndRevisions<LongModel>("order.backend", 1);
    qmlRegisterTypesAndRevisions<TransactionModel>("order.backend", 1);
    qmlRegisterModule("order.backend", 1, 0);
}

static const QQmlModuleRegistration registration("order.backend", 1, qml_register_types_order_backend);
