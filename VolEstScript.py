# importing os module
import os
import time
from tqdm import tqdm
import pandas as pd
import geopandas as gpd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import sqlalchemy as sql
from glob import glob
import os
import sys
import pickle
import datetime

sys.path.append('..')
pd.options.mode.chained_assignment = None

from routee.models.randomForest import randomForest
from routee.models.explicitBin import explicitBin

import warnings
warnings.filterwarnings('ignore')

font = {'family' : 'normal',
        'weight' : 'normal',
        'size'   : 18}
matplotlib.rc('font', **font)
# Command to execute
# Using Windows OS command



###############################
#         RUN RSCRIPTS        #
###############################
def retreive_tomtom_do_volume_estimate(Date):
    # cmd = "Rscript post_api.R " + Date   #runs a post requests to TomTom to prepare data
    # os.system(cmd)
    # for i in tqdm(range(t)):     #Takes a while for TomTom to prepare data so this is a automatic delay before we start continuously requesting the data
    #     time.sleep(1)
    #
    # print("We Waited long enough...here goes nothing")
    cmd =  "Rscript get_api.R " + Date #requests data till it's ready
    os.system(cmd)
    cmd = "export KMP_DUPLICATE_LIB_OK=TRUE"
    os.system(cmd)
    cmd = "Rscript input_data.R " + Date #cleans data and adds features
    os.system(cmd)
    cmd = "python estimate_volume.py " + Date #uses model weights to estimate link-wise volume estimates
    os.system(cmd)
    # cmd = "Rscript visualize.R " + Date + " 1 8 11 17 23"
    # os.system(cmd)

################################
#        MAP MATCHING          #
################################
def read_in_files(Date):
    pred_path = Date + '/daily_data_pred.csv'
    volume = pd.read_csv(pred_path)

    lookupTable = pd.read_csv("2020_TomTom_TPO.csv")
    lookupTable.drop(columns=['Unnamed: 0'], inplace=True)
    return lookupTable, volume

def flattenDataFrame(volume):
    tmp = volume.pivot(index='Id', columns='HOUR', values=['AvgSp', 'pred_volume'])
    volume_flat = pd.DataFrame()

    for t in tqdm(tmp['AvgSp'].columns.tolist()):
        volume_flat['speed_' + str(int(t))] = tmp['AvgSp'][t]
        volume_flat['volume_' + str(int(t))] = tmp['pred_volume'][t]
    volume_flat['TomTomId'] = tmp.index
    return volume_flat

def mergeVolAndSumo(df,volume_flat):
    df_merged = df.merge(volume_flat, left_on='tomId', right_on='Id')
    df_merged.drop(columns=['tomId'],inplace=True)
    return df_merged
def map_match():
    lookupTable, volume = read_in_files(Date)
    volume_flat = flattenDataFrame(volume)
    merged_df= mergeVolAndSumo(lookupTable,volume_flat)
    return merged_df

###################################
#          ROUTE-E ENERGY         #
###################################

def read_speed_volume_process(speed_vol_df):
    speed_vol_AB_df = speed_vol_df[speed_vol_df['sumoId'] >= 0.0]
    speed_vol_BA_df = speed_vol_df[speed_vol_df['sumoId'] < 0.0]
    speed_vol_BA_df['sumoId'] = speed_vol_BA_df['sumoId'] * (-1)
    return speed_vol_AB_df,speed_vol_BA_df

def update_colnames(df, direction):
    for colname in df.filter(regex='volume|speed').columns:
        tmp = colname.split('_')
        if len(tmp) > 1:
            updated_colname = tmp[0] + '_' + direction + '_' + tmp[1]
        else:
            updated_colname = tmp[0] + '_' + direction
        df.rename(columns = {colname:updated_colname}, inplace = True)
    return df
# def update_AB_BA():
#     speed_vol_AB_df = update_colnames(speed_vol_AB_df, 'AB')
#     speed_vol_BA_df = update_colnames(speed_vol_BA_df, 'BA')

def import_vehicle_models():
    explicitbin_in = explicitBin('Vehicle_Models/gasoline_conv_Volkswagen_Tiguan_36000_explicitbin')
    explicitbin_in.read_model('Vehicle_Models/gasoline_conv_Volkswagen_Tiguan_36000_explicitbin.pkl')
    return explicitbin_in

def merge_net_speed_vol(speed_vol_AB_df,speed_vol_BA_df):
    net_merged_AB = pd.merge(left=net, right=speed_vol_AB_df, how='left', left_on='ID', right_on='sumoId')
    net_merged_AB = net_merged_AB.drop('sumoId',axis=1)
    net_merged_speed_vol = pd.merge(left=net_merged_AB, right=speed_vol_BA_df, how='left', left_on='ID',right_on='sumoId')
    return net_merged_speed_vol
