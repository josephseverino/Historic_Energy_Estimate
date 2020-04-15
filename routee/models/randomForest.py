
"""
The energy rates models are trained and used to predict energy consumption 
on link and route objects

This model uses a random forest to select an optimal decision tree, 
meant to serve as an automated construction of a lookup table

Examples:
> from routee.dtree_model.rates import dtree
> from routee.roads.route import route
> from routee.roads.link import link
> 
> link1 = link(args)
> link2 = link(args)
> link3 = link(args)
> route1 = route(link1, link2, link3)
>
> emodel = dtree()
> emodel.train(fc_data) # fc_data = link attributes + fuel consumption
> emodel.predict(route1)
[returns route1 with energy appended to each link]
"""

import pandas as pd 
import numpy as np

from ..validation import errors
from routee.models import predict_model

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV

# from sklearn2pmml import PMMLPipeline


class randomForest(predict_model.parent):
    """Random Forest Regressor for energy consumption prediction.
    
    Class must be initialized with a vehicle description, i.e.:
    
    > randomForest('2016 Ford Explorer', 4)
    """
    
    def __init__(self, veh_desc, cores):
        """Initialization descrides the vehicle that the model
        will train on.
        
        Args:
            veh_desc: (str) recommended that this should include
            year, make, model, and any relevant trim options
            
            cores: (int) number of jobs to run in parallel for training
            the random forest regressor, enter -1 to use all available
            CPUs
        """
        self.veh_desc = veh_desc
        self.attrb_dict = {}
        self.cores = cores

    def train_helper(self):
        """Override parent train_helper method.
        """
        
        # Number of trees in random forest
        n_estimators = [int(x) for x in np.linspace(start = 50, stop = 1000, num = 10)]
        # Maximum number of levels in tree
        max_depth = [int(x) for x in np.linspace(10, 110, num = 11)]
        max_depth.append(None)
        # Minimum number of samples required to split a node
        min_samples_split = [2, 5, 10]
        # Minimum number of samples required at each leaf node
        min_samples_leaf = [1, 2, 4]
        # Create the random grid
        random_grid = {'n_estimators': n_estimators,
                       'max_depth': max_depth,
                       'min_samples_split': min_samples_split,
                       'min_samples_leaf': min_samples_leaf}


        # train Random Forest
        regmod = RandomForestRegressor(n_estimators=20,
                                       max_features='auto',
                                       max_depth=10,
                                       min_samples_split=10,
                                       n_jobs=self.cores,
                                       random_state=52)
        
        # print(self.features)
        self.model = regmod.fit(self.train[self.features], 
                                self.train['rate'])

############################################################
#         # Random Search CV -- Did not yield improvement
#         regmod = RandomForestRegressor()
        
#         regmod_random = RandomizedSearchCV(estimator = regmod, param_distributions = random_grid, n_iter = 10, cv = 3, verbose=2, random_state=42, n_jobs = -1)
        
#         # Fit the random search model
#         regmod_random.fit(self.train[self.features], self.train['rate'])

#         self.model = regmod_random.best_estimator_
        
        # test model performance
############################################################

        self.test = self.test.reset_index(drop=True)
        self.test['rate_pred'] = pd.Series(self.model.predict(self.test[self.features]))

        self = errors.all_error(self)

        return self