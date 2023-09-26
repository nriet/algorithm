import Ngl


def dict_to_object(obj, objMetaClass, params_dict):
    if (obj == None) or not isinstance(obj, objMetaClass):
        obj = objMetaClass()
    if params_dict:
        for key, value in params_dict.items():
            obj.__setattr__(key, value)
    return obj


def create_or_update_resource(resource=None, params_dict={}):
    return dict_to_object(resource, Ngl.Resources, params_dict)
