"""
Route objects are to be defined as a collection of link objects that describe
the sequence of a previous or proposed vehicle trip.

These objects are the input to the energy rates model prediction methods.

Examples:
> from routee.roads.route import route
> from routee.roads.link import link
> 
> link1 = link(args)
> link2 = link(args)
> link3 = link(args)
> route1 = route(link1, link2, link3)
"""

import pandas as pd


class route:
    
    def __init__(self, attribute_dict):
        self.attribute_dict = attribute_dict
        self.keys = list(attribute_dict)
        self.df = pd.DataFrame.from_dict(self.attribute_dict)
        
        
    def __repr__(self):
        return '{}'.format(self.df)


class route_from_links:
    '''
    Route class takes input of Link objects
    '''
    
    def __init__(self, links, *args):
        self.links = [links.attribute_dict]
        for link in args:
            self.links.append(link.attribute_dict)
        self.df = pd.DataFrame(self.links)
    
    def __repr__(self):
        return '{}'.format(self.links)
 