from obs import ObsClient
import logging
# 创建ObsClient实例

obsClient = ObsClient(
    access_key_id='BE390C0711468B860A3A',
    secret_access_key='meUcsfcnK6uJvnoW4gjHO+QJspYAAAFvEUaLh9/i',
    server='10.40.18.27:443'
)


def downloadFile(backname, objectName, filename):
    res = obsClient.getObject(backname, objectName, downloadPath=filename)
    if res.status < 300:
        logging.info("requestId", res.requestId)
        logging.info("url", res.body.url)
    else:
        logging.info('errorCode:', res.errorCode)
        logging.info('errorMessage:', res.errorMessage)


def uploadFile(backname, objectname):
    res = obsClient.putFile(backname, objectname, file_path=objectname)  # localfile为上传的本地文件路径，需要指定到具体的文件名
    if res.status < 300:
        logging.info('requestId:', res.requestId)
    else:
        logging.info('errorCode:', res.errorCode)
        logging.info('errorMessage:', res.errorMessage)


def listFile(backname):
    res = obsClient.listObjects(backname)
    if res.status < 300:
        index = 0
        # 遍历输出所有对象信息
        for content in res.body.contents:
            logging.info('content [' + str(index) + ']')
        # 输出该对象名
        logging.info('key:', content.key)
        # 输出该对象的最后修改时间
        logging.info('lastModified:', content.lastModified)
        # 输出该对象大小
        logging.info('size:', content.size)
        index += 1


if __name__ == '__main__':
    backname = "appdata"
    objectname = "/CMADAAS/APPDATA/DPL/CIPAS/"
    filename = ""
    uploadFile(backname, objectname)
