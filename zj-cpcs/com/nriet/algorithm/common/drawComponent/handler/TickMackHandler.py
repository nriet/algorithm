import os
import time
import logging
import Ngl
from com.nriet.algorithm.common.drawComponent.handler.CommonHandler import CommonHandler
from com.nriet.utils.ResourcesUtils import create_or_update_resource


class TickMackHandler(CommonHandler):
    def __init__(self, workstation, plot, params_dict, tmp_service):
        super().__init__(workstation, plot, params_dict=params_dict)
        self.tmp_service = tmp_service

    def add_map_tickmarks(self):
        start_time = time.time()

        params_dict = self.params_dict
        tm_resource = create_or_update_resource(params_dict=params_dict)

        # �̻������Ტ���ӵ�ԭʼmap_plot��
        tm_plot = Ngl.blank_plot(self.workstation, tm_resource)
        sres = Ngl.Resources()
        sres.amZone = 0
        sres.amResizeNotify = True

        plot = Ngl.add_annotation(self.plot, tm_plot, sres)
        stop_time = time.time()
        cost = stop_time - start_time
        logging.info("             %s cost %s second" % (os.path.basename(__file__), cost))

        return plot
