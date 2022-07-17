from taoics.tardys import config,config_mysql

class Common():
    def __init__(self):
        self.name = "det"
        self.mysql = config_mysql(self.name)

    def _select_status_values(self, keys):
        vals = [self.mysql.select_status(where={"NAME": key}) for key in keys] 
        return vals

    def select_status_values(self, keys):
        """
        Args:
            keys(list) : list of parameters you want
        Returns:
            vals(list) : list of parameter value
        """

        vals = [self.mysql.select_status(where={"NAME": key}) for key in keys] 
        print(vals)    
        vals = [val[0]["value"] for val in vals]
        return vals

    def select_status_dict(self, keys):
        """
        Args:
            keys(list) : list of parameters you want
        Returns:
            vals(dict) : {param1 : param_value1, param2 : param_value2, ... }
        """   

        vals = [self.mysql.select_status(where={"NAME": key}) for key in keys]   
        print(vals)  
        dic = {val[0]["name"]:val[0]["value"] for val in vals}
        return dic

    def true_or_false(self, string):
        if string.lower() == "true":
            return True
        elif string.lower() == "false":
            return False
        else:
            raise ValueError("INVARID INPUT")