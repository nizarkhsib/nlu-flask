from __future__ import unicode_literals, print_function
import io
import json
import datetime
import re
import pandas as pd
import numpy as np
import os
from snips_nlu import SnipsNLUEngine, load_resources
from snips_nlu.default_configs import config_fr
from flask import Flask
from flask import jsonify
from flask import request
from flask_pymongo import PyMongo
import pprint
import pymongo
from pymongo import MongoClient
from odo import odo
from flask_cors import CORS
from collections import defaultdict
import datetime

app = Flask(__name__)
CORS(app)
app.config['MONGO_DBNAME'] = 'apiwatch'
app.config['MONGO_URI'] = 'mongodb://51.38.49.225:27017/apiwatch'
mongo = PyMongo(app)



with io.open("./datajson.json") as f:
    sample_dataset = json.load(f)

load_resources("fr")
nlu_engine = SnipsNLUEngine()
nlu_engine.fit(sample_dataset)



@app.route('/star', methods=['GET'])
def get_all_stars():
  star = mongo.db.apiwatch
  output = []
  for s in star.find():
    output.append({'texte' : s['texte']})
  return jsonify({'result' : output})


@app.route('/star', methods=['POST'])
def add_star():
  texte = request.json['texte']
  

  sentences = re.split(r' *[\.\,?!\n][\'"\)\]]* *', texte[:])
  vide = ''
  espace = ' '
  if(vide in sentences):
    sentences.remove('')
  if(espace in sentences):
    sentences.remove(' ')


  date = datetime.datetime.now()
  date = date.strftime('%Y-%m-%d')


  liste = [] 
  for phrase in sentences:
    liste_boucle = [] 
    liste_ruche = []  
    liste_boucle.append(phrase)                          
            
    parsing = nlu_engine.parse(phrase)                    
            
    if(parsing['intent']):                                 
        prediction = parsing['intent']['intentName']       
        liste_boucle.append(prediction)                  
                
        proba = parsing['intent']['probability']
        liste_boucle.append(proba)                      
            
        for i in parsing['slots']:                       
            if(i['slotName'] == 'IdRuche'):     
                ruche = i['rawValue']              
                liste_ruche.append(ruche)                      
        liste_boucle.append(liste_ruche)                
        
    if (len(liste_boucle) == 1): 
        liste_boucle.append(None)
        liste_boucle.append(None)
        liste_boucle.append(None)
        
    elif (len(liste_boucle) == 2): 
        liste_boucle.append(None)
        liste_boucle.append(None)
        
    elif (len(liste_boucle) == 3): 
        liste_boucle.append(None)
        
    liste.append(liste_boucle) 
            
  df = pd.DataFrame(liste, columns=['sentence', 'type','nluScore', 'ruche'])
  
  df['idApiary']= request.json['idApiary']
  df['date'] = date
  results = json.loads(df.T.to_json()).values()
  mongo.db.tempReport.insert(results)
  
  data_null = df[df['nluScore'].isnull()]
  note_incomprehensibles = pd.DataFrame()
  note_incomprehensibles = data_null.append(df[df['nluScore']<0.50])
  
  records = json.loads(note_incomprehensibles.T.to_json()).values()
  mongo.db.dataIncorect.insert(records)
  

  #derneire solution:
  #dfList = df.values.tolist()
  #return jsonify(dfList)
  result = df.to_dict(orient="index")
  #mydict = defaultdict(list)
  # for key, value in result.items():
  # mydict[key].append(value)  
  #result = {'result' : mydict}

  return jsonify(result)

 #return jsonify(json.dumps(json.loads(df.to_json(orient='list')),indent=2))
 #return render_template(result), 201, {'Content-Type': 'application/json'}
if __name__ == '__main__':
    app.run(host='51.38.49.225')

