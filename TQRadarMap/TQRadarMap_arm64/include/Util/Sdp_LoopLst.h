//////////////////////////////////////////////////////////////////////
// Sdp_CLoopLst<TYPE, ARG_TYPE>   环型队列C++模板类
// Sdp_LoopLSt.h:   interface for the CMyList template class.
//
// Author: TangBing
//
// Created on 2006-04-12
//
//////////////////////////////////////////////////////////////////////

#if !defined(SDP_LOOPLST_H_INCLUDED_)
#define SDP_LOOPLST_H_INCLUDED_
//#include <semaphore.h>
//#include <memory.h>
//#define SetEvent(a) sem_post(&a)
//typedef	unsigned long 	DWORD;
//#define	DWORD		unsigned int		//190907feng

template<class TYPE, class ARG_TYPE>
class Sdp_CLoopLst 
{
// Attributes--------------------------------------------------------------
protected:
	TYPE* m_pData;  //队列内容
	int m_nSize;    //队列容量（允许最大单元数）
	int m_nW;		//队尾指针（始终指向即当新入队的单元--环型队列写指针）
	int m_nR;		//队头指针（始终指向即当  出队的单元--环型队列读指针）

	int volatile m_nEleNum;	//当前队列中单元数

#if defined(WIN32)
	HANDLE		hMutex;																			// 互斥量
#else
	#ifdef	COMPILE_IN_LINUX
		sem_t	hMutex;
	#else	// VXWorks
		SEM_ID	hMutex		;																	// 互斥量
	#endif //COMPILE_IN_LINUX
#endif

private:
	int m_nScan;	//当前遍历指针

public:
// Construction / Destruction---------------------------------------------
	//--默认环型队列构造函数
	//  队列容量为0，在使用前要另调用SetSize设置队列容量
	Sdp_CLoopLst()
	{
		m_pData = NULL;
		m_nSize = m_nW = m_nR = m_nEleNum = 0;
		m_nScan = 0;
		//初始化互斥量
	#if defined(WIN32)
		hMutex = CreateEvent(
			NULL, 
			FALSE,	// manual_reset event //TB20150625一定要改成自动重置(要不直接用CMutex)，否则会出现两个任务同时被一次性触发，读写指针，单元数仍会错误
			TRUE,
		NULL );
	#else
		#ifdef	COMPILE_IN_LINUX
			sem_init(&hMutex,0,1);												
		#else	// VXWorks
			hMutex = semBCreate (SEM_Q_PRIORITY, SEM_FULL);
		#endif //COMPILE_IN_LINUX
	#endif
	}

	//--环型队列构造函数
	//  输入参数:  nSize 队列容量
	Sdp_CLoopLst(int nSize)
	{
		SetSize(nSize);
	}
		
	//--环型队列析构函数
	~Sdp_CLoopLst()
	{
		if (m_pData != NULL)
			delete[] (unsigned char*)m_pData;
	}

	int GetR()
	{
		return m_nR;
	}

	int GetW()
	{
		return m_nW;
	}

	// Interface: Operations about Attributes------------------------------------
	
	/*****************************************************************
	接口名称：  SetSize
	接口类型：  属性操作类
	描述：      设置环型队列容量
	共享内存：	无
	信息：      无
	硬件：      无
	参数：      int nNewSize : 队列容量
	返回值：    无
	错误码：    无
	注意项：    无
	函数说明： 	该接口用来设置环型队列容量，
				如果设置容量为0，则等同于清空队列。
	*******************************************************************/
	void SetSize(int nNewSize)
	{
		if (nNewSize == 0)
		{
			RemoveAll();
			return;
		}
		if (m_pData != NULL)
		{
			RemoveAll();
		}
		//m_pData = (TYPE*) new unsigned char[nNewSize * sizeof(TYPE)];
		m_pData = new TYPE[nNewSize];
		m_nSize = nNewSize;
		m_nW = m_nR = m_nEleNum = 0;
		m_nScan = m_nSize-1;
	}

	//--查询环型队列容量
	//  返回参数 : 队列容量
	/*****************************************************************
	接口名称：  GetSize
	接口类型：  属性操作类
	描述：      查询环型队列容量
	共享内存：	无
	信息：      无
	硬件：      无
	参数：      int nNewSize : 队列容量
	返回值：    无
	错误码：    无
	注意项：    无
	函数说明： 	该接口用来设置环型队列容量，
				如果设置容量为0，则等同于清空队列。
	*******************************************************************/
	inline int GetSize() const
	{
		return m_nSize; 
	}
	
