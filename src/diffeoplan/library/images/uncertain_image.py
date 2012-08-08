from . import contract, np


class UncertainImage():
    
    @contract(values='array[HxWx...]', scalar_uncertainty='None|array[HxW]')
    def __init__(self, values, scalar_uncertainty=None):
        """ 
            To avoid errors later, the values are stored as float values.
            (If we use uint8, then taking differences might introduce
             strange effects.)
            
        """  
        self._values = values.astype('float32')
        self.scalar_uncertainty = scalar_uncertainty
    
    @contract(returns='array[HxW](float32)|array[HxWxN](float32)')
    def get_values(self):
        return self._values
        

    @staticmethod
    @contract(returns='dict(str:*)')
    def compute_all_distances(y0, y1):
        """ Computes all measures of difference between y0 and y1. 
            Returns a dictionary. """
        r = {}
        r['values_L2'] = UncertainImage.dist_values_L2(y0, y1)
        r['values_L1'] = UncertainImage.dist_values_L1(y0, y1)
        # add here
        return r
    
    @staticmethod
    def dist_values_L2(y0, y1):
        diff = (y0.get_values() - y1.get_values()).flatten()
        return float(np.linalg.norm(diff, 2)) #/ y0.size

    @staticmethod
    def dist_values_L1(y0, y1):
        diff = (y0.get_values() - y1.get_values()).flatten()
        return float(np.linalg.norm(diff, 1)) #/ y0.size

    # ADD here
    
