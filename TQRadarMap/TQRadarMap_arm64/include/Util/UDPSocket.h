// 
// File:   UDPSocket.h
// Author: John_Tsai
//
// Created on 2017-6-26
//

#ifndef _UDPSocket_H
#define	_UDPSocket_H

#include "SocketTrans.h"

using namespace std;

class UDPSocket  : public SocketTrans{
public:
    UDPSocket();
    ~UDPSocket() override;

    int  CreateSocket(int nPort,const char* strLocalIP) override;      /*创建插口 */
    int  CreateAndBindSocket(int nPort,const char* strLocalIP) override;
    int  RecvData(char*  buffer,int len) override; /*接收数据 */
    int  SendData(char*  buffer,int len) override; /*发送数据*/
    void closeMySocket() override;
    int UdpGroupCreateSocket(int nPort, const char* strLocalIP);
public:
	//网络设置函数，1 = 成功，0 = 失败
    bool JoinGroup(const char * groupaddress,const  char * interaddress);
    bool DropGroup(char * groupaddress, char * interaddress);

private:
    bool m_bUseable;
    char* m_strPeerAddress;
    unsigned int m_nPeerPort;
    const char* strDestAddr;
    int m_DesPort;
    struct sockaddr_in localaddr;
protected:
    int PharseAddress(struct sockaddr_in * returnaddr,const char * address = nullptr);

};

#endif	/* _UDPSocket_H */