	//--查询当前队列中单元数
	//  返回参数 : 当前队列中单元数
	inline int GetElementNum() const
	{
		return m_nEleNum; 
	}

	//--查询队列内部状态
	//	参数值：pVector 用于返回队列中所有单元内容，由调用者保证分配与队列容量一致的内存
	//			nR      用于返回队头指针（读指针）
	//			nW      用于返回队尾指针（写指针）
	//			nEleNum 用于返回当前队列中单元数
	//			nSize   用于返回队列容量
	void AskState(ARG_TYPE* pVector, int& nR, int& nW, int& nEleNum, int& nSize) const
	{
		memcpy((void*)pVector, (void*)(m_pData), m_nSize*sizeof(TYPE));
		nR = m_nR;
		nW = m_nW;
		nEleNum = m_nEleNum;
		nSize = m_nSize;
	}

	// Interface: Operations about resetting / inlist / outlist-----------------------------
	//--清空队列，释放所有单元，容量归0
	//  free the memory for all the loop
	void RemoveAll() 	
	{ 
		// shrink to nothing
		if (m_pData != NULL)
		{
			delete[] (unsigned char*)m_pData;
			m_pData = NULL;
		}
		m_nSize = m_nW = m_nR = m_nEleNum = 0;
	}
	
	//--复位队列，所有单元内容清0，容量不变
	//  Clean up all the loop
	void CleanAll()	
	{
		memset(m_pData,0, m_nSize*sizeof(TYPE));
		m_nW = m_nR = m_nEleNum = 0;
	}


	void CleanAll2No0()	
	{
		m_nW = m_nR = m_nEleNum = 0;
	}


	//--单个单元的入队操作
	//	popin the new element to the tail
	//	参数值：newElement 新入队的单元 (//TB070910: 改为传入引用，否则在结构很大时，易报stack overflow)
	//  返回参数：实际入队单元数
	//			0：表示队列已满，入队请求未被接受
	//			1：表示指定的单个单元（拷贝）已入队
	int InElement (const ARG_TYPE& newElement)	
	{
	DWORD dwWaitResult;
		if (m_nEleNum >= m_nSize)
			return 0;
	#if defined(WIN32)
		dwWaitResult = WaitForSingleObject(hMutex,INFINITE);
	//		ResetEvent(hMutex);
	#else  //not defined(WIN32) 
		#ifdef	COMPILE_IN_LINUX
			dwWaitResult = sem_wait(&hMutex);
		#else	// VXWorks
			dwWaitResult = semTake(hMutex,WAIT_FOREVER);
		#endif //COMPILE_IN_LINUX
	#endif //end of '#ifdef(WIN32)'
		m_pData[m_nW] = newElement; 
		if (++m_nW >= m_nSize)	m_nW = 0;
		m_nEleNum++;
		SetEvent(hMutex);
		return 1;
	}

	//--单个单元的出队操作
	//  popout the element from the head
	//	参数值：headElement 用来接收出队单元
	//  返回参数：实际出队单元数
	//			0：表示队列已空，获取出队单元失败
	//			1：队头单元出队
	int OutElement(ARG_TYPE& headElement)	
	{
	DWORD dwWaitResult;
	#if defined(WIN32)
		 dwWaitResult = WaitForSingleObject(hMutex,INFINITE);
		 //		ResetEvent(hMutex);
	#else  //not defined(WIN32) 
		#ifdef	COMPILE_IN_LINUX
			 dwWaitResult = sem_wait(&hMutex);
		#else	// VXWorks
			 dwWaitResult = semTake(hMutex,WAIT_FOREVER);
		#endif //COMPILE_IN_LINUX
	#endif //end of '#ifdef(WIN32)'

		if (m_nEleNum>0)
		{
			headElement = m_pData[m_nR];
		//	m_pData[m_nR] = 0;	//clean the cell after read （NOTE: Do this as followings）
			memset((void*)(&m_pData[m_nR]), 0, sizeof(TYPE));									//清0出队后的空单元

			if (++m_nR >= m_nSize)	m_nR = 0;
			m_nEleNum--;
			SetEvent(hMutex);
			return 1;
		}
		else
		{
			SetEvent(hMutex);
			return 0; //no element in loop
		}
	}
	

