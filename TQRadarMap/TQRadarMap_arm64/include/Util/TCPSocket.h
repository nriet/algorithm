// 
// File:   TCPSocket.h
// Author: John_Tsai
//
// Created on 2017-6-26
//

#ifndef _TCPSocket_H
#define	_TCPSocket_H

#include "SocketTrans.h"

class TCPSocket : public SocketTrans {
public:
    TCPSocket();
    ~TCPSocket() override;

    int  CreateSocket(int nPort,const char* strLocalIP) override;      /*创建插口 */
    int  CreateAndBindSocket(int nPort,const char* strLocalIP) override;
    int  RecvData(char*  buffer,int len) override; /*接收数据 */
    int  SendData(char*  buffer,int len) override;
    void closeMySocket() override;

    int  ClientConnect();
public:
	char* GetHostIp(unsigned char bAdapter = 0);
	int GetHostIp(char pLpStr[10][100]);  
	int SocketInit();
	int m_bUseable;
    char* m_strPeerAddress;
    unsigned int m_nPeerPort;
    
//    _FRMMEA m_frmMeaLocal;

private:
	/*
	int sockfd;
   // int socklen;
    struct sockaddr_in localaddr;
	SOCKET sock_client;
	struct sockaddr_in clientaddr;*/
    bool ClientFlag;//0:无连接 1有连接
    int sockClient;
   // int socklen;
    struct sockaddr_in serveraddr;
    struct sockaddr_in clientaddr;
};

#endif	/* _TCPSocket_H */

