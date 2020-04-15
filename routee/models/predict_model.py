import pandas as pd 
import numpy as np
import pickle

from ..validation import errors

from sklearn.model_selection import train_test_split
from sklearn import linear_model


def test_train_split(df, test_perc):
    msk = np.random.rand(len(df)) < (1-test_perc)
    train = df[msk]
    test = df[~msk]
    return train, test

class parent:
    """
    The prediction models are trained and used to predict energy consumption 
    on link and route objects.

    This module is the parent prediction model, from which each
    child model inherits main functionality.

    The parent class can also be used directly as a linear regression model.

    Child inheritance example:
    ==========================
    import predict_model

    class randomForest(predict_model.parent):
        pass

    """

    def __init__(self, veh_desc):
        """
        """
        self.veh_desc = veh_desc

    def train(self, fc_data, energy, distance, trip_ids):
        """Train an energy consumption model based on energy use data

        Args:
            fc_data: (dataframe) link level energy consumption information
            and associated link attributes

            energy: (str) name/units of the target energy consumption column

            distance: (str) name/units of the distance column

        Returns:
            self: Energy model object
        
        """

        # Assign input df to class variable
        self.pass_data = fc_data.copy()

        # identify feature, target, and distance columns
        self.features = [x for x in list(fc_data.columns) \
                            if x not in [energy,distance,trip_ids]]
        self.energy = energy
        self.distance = distance
        self.trip_ids = trip_ids
        self.pass_data['rate'] = 100.0*self.pass_data[self.energy]/\
                                self.pass_data[self.distance]   

        # test, train, validate split
        self.train, self.test = test_train_split(self.pass_data.dropna(), 0.2)
        self.test, self.validate = test_train_split(self.test, 0.5)
        self.y_train, self.y_test = self.train, self.test
        self.y_test, self.y_validate = self.test, self.validate
        
        return self.train_helper()

    def train_helper(self):
        """Helper method contains steps that will likely be overridden
        in child classes.
        """

        # train model
        regmod = linear_model.LinearRegression()
        self.model = regmod.fit(self.train[self.features], 
                                self.train['rate'])

        # test model performance
        self.test = self.test.reset_index(drop=True)
        self.test['rate_pred'] = pd.Series(self.model.predict(self.test[self.features]))

        self = errors.all_error(self)

        return self


    def predict(self, links_df):
        """Apply the trained energy model to to predict consumption

        Args:
            links_df: (DataFrame) columns that match self.features and self.distance
            that describe vehicle passes over links in the road network

        Returns:
            output: predicted energy consumption for every row in links_df
        """
        
        output = self.predict_helper(links_df)
        
        return output
        
    def predict_helper(self, links_df):
        """Helper method for the predict method, steps will be overridden
        depending on what type of model is trained in the child class.
        Apply the trained energy model to to predict consumption

        Args:
            links_df: (DataFrame) columns that match self.features and self.distance
            that describe vehicle passes over links in the road network

        Returns:
            energy_pred: predicted energy consumption for every row in links_df
        
        """
        
        cols_model = [x for x in list(links_df.columns) if x not in [self.distance]]
        
        links_df.loc[:,'rate'] = self.model.predict(links_df[cols_model])
        
        energy_pred = (links_df['rate']/\
                                 100.0)*links_df[self.distance]

        return energy_pred
    
    def dump_model(self, fileout):
        """This method is used to dump a trained model and the necessary metadata
        to the catalog of pre-trained models, or a specified user location.
        
        Args:
            fileout: (str) full path and name of the (pickle) file to which the 
            model object will be written. If file exists, it is overwritten.
        """
        out_obj = parent(self.veh_desc)
        out_obj.model = self.model
        out_obj.energy = self.energy
        out_obj.distance = self.distance
        out_obj.features = self.features
        out_obj.link_err = self.link_average_error_unweight
        out_obj.trip_err = self.trip_average_error_weight
        out_obj.net_err = self.net_error
        out_obj.attrb_dict = self.attrb_dict
        
        pickle.dump(out_obj, open(fileout,'wb'))
        
        
    def read_model(self, filein):
        """This method is used to read a trained model and the necessary metadata
        from the catalog of pre-trained models, or a specified user location. 
        Pickling custom objects causes unexpected class inheritence behavior (upon
        loading the model is seen as parent class not child). This method is a 
        workaround.
        
        Args:
            filein: (str) full path and name of the (pickle) file from which the model
            object will be loaded.
        """
        in_obj = pickle.load(open(filein,'rb'))
        self.model = in_obj.model
        self.energy = in_obj.energy
        self.distance = in_obj.distance
        self.features = in_obj.features
        self.link_err = in_obj.link_err
        self.trip_err = in_obj.trip_err
        self.net_err = in_obj.net_err
        self.attrb_dict = in_obj.attrb_dict
        