	//--多个单元的入队操作
	//Popin the new vector to the tail
	//	参数值：	pnew	指向新入队的单元数组的指针（其指向的单元后有效单元数不小于nEleNum）
	//				nEleNum	新入队单元数
	//  返回参数：	实际入队单元数
	//	注：该操作会将请求入队的单元依次入队，直到队列满或本次入队数达到nEleNum
	int InVector (const ARG_TYPE* pNew, int nEleNum)		
	{
		int n=0;
		for(n=0; n<nEleNum; n++)
		{
			if(InElement(pNew[n]) == 0)
				break;
		}
		return n;
	}

	//--获取队列中前nEleNum单元，但不出队　//TB20160313ADD
	//Get certain elements from the head
	//	参数值：	pVector	用于接收获取的单元数组的指针（其指向的单元后有效单元数不小于nEleNum）
	//				nEleNum	期望获取单元数
	//  返回参数：	实际获取单元数
	int GetVectorFromHead(ARG_TYPE* pVector, int nEleNum)	
	{
	DWORD dwWaitResult;
	int n=0;
		if ( nEleNum >m_nEleNum )
			nEleNum	= m_nEleNum;
		if (nEleNum>0)
		{
		#if defined(WIN32)
			dwWaitResult = WaitForSingleObject(hMutex,INFINITE);
			//		ResetEvent(hMutex);
		#else  //not defined(WIN32) 
			#ifdef	COMPILE_IN_LINUX
				dwWaitResult = sem_wait(&hMutex);
			#else	// VXWorks
				dwWaitResult = semTake(hMutex,WAIT_FOREVER);
			#endif //COMPILE_IN_LINUX
		#endif //end of '#ifdef(WIN32)'

			int nScan = m_nR; 
			for (n=0; n<nEleNum; n++)
			{
				pVector[n] = m_pData[nScan];
				if (++nScan >= m_nSize)	nScan = 0;
			}
			SetEvent(hMutex);
		}
		return nEleNum;
	}

	//--多个单元的出队操作
	//Popout certain elements from the head
	//	参数值：	pVector	用于接收出队的单元数组的指针（其指向的单元后有效单元数不小于nEleNum）
	//				nEleNum	期望出队单元数
	//  返回参数：	实际出队单元数
	//	注：当队列中当前在队单元数多于nEleNum时，该操作成功，返回值为nEleNum;
	//		否则，出队请求被拒绝，返回0，队列状态不变。
	int OutVector(ARG_TYPE* pVector, int nEleNum)	
	{
	DWORD dwWaitResult;
	int n=0;
	#if defined(WIN32)
		dwWaitResult = WaitForSingleObject(hMutex,INFINITE);
		//		ResetEvent(hMutex);
	#else  //not defined(WIN32) 
		#ifdef	COMPILE_IN_LINUX
			dwWaitResult = sem_wait(&hMutex);	
		#else	// VXWorks
			dwWaitResult = semTake(hMutex,WAIT_FOREVER);
		#endif //COMPILE_IN_LINUX
	#endif //end of '#ifdef(WIN32)'

		if (m_nEleNum >= nEleNum)
		{
			for (n=0; n<nEleNum; n++)
			{
				pVector[n] = m_pData[m_nR];
				memset((void*)(&m_pData[m_nR]), 0, sizeof(TYPE));								//清0出队后的空单元
				if(++m_nR >= m_nSize)	m_nR = 0;
			}
			
		/*	int iSp = m_nSize - m_nR;
			ASSERT(iSp > 0);
			if(iSp >= nEleNum)
			{
				memcpy((void*)pVector, (void*)(&m_pData[m_nR]), nEleNum*sizeof(TYPE));
				memset((void*)(&m_pData[m_nR]), 0, nEleNum * sizeof(TYPE));
				m_nR = (m_nR+nEleNum)%m_nSize;
			}
			else
			{
				memcpy((void*)pVector, (void*)(&m_pData[m_nR]), iSp*sizeof(TYPE));
				memset((void*)(&m_pData[m_nR]), 0, iSp * sizeof(TYPE));
				memcpy((void*)(&pVector[iSp]), (void*)(&m_pData[0]), (nEleNum-iSp)*sizeof(TYPE));
				memset((void*)(&m_pData[0]), 0, (nEleNum-iSp) * sizeof(TYPE));
				m_nR = nEleNum-iSp;
			}
		*/
			m_nEleNum -= nEleNum;
			SetEvent(hMutex);
			return nEleNum;
		}
		else
		{
			SetEvent(hMutex);
			return 0; //if no enough element in loop, do nothing.
		}
	}

