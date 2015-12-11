#!/usr/local/bin/python3
#encoding=utf-8

import json
import sys
from els.utils import ElasticFilesGenerator

class Decider:
  
    def __init__(self, config):

        self.options = []
        for option in config['options']:
            self.options.append(option['description'])
        
        self.criteria = {}
        weight_sum = 0
        for criterion in config['criteria']:
            weight = float(criterion['weight'])
            self.criteria[criterion['description']] = weight
            weight_sum = weight_sum + weight

        # weight normalization
        for criterion in self.criteria:
            self.criteria[criterion] = self.criteria[criterion] / weight_sum


    def scores_template(self):

        scores = {}
        
        for criteria in self.criteria:
            scores[criteria] = {}
            for option in self.options:
                scores[criteria][option] = 1

        return scores

    def decide(self, scores):
        
        desition = {}
        for option in self.options:
            desition[option] = {}
            desition[option]["total"] = 0
            desition[option]["description"] = option

        for criterion in scores:
            criterion_score_sum = sum([float(scores[criterion][option]) for option in scores[criterion]])
            for option in scores[criterion]:
                desition[option][criterion] = self.criteria[criterion] * (float(scores[criterion][option]) / criterion_score_sum )
                desition[option]["total"] = ( desition[option]["total"] + desition[option][criterion])

        desition = [ desition[option] for option in desition ]
        return sorted(desition,key = lambda x: x['total'], reverse=True)

with open(sys.argv[1],'r') as f:
    config = json.load(f)

decider = Decider(config)

if len(sys.argv) == 3:
    with open(sys.argv[2],'r') as f:
        scores = json.load(f)
    desition = decider.decide(scores)
    efg = ElasticFilesGenerator("wdecide", "wdecide", "wdecide")
    for i in range(len(desition)):
        
        # stdout
        print("(%s) [%s]: %s" % (i+1, desition[i]['description'], desition[i]['total']))

        # elastic search bulk file
        for criteria in desition[i]:
            if criteria == 'description' or criteria == 'total':
                continue
            efg.add({
               'option': desition[i]["description"],
               'criteria': criteria,
               'value': desition[i][criteria],
               },"%s-%s" %(desition[i]["description"], criteria))
else:
    print(json.dumps(
        decider.scores_template(),
        sort_keys=True, indent=4, ensure_ascii=False))
    
