from flask import Flask
from flask_cors import CORS
import os
import csv
import json
from scipy import stats

app = Flask(__name__)
CORS(app)


port = 12121
amountOfFuturePredictions = 5000

@app.route('/engines/list')
def enginesList():
    resultJson = "["
    for item in range(700101, 700198):
        if item == 700101:
            resultJson += "{\"key\":\"" + str(item) + "\",\"val\":\"" + str(item)+"\"}"
        else:
            resultJson += ",{\"key\":\"" + str(item) + "\",\"val\":\"" + str(item)+"\"}"
    resultJson += "]"
    return resultJson


@app.route('/engines/<esn>')
def engines(esn):
    jsonString = "["
    with open('preprocessedEngines.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if (row['Engine']) != str(esn):
                continue
            currentStep = int(row['StepsSinceLastRepair'])
            linearRegressionSlope = float(row['MinutesAboveTemperatureSlope'])
            linearRegressionIntercept = float(row['MinutesAboveTemperatureIntercept'])
            currentTemp = float(row['CurrentAcumulatedTime'])
            jsonString += "[" + str(0) + "," + str(currentTemp) + "]"
            if linearRegressionSlope != 0:
                for futureT in range(1,51):
                    predictedTemperature = (futureT * linearRegressionSlope) + currentTemp
                    jsonString += ",[" + str(futureT) + "," + str(predictedTemperature) + "]"
            else:
                slopeAverage = 0
                interceptAverage = 0
                rowAmount = 0
                with open('preprocessedEngines.csv') as csvfile:
                    reader2 = csv.DictReader(csvfile)
                    for row2 in reader2:
                        slopeAverage += float(row2['MinutesAboveTemperatureSlope'])
                        interceptAverage += float(row2['MinutesAboveTemperatureIntercept'])
                        rowAmount += 1
                    slopeAverage /= rowAmount
                    interceptAverage /= rowAmount

                for futureT in range(1,51):
                    predictedTemperature = (futureT * slopeAverage)  + currentTemp
                    jsonString += ",[" + str(futureT) + "," + str(predictedTemperature) + "]"
    jsonString += "]"
    return jsonString


@app.route('/engineTable/<esn>')
def engineTable(esn):
    repairCosts = {}
    with open('airports.csv') as csvfile2:
        reader2 = csv.DictReader(csvfile2)
        for row2 in reader2:
            repairCosts[row2['iata']] = row2['repairCostAtAirport']
    jsonString = "["
    with open('preprocessedEngines.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if (row['Engine']) != str(esn):
                continue
            linearRegressionSlope = float(row['MinutesAboveTemperatureSlope'])
            currentTemp = float(row['CurrentAcumulatedTime'])
            route = row['Route'].split("@")
            currentCity = row['CurrentCity']
            cityPositionInRoute = route.index(currentCity)
            routeCitiesAmount = len(route)
            probabilityOfTemperature = round(stats.norm(11993.375, 26.48415969).cdf(currentTemp) * 100,2)
            jsonString += "{\"itearation\":" + str(0) + ",\"probabilityOfReachingThreshold\":" + str(
                probabilityOfTemperature) + ",\"city\":\"" + currentCity + "\",\"repairCost\": " + repairCosts[
                              currentCity] + "}"
            if linearRegressionSlope != 0:
                for futureT in range(1,amountOfFuturePredictions + 1):
                    predictedTemperature = (futureT * linearRegressionSlope) + currentTemp
                    probabilityOfTemperature = round(stats.norm(11993.375, 26.48415969).cdf(predictedTemperature) * 100,2)
                    destinationCity = route[(cityPositionInRoute + futureT) % routeCitiesAmount]
                    jsonString += ",{\"itearation\":" + str(futureT) + ",\"probabilityOfReachingThreshold\":" + str(probabilityOfTemperature) +",\"city\":\""+ destinationCity + "\",\"repairCost\": "+repairCosts[destinationCity]+"}"
            else:
                slopeAverage = 0
                interceptAverage = 0
                rowAmount = 0
                with open('preprocessedEngines.csv') as csvfile:
                    reader2 = csv.DictReader(csvfile)
                    for row2 in reader2:
                        slopeAverage += float(row2['MinutesAboveTemperatureSlope'])
                        interceptAverage += float(row2['MinutesAboveTemperatureIntercept'])
                        rowAmount += 1
                    slopeAverage /= rowAmount
                    interceptAverage /= rowAmount
                    for futureT in range(1, amountOfFuturePredictions + 1):
                        predictedTemperature = (futureT * slopeAverage) + currentTemp
                        probabilityOfTemperature = round(
                            stats.norm(11993.375, 26.48415969).cdf(predictedTemperature) * 100, 2)
                        destinationCity = route[(cityPositionInRoute + futureT) % routeCitiesAmount]
                        jsonString += ",{\"itearation\":" + str(futureT) + ",\"probabilityOfReachingThreshold\":" + str(
                            probabilityOfTemperature) + ",\"city\":\"" + destinationCity + "\",\"repairCost\": " + \
                                      repairCosts[destinationCity] + "}"

    jsonString += "]"
    return jsonString

@app.route('/engines/critical')
def critical():
    jsonString = "["
    firstRow = True
    with open('preprocessedEngines.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if(float(row['CurrentAcumulatedTime']) > 12000):
                if not firstRow:
                    jsonString += "," + str(row['Engine'])
                else:
                    firstRow = False
                    jsonString += str(row['Engine'])
    jsonString += "]"
    return jsonString

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