	//--多个单元的出队操作
	//Popout certain elements from the head
	//	参数值：	pVector	用于接收出队的单元数组的指针（其指向的单元后有效单元数不小于nEleNum）
	//				nEleNum	期望出队单元数
	//  返回参数：	实际出队单元数
	int OutVector2(ARG_TYPE* pVector, int nEleNum)	
	{
		if ( nEleNum >m_nEleNum )
			nEleNum	= m_nEleNum;
		OutVector(pVector,nEleNum);
		return nEleNum;
	}

	//B--单个单元的强制入队操作
	//	Popin the new element to the tail even the list is full
	//	参数值：newElement 新入队的单元
	//  返回参数：队尾指针
	int ForceInElement (const ARG_TYPE& newElement)	
	{
	DWORD dwWaitResult;
	#if defined(WIN32)
		dwWaitResult = WaitForSingleObject(hMutex,INFINITE);
			//		ResetEvent(hMutex);
	#else  //not defined(WIN32) 
		#ifdef	COMPILE_IN_LINUX
			dwWaitResult = sem_wait(&hMutex);
		#else	// VXWorks
			dwWaitResult = semTake(hMutex,WAIT_FOREVER);
		#endif //COMPILE_IN_LINUX
	#endif //end of '#ifdef(WIN32)'

		m_pData[m_nW] = newElement; 
		if (++m_nW >= m_nSize)	m_nW = 0;
		
		if (m_nEleNum == m_nSize)																//队列原来已满，以上强制插入已挤跑进队时间最长的那一单元，
			m_nR = m_nW;																		//因此要同步更新队头指针
		else
			m_nEleNum++;
		SetEvent(hMutex);
		return m_nW;
	}

	// Interface: Accessing elements--------------------------------------------------

	//B--overloaded operator helpers
	//--得到队列中任一单元的单元值
	//	参数值：	nIndex	指定的单元号（必须有效）
	//  返回参数：	指定的单元内容
	inline TYPE operator[](int nIndex) const
	{
		ASSERT(nIndex >= 0 && nIndex < m_nSize);
		return m_pData[nIndex];
	}

	//B--判得到队列中队头的单元值（历史值）
	//	参数值：	fstEle	用于返回指定的单元内容
	//  返回参数：	true--操作有效，false--操作无效，队列为空
	inline bool GetFst(ARG_TYPE& fstEle) const
	{
	bool rs = false;
		if(m_nEleNum>0)
		{
			fstEle = GetFst();
			rs = true;
		}
		return	rs;
	}

	inline TYPE * FstElement()
	{
		return &m_pData[m_nR];
	}

	//B--得到队列中队头的单元值（历史值）
	//  返回参数：	指定的单元内容
	inline TYPE GetFst() const
	{
		return m_pData[m_nR];
	}
    
	//B--将队头单元扔出队
	//  返回参数：	true--操作有效，false--操作无效，队列为空
	inline bool CleanFst()	
	{
		if (m_nEleNum>0)
		{
			memset((void*)(&m_pData[m_nR]), 0, sizeof(TYPE));									//清0出队后的空单元
			if(++m_nR >= m_nSize)	m_nR = 0;
			m_nEleNum--;
			return true;
		}
		else
			return false; //no element in loop
	}

	//B--得到队列中最新的单元值
	//  返回参数：	指定的单元内容
	inline TYPE GetLast() const
	{
		return m_pData[(m_nW+m_nSize-1)%m_nSize];
	}

	//B--判得到队列中最新的单元值
	//	参数值：	lastEle	用于返回指定的单元内容
	//  返回参数：	true--操作有效，false--操作无效，队列为空
	inline bool GetLast(ARG_TYPE& lastEle) const
	{
		bool rs = false;
		if (m_nEleNum>0)
		{
			lastEle = GetLast();
			rs = true;
		}
		return	rs;
	}

	//B--得到队列中相对队头/队尾指定偏移单元的单元值
	//	参数值：	nOffset	指定的偏移单元数（不要超过队列长度）
	//	注：当nOffset>=0时为相对队头向后偏移，特殊地：为0则返回队头单元
	//      否则          为相对队尾向前偏移，特殊地：为-1时返回最新的单元值
	//  返回参数：	指定的单元内容
	inline TYPE GetOffset(int nOffset) const
	{
		int i = (nOffset>=0) ? ((m_nR+nOffset)%m_nSize) : ((m_nW+m_nSize+nOffset)%m_nSize);
		return m_pData[i];
	}

