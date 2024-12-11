QT -= gui

TEMPLATE = lib
DEFINES += LIB_PPIS_LIBRARY

CONFIG += c++11
include(../LibAlgorithm.pri)
# The following define makes your compiler emit warnings if you use
# any Qt feature that has been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS
INCLUDEPATH += ..\include
# You can also make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
    lib_ppis.cpp

HEADERS += \
    ../../../../include/Util/NrietAlgorithm.h \
    lib_ppis.h

# Default rules for deployment.
unix {
    target.path = /usr/lib
}
!isEmpty(target.path): INSTALLS += target
TARGET = PPIS
QMAKE_POST_LINK += cp $$DESTDIR/libPPIS.so.1.0.0 $$DESTDIR/../../../../../dist/lib/libPPIS.so
