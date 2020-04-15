
"""
Link objects are the functional unit of road information in routeE

Each link object contains a set of features (attributes) along the link and 
will have an energy prediction appended to it in the rates prediction methods

These objects can be used to build route objects, or can be input directly to
the rates prediction methods

Examples:
> from routee.roads.link import link
> 
> link1 = link(args)
> link2 = link(args)
> link3 = link(args)
"""

import pandas as pd 

class link:
    """Object describing a link as a combination of features/attributes.
    """
        
    def __init__(self, attribute_dict):
        
        """
        Accepts input of dictionary object
        Example:
        dataset = [{a : 1, b: 2, c: 3}, {d : 4, e : 5, f : 6}]
        link1 = Link(dataset[0])
        
        In:
        print(link1.attribute_dict)
        
        Out: 
        {a : 1, b: 2, c: 3}
        
        """
        self.attribute_dict = attribute_dict
        self.keys = list(attribute_dict)
        self.values = list(attribute_dict.values())
        self.df = pd.DataFrame.from_dict(self.attribute_dict, orient ='index')
        self.size = len(attribute_dict)
        
    def __repr__(self):
        return '{}'.format(self.attribute_dict)





    ## TODO: move link.lookup() to model.predict() method
    def lookup(self, rates):
        """Lookup energy rates by feature combination of link object.

        Aprintrgs:
            rates: (obj) object describing energy consumption rate by
                feature combination

        Returns:
            link object with an energy consumption variable

        """
        df_tmp = rates.df

        # Downselect rates table to the link combination value
        for ft in self.features:
            df_tmp = df_tmp[df_tmp[ft] == self.attrb_dict[ft]]
        e_rate = float(df_tmp.fuel_rate_gal100mi)/100.0 # gal/mi

        self.energy_pred = e_rate * self.distance

        return self.energy_pred