	//B--判得到队列中相对队头/队尾指定偏移单元的单元值
	//  参数值：    Ele	    用于返回指定的单元内容
	//              nOffset	指定的偏移单元数（不要超过队长）
	//	注：当nOffset>=0时为相对队头向后偏移，特殊地：为0则返回队头单元
	//      否则          为相对队尾向前偏移，特殊地：为-1时返回最新的单元值
	//  返回参数：	true--操作有效，false--操作无效，指定队列单元为空
	inline bool GetOffset(ARG_TYPE& Ele, int nOffset) const
	{
	bool rs = false;
		if (nOffset>=0)
		{	
			if (m_nEleNum>nOffset)
			{
				Ele	= m_pData[(m_nR+nOffset)%m_nSize];	
				rs = true;
			}
		}
		else	//if(nOffset>=0)
		{
			if (m_nEleNum >= -nOffset)
			{
				Ele	= m_pData[(m_nW+m_nSize+nOffset)%m_nSize];	
				rs = true;
			}
		}
		return	rs;
	}

	//B--得到最新的有效单元指针（号），返回-1表示为空
	inline int GetPosLst()
	{
		if (m_nEleNum>0)
			return (m_nW+m_nSize-1)%m_nSize;
		else
			return -1;
	}

	//B--启动对队列中有效单元的遍历
	//  参数值： fstScanEle 用于返回指定的遍历起始单元内容
	//           nOffsetFst 指定的遍历起始单元的偏移单元数（不要超过队长）
	//	注：当nOffsetFst>=0时为相对队头向后偏移，特殊地：为0则返回队头单元
	//      否则          为相对队尾向前偏移，特殊地：为-1时返回最新的单元值
	//  返回参数：	!=-1时为fstScanEle单元指针--可以开始遍历，操作有效，fstScanEle中已返回指定的遍历起始单元值
	//              -1--操作无效，指定的遍历起始单元为空, 
	inline int ScanStart(ARG_TYPE& fstScanEle, int nOffsetFst = 0)
	{
	bool rs = GetOffset(fstScanEle, nOffsetFst);
		if (rs) 
			m_nScan = (nOffsetFst>=0) ? ((m_nR+nOffsetFst)%m_nSize) : ((m_nW+m_nSize+nOffsetFst)%m_nSize);
		else
			m_nScan = (m_nW+m_nSize-1)%m_nSize;	//防止再调用ScanNext时成功
		return (rs? m_nScan : -1);
	}

	//B--遍历队列中下一有效单元(在这之前要先调用ScanStart，并返回为非-1时才可用)
	//  参数值： nextScanEle用于返回遍历队列中下一有效单元内容
	//  返回参数：	!=-1时为nextScanEle单元指针, 操作有效，nextScanEle中已返回下一有效单元内容
	//              -1--操作无效，已遍历到队尾单元为空, 
	inline int ScanNext(ARG_TYPE& nextScanEle)
	{
	bool bNorEnd = true;
		if (++m_nScan >= m_nSize)	m_nScan = 0;
		if (m_nScan == m_nW)
		{
		//	m_nScan = (m_nW+m_nSize-1)%m_nSize;
			bNorEnd = false;
		}
		else
			nextScanEle = m_pData[m_nScan];
		return (bNorEnd? m_nScan : -1);
	}

	//B--将当前遍历队列单元前面（包括当前已遍历出的当前单元）扔出队(但出队后的单元内容未清）
	//-- 注意：该操作只能紧接着成功调用ScanStart或ScanNext时才能用！！
	//  返回参数：	0 --操作有效
	//              -1--操作无效（当前遍历队列单元不在队）
	inline int CleanToCurScanPos()
	{
		int iOutEleNum = (m_nScan + m_nSize - m_nR)%m_nSize + 1;								//TB050407.mod +1
		if (iOutEleNum > m_nEleNum) 
		{
			return -1;
		}
		else
		{
			m_nR = (m_nScan+1)%m_nSize;
			m_nEleNum -= iOutEleNum;
			return 0;
		}
	}
};
#endif // !defined(SDP_LOOPLST_H_INCLUDED_)