def extract_extra_links(net):
    net = net[net['ROAD_FLAG'] != 1300] #parking malls
    net = net[net['ROAD_FLAG'] != 1100] #centroid connectors
    net = net[net['ROAD_FLAG'] != 1200] #walk
    net = net[net['ROAD_FLAG'] != 1000] #Split for Centroid Connector
    net = net[net['ROAD_FLAG'] != 900] #network additions
    return net

def build_energy_estimate(net_merged_speed_vol,Date):
    # results_spvol_drc = {}
    #
    # net_merged_speed_vol[['AB_LANES','BA_LANES']] = net_merged_speed_vol[['AB_LANES','BA_LANES']].fillna(0)
    # for drc in ['AB', 'BA']:
    #
    #     for hour_of_day in tqdm(range(24)):
    #         net_selected = net_merged_speed_vol[net_merged_speed_vol[drc + '_LANES'] > 0]
    #         net_selected['volume'] = net_selected['volume_' + drc + '_' + str(hour_of_day)]
    #         net_selected['speed_mph_float'] = net_selected['speed_' + drc + '_' + str(hour_of_day)].astype(float)
    #         net_selected['grade_percent_float'] = net_selected[drc + '_grade_p'].astype(float)
    #         net_selected['num_lanes_int'] = net_selected[drc + '_LANES'].astype(int)
    #         net_selected['miles'] = net_selected['Length'].astype(float)
    #         net_selected['energy'] = 0.0
    #         net_selected['energy_density'] = 0.0
    #         cols = ['speed_mph_float', 'grade_percent_float', 'num_lanes_int','miles']
    #         net_selected['energy'] = explicitbin_in.predict(net_selected[cols])
    #         net_selected['energy_density'] = net_selected['energy'] * net_selected['volume']
    #         net_selected['energy_per_meter'] = net_selected['energy']/(net_selected['miles'] * 1609.344)
    #         net_selected['energy_density_per_meter'] = net_selected['energy_per_meter'] * net_selected['volume']
    #         net_selected['energy_per_meter_per_lane'] = (net_selected['energy']/(net_selected['miles'] * 1609.344))/net_selected['num_lanes_int'].astype(float)
    #         net_selected['energy_density_per_meter_per_lane'] = net_selected['energy_per_meter_per_lane'] * net_selected['volume']
    #         net_selected['energy_per_meter_per_lane_grade_adj'] = net_selected['energy_per_meter_per_lane']/(net_selected['grade_percent_float']/100.0)
    #         net_selected['energy_density_per_meter_per_lane_grade_adj'] = net_selected['energy_per_meter_per_lane_grade_adj'] * net_selected['volume']
    #
    #         results_spvol_drc[drc + "_" + str(hour_of_day)] = net_selected['energy_density'].sum()
    # return results_spvol_drc
    net_merged_speed_vol = extract_extra_links(net_merged_speed_vol)
    results_spvol_drc = {}

    net_merged_speed_vol[['AB_LANES','BA_LANES']] = net_merged_speed_vol[['AB_LANES','BA_LANES']].fillna(0)
    AB_net = gpd.GeoDataFrame()
    BA_net = gpd.GeoDataFrame()
    for drc in ['AB', 'BA']:

        for hour_of_day in range(24):
            net_selected = net_merged_speed_vol[net_merged_speed_vol[drc + '_LANES'] > 0]
            net_selected['volume'] = net_selected['volume_' + drc + '_' + str(hour_of_day)]
            net_selected['speed_mph_float'] = net_selected['speed_' + drc + '_' + str(hour_of_day)].astype(float)
            net_selected['grade_percent_float'] = net_selected[drc + '_grade_p'].astype(float)
            net_selected['num_lanes_int'] = net_selected[drc + '_LANES'].astype(int)
            net_selected['miles'] = net_selected['Length'].astype(float)
            net_selected['energy'] = 0.0
            net_selected['energy_density'] = 0.0
            cols = ['speed_mph_float', 'grade_percent_float', 'num_lanes_int','miles']
            net_selected['energy'] = explicitbin_in.predict(net_selected[cols])
            net_selected['energy_density'] = net_selected['energy'] * net_selected['volume']
            net_selected['energy_per_mile'] = net_selected['energy']/(net_selected['miles'])
            net_selected['energy_density_per_mile'] = net_selected['energy_per_mile'] * net_selected['volume']
            net_selected['energy_per_mile_per_lane'] = (net_selected['energy']/(net_selected['miles'] ))/net_selected['num_lanes_int'].astype(float)
            net_selected['energy_density_per_mile_per_lane'] = net_selected['energy_per_mile_per_lane'] * net_selected['volume']
            net_selected['energy_per_mile_per_lane_grade_adj'] = net_selected['energy_per_mile_per_lane']/(net_selected['grade_percent_float']/100.0)
            net_selected['energy_density_per_mile_per_lane_grade_adj'] = net_selected['energy_per_mile_per_lane_grade_adj'] * net_selected['volume']
            columns = ['ID','volume','speed_mph_float','miles','energy','energy_per_mile','grade_percent_float','num_lanes_int','geometry']
            results_spvol_drc[drc + "_" + str(hour_of_day)] = net_selected[columns].copy()
            file_name = "%s_%s_%s.geojson" % (Date,hour_of_day,drc)
            folder = "EnergyData"
            net_selected[columns].to_file(os.path.join(folder,file_name),driver='GeoJSON')
            # pickle.dump( net_selected, open( os.path.join(folder,file_name), "wb" ) )

            # tmp = net_selected[['energy_density_per_meter','speed_mph_float','volume','ID','geometry']].copy()
            # DateArray = Date.split("-")
            # year = DateArray[0]
            # monthInteger = int(DateArray[1])
            # month = datetime.date(1900, monthInteger, 1).strftime('%B')
            # day = DateArray[2]
            # hour = str(hour_of_day)
            # fileExtension = ".geojson"
            # filename = "_".join([month,day,year,hour,drc,fileExtension])
            # folder = "EnergyData"
            # path = os.path.join(folder,filename)
            # print(path)
            # tmp.to_file(path,driver='GeoJSON')

    # energy_volume_speed_columns = []
    # for col in results_spvol_drc['AB_0'].columns:
    #     if col.startswith("energy"):
    #
    #         energy_volume_speed_columns.append(col)
    # base_columns  = ['ID','geometry']
    # exclude = ['volume']
    # for col in results_spvol_drc['AB_0'].columns:
    #     if col.startswith("speed") or col.startswith("volume") and (col not in exclude):
    #         base_columns.append(col)
    # base_columns.remove('speed_mph_float')
    # energy_volume_speed_columns = ['energy_density']
    # base_df = net_merged_speed_vol[base_columns]
    #
    # for key in ['AB','BA']:
    #
    #     for hour_of_day in range(24):
    #         df_name = key + '_' + str(hour_of_day)
    #         new_column_name = 'E_'+ df_name
    #         tmp_df = pd.DataFrame()
    #         tmp_df = results_spvol_drc[df_name][['energy_density','ID']]
    #         tmp_df.rename(columns={'energy_density': new_column_name},inplace=True)
    #         base_df = base_df.merge(tmp_df,on='ID')
    #         print(base_df.shape)
    # base_df.to_file("network_energy.geojson", driver='GeoJSON')
    # file_name = Date + "_energy.geojson"
    # folder = "EnergyData"
    # print("saving energy file to: ",file_name)
    # AB_net.to_file(os.path.join(folder,file_name),driver='GeoJSON')
    # # pickle.dump( AB_net, open( os.path.join(folder,file_name), "wb" ) )

