library(randomForest)
library(plyr)
library(sqldf)
library(lubridate)
library(doParallel)
library(ggplot2)
library(reshape2)
library(httr)
library(jsonlite)
library(zoo)
library(AtmRay)
library(data.table)
library(htmlwidgets)
library(mapview)
library(rgdal)
library(foreign)
registerDoParallel(cores=8) 
set_config(config(ssl_verifypeer = 0L))

args = commandArgs(trailingOnly=TRUE)
query_date = args[1] # Date format: "yyyy-mm-dd"
week_day = weekdays(as.Date(query_date))

# Read TomTom network
network = readOGR(dsn = paste0('./', query_date), layer = 'network', stringsAsFactors = F)
network = subset(network, FRC<=6)
network_df = network@data
coords = foreach(i = 1:length(network), .combine = rbind) %dopar% {
  network@lines[[1]]@Lines[[1]]@coords[1,]
}
network_df$LONGITUDE = coords[, 1]
network_df$LATITUDE = coords[, 2]
saveRDS(network, paste0(query_date, '/network.rds'))

# Obtain daily data
filenames = list.files(paste0('./', query_date, '/'))
daily_data = data.frame(Id=integer(),
                        AvgSp=numeric(), 
                        count=integer(),
                        HOUR=integer())
for(file in filenames){
  if(grepl(query_date, file)){
    data = read.dbf(paste0("./", query_date, "/", file))
    data = data[, c(1,5,9)]
    names(data)= c("Id", "AvgSp", "count")
    data$HOUR = as.integer(unlist(strsplit(file, "\\-|\\_"))[4])
    daily_data = rbind(daily_data, data)
  }
}

id_hour = meshgrid(network$Id, 0:23)
dim(id_hour$x) = c(length(network$Id)*24, 1)
dim(id_hour$y) = c(length(network$Id)*24, 1)
id_hour = data.frame(Id = id_hour$x, HOUR = id_hour$y)

daily_data = sqldf('select id_hour.*, daily_data."AvgSp", daily_data.count
                    from id_hour left join daily_data
                    on daily_data."Id" = id_hour."Id" and daily_data."HOUR" = id_hour."HOUR"')

daily_data = sqldf('select daily_data.*, network_df."SpeedLimit" as speed_limit, network_df."FRC" as frc, network_df."LONGITUDE", network_df."LATITUDE" 
                   from daily_data left join network_df
                   on daily_data."Id" = network_df."Id"')
daily_data[['DAYOFWEEK_Friday']] = ifelse(week_day == 'Friday', 1, 0)
daily_data[['DAYOFWEEK_Monday']] = ifelse(week_day == 'Monday', 1, 0)
daily_data[['DAYOFWEEK_Thursday']] = ifelse(week_day == 'Thursday', 1, 0)
daily_data[['DAYOFWEEK_Tuesday']] = ifelse(week_day == 'Tuesday', 1, 0)
daily_data[['DAYOFWEEK_Wednesday']] = ifelse(week_day == 'Wednesday', 1, 0)

# Join weather info with volume data
get_weather = function(lat, long, startdate, enddate){
  r = GET(
    "http://cleanedobservations.wsi.com/CleanedObs.svc/GetObs?",
    query = list(version = 2, lat=lat, long=long, startDate=startdate, endDate=enddate, interval='hourly', time='lwt',
                 units='imperial', format='json', fields='surfaceTemperatureFahrenheit,precipitationPreviousHourInches,snowfallInches,windSpeedMph', 
                 delivery='stream', userKey='df91579241f6569da3efe52187f6991e')
  )
  weather = fromJSON(content(r, "text", encoding = "UTF-8"))$weatherData$hourly$hours
  return(weather)
}
weather = get_weather(35.043831, -85.308608, format(as.Date(query_date), "%m/%d/%Y"), format(as.Date(query_date)+1, "%m/%d/%Y"))
weather$dateHrLwt = strptime(weather$dateHrLwt, '%m/%d/%Y %H:%M:%S', tz = 'EST')
weather$DATE = date(weather$dateHrLwt)
weather$HOUR = hour(weather$dateHrLwt)
weather$dateHrLwt = NULL

daily_data = sqldf('select weather."surfaceTemperatureFahrenheit" as temp, weather."windSpeedMph" as wind, weather."precipitationPreviousHourInches" as precip, weather."snowfallInches" as snow, daily_data.*  
                      from daily_data left join weather 
                      on daily_data."HOUR" = weather."HOUR"')
daily_data$temp = na.locf(daily_data$temp)
daily_data$precip = na.locf(daily_data$precip)
daily_data$wind = na.locf(daily_data$wind)
daily_data$snow = na.locf(daily_data$snow)

# Output daily data
daily_data$count[is.na(daily_data$count)] = 0
daily_data$AvgSp[daily_data$count==0] = daily_data$speed_limit[daily_data$count==0]
daily_data = daily_data[, c('Id', 'temp', 'wind', 'precip', 'snow', 'LONGITUDE', 'LATITUDE',
                            'speed_limit', 'frc', 'HOUR', 'AvgSp', 'count', 
                            'DAYOFWEEK_Friday', 'DAYOFWEEK_Monday', 'DAYOFWEEK_Thursday',
                            'DAYOFWEEK_Tuesday', 'DAYOFWEEK_Wednesday')]
write.table(daily_data, file = paste0(query_date, "/daily_data.csv"), row.names = FALSE, sep=",")


