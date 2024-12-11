
#指定发布文件路径
CONFIG(release, debug|release):{
DESTDIR = $$PWD/bin/release
}
else:CONFIG(debug, debug|release): {
DESTDIR = $$PWD/bin/debug
}

QMAKE_CXXFLAGS += -fopenmp
QMAKE_CXXFLAGS_DEBUG += -fopenmp
LIBS += -fopenmp
LIBS += -L$$PWD/../../../dist/lib   -lbz2
INCLUDEPATH += $$PWD/../../../include/Util


#INCLUDEPATH += $$PWD/../../../../../../../../usr/include/opencv
#INCLUDEPATH +=  $$PWD/../../../../../../../../usr/include/opencv2
#INCLUDEPATH +=  $$PWD/../../../../../../../../usr/include/opencv2/core
#INCLUDEPATH +=  $$PWD/../../../../../../../../usr/include/opencv2/highgui

#LIBS += -L/usr/lib64  -lopencv_core -lopencv_highgui -lopencv_imgproc



