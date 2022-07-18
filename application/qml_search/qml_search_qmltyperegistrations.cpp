/****************************************************************************
** Generated QML type registration code
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include <QtQml/qqml.h>
#include <QtQml/qqmlmoduleregistration.h>

#include <SearchBackend.h>

void qml_register_types_search_backend()
{
    qmlRegisterTypesAndRevisions<SearchBackend>("search.backend", 1);
    qmlRegisterModule("search.backend", 1, 0);
}

static const QQmlModuleRegistration registration("search.backend", 1, qml_register_types_search_backend);
