from flask import Flask, request, jsonify
import json
import os
import math
import sqlite3
from datetime import datetime, timedelta
from tqdm import tqdm

# Code for haversine function courtesy of GeeksforGeeks (https://www.geeksforgeeks.org/haversine-formula-to-find-distance-between-two-points-on-a-sphere/)
def haversine(lat1, lon1, lat2, lon2):
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0
    lat1 = (lat1) * math.pi / 180.0
    lat2 = (lat2) * math.pi / 180.0
    a = (pow(math.sin(dLat / 2), 2) + pow(math.sin(dLon / 2), 2) * math.cos(lat1) * math.cos(lat2))
    rad = 6371
    c = 2 * math.asin(math.sqrt(a)) 
    return rad * c

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/graph', methods = ['GET'])
def contact_graph():
    if os.path.exists('matrix.json') == False:
        subject_id = int(request.args.get('subject_id', default = ""))
        date = request.args.get('date', default = "")
        timestamp = datetime.strptime(date, '%Y%m%d')
        if subject_id == "" or date == "":
            return "Parameters missing"
        locations = []
        for i in range(1,12):
            db_file = "LifeMap_GS" + str(i) + ".db"
            try:
                conn = sqlite3.connect(db_file)
            except sqlite3.Error as e:
                print(e)
            cur = conn.cursor()
            query = "SELECT (_latitude*1.0)/1000000, (_longitude*1.0)/1000000, substr(_time_location, 1, 8) FROM locationTable WHERE substr(_time_location, 1, 8) <= \"" + date + "\""
            if i == subject_id:
                query += " AND substr(_time_location, 1, 8) > \"" + str(datetime.date(timestamp - timedelta(days = 7))).replace('-','') + "\""
            cur.execute(query + " ORDER BY substr(_time_location, 1, 8)")
            locations.append(cur.fetchall())
        adj_matrix = [[0]*11 for i in range(11)]
        subject_timestamps = [None]*11
        for sub_loc in tqdm(locations[subject_id-1]):
            for i, subject in enumerate(locations):
                if i != subject_id-1:
                    for loc in subject:
                        if datetime.strptime(sub_loc[2], '%Y%m%d') == datetime.strptime(loc[2], '%Y%m%d') and haversine(sub_loc[0], sub_loc[1], loc[0], loc[1]) <=5:
                            adj_matrix[subject_id-1][i] = 1
                            subject_timestamps[i] = datetime.strptime(sub_loc[2], '%Y%m%d')
                            break
        for i, subject in tqdm(enumerate(locations), total = len(locations)):
            if adj_matrix[subject_id-1][i] == 1:
                for sub_loc in locations[i]:
                    if subject_timestamps[i] - timedelta(days = 7) < datetime.strptime(sub_loc[2], '%Y%m%d'):
                        for j, subject in enumerate(locations):
                            if j != i:
                                for loc in subject:
                                    if datetime.strptime(sub_loc[2], '%Y%m%d') == datetime.strptime(loc[2], '%Y%m%d') and haversine(sub_loc[0], sub_loc[1], loc[0], loc[1]) <=5:
                                        adj_matrix[i][j] = 1
                                        break
        f = open("matrix.json", 'w')
        json.dump(adj_matrix, f)
        f.close()
        return jsonify(adj_matrix)
    f = open("matrix.json", 'r')
    matrix = json.load(f)
    f.close()
    return jsonify(matrix)

@app.route('/upload', methods = ['POST'])
def upload_file():
    f = open(os.path.join(app.config['UPLOAD_FOLDER'], "data.json"), 'w')
    json.dump(request.json, f)
    f.close()
    return "Uploaded"

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug = True)