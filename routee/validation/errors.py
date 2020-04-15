"""
Errors submodule contains the standard functions for calculating errors
on model classes after training.

Each function expects particular variables and column names within the model
classes.

Args:
    model: (model class), 'test' dataframe in model must have columns
            ['rate', energy, 'rate_pred', trip_ids]

Returns:
    model: Energy model class with error variables
"""


def calc_predicted_energy(df, distance):
    """Convert energy rate + distance to energy consumption
    """
    df['energy_pred'] = (df['rate_pred']/100.0)*df[distance]
    return df

def link_average_error_unweight(df,energy):
    """Calculate the median error on links without weighting 
    by distance or energy consumption
    """
    rate_error = (df[energy] - df.energy_pred)/df[energy]
    lae_uw = rate_error.abs().median()
    return lae_uw

def trip_average_error_weight(df,energy,trip_ids):
    """Calculate the median error on links without weighting 
    by distance or energy consumption
    """
    trips_df = df.groupby(trip_ids).agg({energy:sum, 'energy_pred':sum})
    rate_error = (trips_df[energy]/trips_df[energy].sum())*abs(trips_df[energy] - trips_df.energy_pred)/trips_df[energy]
    tae_w = rate_error.sum()
    return tae_w

def net_energy_error(df,energy):
    """Calculate the net energy prediction error over all 
    links in the test dataset
    """
    net_e = df[energy].sum()
    net_e_pred = df['energy_pred'].sum()
    net_error = (net_e_pred - net_e)/net_e
    return net_error


def all_error(model):
    # Predicted Energy Consumption
    model.test = calc_predicted_energy(model.test, model.distance)
    
    # Link average error - unweighted
    model.link_average_error_unweight = link_average_error_unweight(model.test,
                                                                    model.energy)
    
    # Link average error - weighted
    model.trip_average_error_weight = trip_average_error_weight(model.test,
                                                                model.energy,
                                                                model.trip_ids)
    
    # Net energy error
    model.net_error = net_energy_error(model.test, model.energy)

    return model