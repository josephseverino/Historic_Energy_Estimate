
"""
The energy rates models are trained and used to predict energy consumption 
on link and route objects.

There can be many model types including explicit feature binning, automatic
feature binning, regression models, and more complex machine learning approaches.

This module defines the explicitBin class which allows users to specify precisely
which features to aggregate the data on and set the bin limits to discretize
the data in each feature (dimension).

Example application:
====================
> from routee.models.explicitBin import explicitBin
>
> model_eb = explicitBin('2016 Ford Explorer')
> model_eb.attrb_dict = {'speed_mph_float':[1,10,20,30,40,50,60,70,80],
>                      'grade_percent_float':[-5,-4,-3,-2,-1,0,1,2,3,4,5],
>                      'num_lanes_int':[0,1,2,3,4,10]}
>
> model_eb.train(fc_data, # fc_data = link attributes + fuel consumption
>               energy='gallons', 
>               distance='miles', 
>               trip_ids='trip_ids') 
>
> model_eb.predict(route1) # returns route1 with energy appended to each link
"""

import pandas as pd 
import numpy as np
import copy
from ..validation import errors
from routee.models import predict_model

class explicitBin(predict_model.parent):
    """Energy consumption rates matrix with same dimensions as link features.
    
    Class must be initialized with a vehicle description, i.e.:
    
    > explicitBin('2016 Ford Explorer')
    """

    def train_helper(self):
        """Override parent train_helper method.
        """

        # identify attribute and target (energy consumption) columns
        self.features = list(self.attrb_dict.keys())

        # Cut and label each attribute - manual        
        for f_i in self.features:
            bin_lims = self.attrb_dict[f_i]
            self.train.loc[:,f_i+'_bins'] = pd.cut(self.train[f_i], bin_lims)
            self.test.loc[:,f_i+'_bins'] = pd.cut(self.test[f_i], bin_lims)


        # train rates table - groupby bin columns
        bin_cols = [i+'_bins' for i in self.features]
        agg_funs = {self.distance:sum, self.energy:sum}

        self.model = self.train.dropna(subset=bin_cols).\
                        groupby(bin_cols).agg(agg_funs)
        
        # rate is dependent on the energy and distance units provided (*100)
        self.model.loc[:,'rate'] = 100.0*self.model[self.energy]/\
                                self.model[self.distance]

        # test rates table performance on self.test holdout
        ## merge energy rates from grouped table to self.test
        self.test = pd.merge(self.test, self.model[['rate']], \
                            how='left', left_on = bin_cols, right_index=True,\
                            suffixes=('','_pred'))

        self.test.dropna(how='any',inplace=True)

        self = errors.all_error(self)

        return self


    def predict_helper(self, link_df):
        """Apply the trained energy model to to predict consumption

        Args:
            road_obj: (object) link or route objects on which energy 
            prediction is desired

        Returns:
            road_obj: the link or route object is returned with energy 
            prediction as an added variable
        """
        # Cut and label each attribute - manual        
        for f_i in self.features:
            bin_lims = self.attrb_dict[f_i]
            link_df.loc[:,f_i+'_bins'] = pd.cut(link_df[f_i], bin_lims)

        # merge energy rates from grouped table to link/route df
        bin_cols = [i+'_bins' for i in self.features] 
        link_df = pd.merge(link_df, self.model[['rate']], \
                            how='left', left_on = bin_cols, right_index=True)

        link_df.dropna(how='any',inplace=True)

        # calculate predicted energy use from merged energy rates
        energy_pred = (link_df['rate']/\
                                 100.0)*link_df[self.distance]

        return energy_pred
    
    def dump_csv(self, fileout):
        """Dump CSV file of table ONLY. No associated metadata.

        Args:
            fileout: (str) path and filename of dumped CSV

        Returns:
            CSV file in specified location
        """
        
        self.model = self.model.reset_index()
        self.model.to_csv(fileout, index=False)
        
    def cavs_mapper(self, auxLoad=0, speedCol='speed_mph_float_bins', caccEquip=True):
        """Map the trained routeE model from that of human driven
        vehicles to vehicles with connected automated vehicle (CAV) 
        technologies.
        
        Args:
            auxLoad: (float) this is the additional auxilary due to electrical
            demand from the required hardware/sensing devices for CAV technology
            in units of kilowatts
            
            speedCol: (str) the name of the vehicle speed bin in the model
            
            caccEquip: (boolean true/false) indicator of whether or not the vehicle
            is equipped with connected addaptive cruise control (CACC) technology. If 
            yes, an energy benefit at low speeds due to drive cycle smoothing is also 
            taken into account.
            
        Returns:
            self.cavs_model: the mapped model describing energy consuption for
            the same vehicle with automated technolgies is returned.
        
        """
        
        # clone the routeE object
        cavs_model = copy.deepcopy(self)
        
        cavs_model.model = pd.DataFrame()
        
        # set energy variables
        
        caccBenefit = 0 # set to 0 for now because microsim is only hwy
        
        kwh_to_gge = 1/33.4
    
        for index, row in self.model.reset_index().iterrows():
            
            avgSpd = row[speedCol].mid #index[0].mid
            
            kwh100mi_add = 100.0*(auxLoad/avgSpd)
            
            rate_add = kwh100mi_add
            
            if self.energy == 'gallons':
                
                gal100mi_add = kwh100mi_add*kwh_to_gge
                
                rate_add = gal100mi_add
                
            row.rate = row.rate + rate_add
            
            cavs_model.model = cavs_model.model.append(row, ignore_index=True)
            
        feat_lst = [feat+'_bins' for feat in cavs_model.features]
        
        # idx_names = [col for col in list(cavs_model.model.columns) if col not in feat_lst]
            
        cavs_model.model = cavs_model.model.groupby(by=feat_lst).agg({'rate':'first'})
                                                                             
        return cavs_model