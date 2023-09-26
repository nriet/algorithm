from com.nriet.application.handler.Basehandler import BaseHandler

class IndexHandler(BaseHandler):

    def initialize(self):
        print("调用了initialize()")


    def prepare(self):
        print("调用了prepare()")


    def set_default_headers(self):
        print("调用了set_default_headers()")


    def write_error(self, status_code, **kwargs):
        print("调用了write_error()")

    def get(self):
        print("调用了get()")


    def post(self):
        print("调用了post()")

        self.send_error(200)  # 注意此出抛出了错误

    def on_finish(self):
        print("调用了on_finish()")