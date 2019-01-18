import traceback

__all__ = ['global_par']
class global_par:
    """这是全局参数管理类,用于管理全局参数"""
    _my_global = {}
    _all_global = []
    @staticmethod
    def set_global_pars(pars,values):
        """
        set one pars
        :param pars: what global pars will set
        :param values: what values your set
        :return:  no value
        """
        try:
            if isinstance(pars,str) != 1:
                raise TypeError
            global_par._all_global.append(pars)
            global_par._my_global[pars] = values
        except Exception as e:
            traceback.print_exc()
            exit()
    @staticmethod
    def get_global_pars(pars):
        """
        get one para
        :param pars: what global pars will get
        :return:return this para values
        """
        try:
            if isinstance(pars, str) != 1:
                raise TypeError
            return global_par._my_global[pars]
        except KeyError as e:
            traceback.print_exc()
            print("no key in _my_global for {}".format(pars))
            exit()
        except Exception as e:
            traceback.print_exc()
            exit()
    @staticmethod
    def get_all_global_pars():
        """
        return a dict of all paras
        :return: return a dict of all paras
        """
        return global_par._my_global