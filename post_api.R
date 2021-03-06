library(httr)
library(lubridate)
set_config(config(ssl_verifypeer = 0L))

tomtom_query = function(left_lon, right_lon, top_lat, down_lat, date){

  week_day = toupper(substring(weekdays(as.Date(date)), 1, 3))

  from_date = as.Date(date)-3
  to_date = as.Date(date)+3

  timesets = paste0(
    '{
    "name":"0-1",
    "timeGroups":[
      {
        "days":[
          "', week_day, '"
          ],
        "times":[
          "0:00-0:01"
          ]
      }
      ]
  }')
  for(i in 1:23){
    temp = paste0(
      '{
        "name":"', i, '-', i+1, '",
        "timeGroups":[
          {
            "days":[
              "', week_day, '"
              ],
            "times":[
              "', i, ':00-', i+1, ':00', '"
              ]
          }
          ]
      }')
    timesets = paste(timesets, temp, sep = ",\n")
  }

  body = paste0('{
    "jobName":"', date, '",
    "distanceUnit":"MILES",
    "network": {
      "name": "co",
      "boundingBox" : {
        "leftDownCorner": {
          "longitude":', left_lon, ',
          "latitude":', down_lat, '
        },
        "rightTopCorner": {
          "longitude":', right_lon, ',
          "latitude":', top_lat, '
        }
      },
      "timeZoneId": "US/Eastern",
      "frcs": [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8"
        ],
      "probeSource":"ALL"
    },
    "dateRange": {
      "name":"', date, '",
      "from":"', from_date, '",
      "to":"', to_date, '"
    },
    "timeSets":[',
                timesets,
                ']
  }')

  p = POST(
    "https://api.tomtom.com/traffic/trafficstats/caa/1?key=j8DuYC17MaGl0UcKLcI9gGSd1e3rpvaJ",
    body = body,
    encode = "raw",
    content_type_json()
  )
  jobId = content(p, "parse")$jobId
  if(is.null(jobId)) {
    jobId = NA
  }
  return(list(date=date, Id=jobId))
}

left = -85.518
right = -84.892
top = 35.46
down = 34.738

args = commandArgs(trailingOnly=TRUE)
query_date = args[1] # Date format: "yyyy-mm-dd"

job = tomtom_query(left, right, top, down, query_date)
if(is.na(job$Id)) {
  cat(paste0('TomTom data query for ', query_date, " is failed!\n"))
} else {
  cat(paste0('TomTom data query for ', query_date, " is successful!\n"))
}

if(!file.exists('job')) {
  dir.create('./job/')
}
saveRDS(job, paste0('./job/', query_date, '_job.rds'))
