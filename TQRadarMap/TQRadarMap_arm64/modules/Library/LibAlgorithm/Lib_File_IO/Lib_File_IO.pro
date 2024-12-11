QT -= gui

TEMPLATE = lib
DEFINES += LIB_FILE_IO_LIBRARY

CONFIG += c++11

include(../LibAlgorithm.pri)

# The following define makes your compiler emit warnings if you use
# any Qt feature that has been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

# You can also make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
    lib_file_io.cpp

HEADERS += \
    ../../../../include/Util/struct_VTBnew.h \
    ../../../../include/Util/struct_WeatherRadar.h \
    lib_file_io.h

# Default rules for deployment.
unix {
    target.path = /usr/lib
}
!isEmpty(target.path): INSTALLS += target

TARGET = FileIO

win32{
contains(DEFINES, WIN64){
LIBS += -L$$PWD/../../../../lib/zlib/x64/ -lzlibwapi
}
else{
Debug:LIBS += \
     -L$$PWD/../../../../lib/zlib/x86/debug/ -lzlibwapi

Release:LIBS += \
     -L$$PWD/../../../../lib/zlib/x86/release/ -lzlibwapi
}
}

unix:!macx{
LIBS += -L$$PWD/../../../../dist/lib/ -lz
}


QMAKE_POST_LINK += cp $$DESTDIR/libFileIO.so.1.0.0 $$DESTDIR/../../../../../dist/lib/libFileIO.so
