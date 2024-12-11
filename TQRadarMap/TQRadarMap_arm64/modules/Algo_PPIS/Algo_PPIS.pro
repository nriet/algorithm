# 指定项目的配置信息
TEMPLATE = app

CONFIG += c++11 console
CONFIG -= app_bundle
QT -= gui

# The following define makes your compiler emit warnings if you use
# any Qt feature that has been marked deprecated (the exact warnings
# depend on your compiler). Please consult the documentation of the
# deprecated API in order to know how to port your code away from it.
DEFINES += QT_DEPRECATED_WARNINGS

DEFINES += ALGORITHM_DEBUG
# You can also make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
# You can also select to disable deprecated APIs only up to a certain version of Qt.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

contains(DEFINES, ALGORITHM_DEBUG){

    DEFINES += ALGORITHM_DEBUG_FILE_IO
    #DEFINES += ALGORITHM_DEBUG_PPI_S

    contains(DEFINES, ALGORITHM_DEBUG_FILE_IO){
        INCLUDEPATH += \
                    $$PWD/../Library/LibAlgorithm/Lib_File_IO

        HEADERS += \
                $$PWD/../Library/LibAlgorithm/Lib_File_IO/lib_file_io.h \

        SOURCES += \
                $$PWD/../Library/LibAlgorithm/Lib_File_IO/lib_file_io.cpp \
    }

    contains(DEFINES, ALGORITHM_DEBUG_PPI_S){
        INCLUDEPATH += \
                    $$PWD/../Library/LibAlgorithm/Lib_PPIS

        HEADERS += \
                $$PWD/../Library/LibAlgorithm/Lib_PPIS/lib_ppis.h \

        SOURCES += \
                $$PWD/../Library/LibAlgorithm/Lib_PPIS/lib_ppis.cpp \
    }
}

# 项目名称
TARGET = Algo_PPIS


INCLUDEPATH += \
    $$PWD/../../include/Util \
    $$PWD/../Library/LibAlgorithm/Lib_File_IO \
    $$PWD/../Library/LibAlgorithm/Lib_PPIS \

HEADERS += \


SOURCES += \
        main.cpp \
        $$PWD/../../res/Util/IniParser/INIParser.cpp

DESTDIR = $$PWD/../../dist/bin

LIBS += \
    -lz     \
    -lbz2   \
    -fopenmp \
    -ldl


## Default rules for deployment.
#qnx: target.path = /tmp/$${TARGET}/bin
#else: unix:!android: target.path = /opt/$${TARGET}/bin
#!isEmpty(target.path): INSTALLS += target
