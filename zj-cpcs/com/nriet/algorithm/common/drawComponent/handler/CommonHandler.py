from abc import ABCMeta, abstractmethod


class CommonHandler:

    def __init__(self
                 , workstation
                 , plot
                 , input_data=None
                 , resource=None
                 , params_dict=None
                 ):
        '''
        :param workstation:
        :param plot:
        :param input_data:
        :param resource:
        :param params_dict:
        '''
        self.workstation = workstation
        self.plot = plot
        self.input_data = input_data
        self.resource = resource
        self.params_dict = params_dict

    def draw(self):
        pass
