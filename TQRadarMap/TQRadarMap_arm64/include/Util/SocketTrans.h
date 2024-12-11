#ifndef SOCKETTRANS_H
#define SOCKETTRANS_H


#include <sys/types.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <net/if.h>
#include <arpa/inet.h>
#include <stdio.h>
#include <stdlib.h>
#include <netdb.h>
#include <iostream>
#include <string.h>
#include <unistd.h>
#include <exception>

#define CREATE_SOCKER_ERROR  -1
#define CONNECT_SOCKER_ERROR -2
#define SOCKER_BUSY      -3
#define SOCKET_CREATE_SUCCESS 1
class SocketTrans
{
public:
    virtual ~SocketTrans()= default;
    virtual int  CreateSocket(int nPort,const char* strLocalIP) = 0;      /*创建插口 */
    virtual int  CreateAndBindSocket(int nPort,const char* strLocalIP) = 0;
    virtual int  RecvData(char*  buffer,int len) = 0; /*接收数据 */
    virtual int  SendData(char*  buffer,int len) = 0;
    virtual void closeMySocket() = 0;
    int sockfd = 0;
};

#endif // SOCKETTRANS_H