def deleteFiles(Date):
    cmd = "rm " + Date + "/" + Date + "*"
    os.system(cmd)
    cmd = "rm " + Date + "/*.html"
    os.system(cmd)
    # cmd = "rm " + Date + "/network*"
    # os.system(cmd)
    cmd = "rm " + Date + "/*.txt"
    os.system(cmd)

if __name__=="__main__":

    ##############################
    #    SET Global Variables    #
    ##############################


    t = 60 * 60  # This is the seconds to wait till we can call back print_function
    # Date = "2020-02-18"
    Date = sys.argv[1]
    # print(Date)
    # retreive_tomtom_do_volume_estimate(Date)
    merged_df = map_match()
    speed_vol_AB_df,speed_vol_BA_df = read_speed_volume_process(merged_df)
    speed_vol_AB_df = update_colnames(speed_vol_AB_df, 'AB')
    speed_vol_BA_df = update_colnames(speed_vol_BA_df, 'BA')

    explicitbin_in = import_vehicle_models()
    net = gpd.read_file("Network/network_with_grade.shp")
    net_merged_speed_vol = merge_net_speed_vol(speed_vol_AB_df,speed_vol_BA_df)
    # print(net_merged_speed_vol.columns.tolist())
    build_energy_estimate(net_merged_speed_vol,Date)
    deleteFiles(Date)
    cmd = 'echo "Done!!!"'
    os.system(cmd)
