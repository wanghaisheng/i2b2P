import string
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import sys
import time
from datetime import date
import re
from subprocess import call
from collections import OrderedDict
from operator import itemgetter
import nltk
import lexicons
from nltk.tag.stanford import NERTagger

def TF2binary(x):
    if str(x) == 'False' or str(x) == '0':
        return str(0)
    elif str(x) == '-1':
        return str(-1)
    else:
        return str(1)

def collect(l,index):
    return map(itemgetter(index),l)

labelSeq=['during DCT','before DCT','after DCT','continuing', ]
posSeq=['VB','VBD','VBG','VBN','VBP','VBZ','MD']
lexiconSeq=re.split(',','before,after,cause,causedBy,during,starting,continuing,ending,suddenly,now,says')
#dependencySeq=re.split(',','gov,gov_POS')
disease_factors=re.split(' ','DIABETES CAD HYPERTENSION HYPERLIPIDEMIA OBESE')


secFile=open('sec_Names.txt','r')
secNameSeq=secFile.read().splitlines()
secFile.close()

relWordDict=open('wordDict.txt','r')
relWordSeq=relWordDict.read().splitlines()
relWordDict.close()

dictFeature=dict()
features=posSeq+lexiconSeq+secNameSeq+relWordSeq
for index, val in enumerate(features):
    dictFeature[val]=index+1
 

'''
features_pos, include the POS of verb and modal within the sentence
features_lexicon, 
features_dependencyTree, include govening word and its POS tag, length of the path through
the dependency from each entity to their common ancestor and the path between the two entities
... the agreement of different dependency parser

features_pathLEngth

'''
'''
first column is the tag_id,the last four column is the time attribute value(four values in the dtd)
time ( before DCT | during DCT | after DCT | continuing ) 
'''
# class Features:
#     TAG_ID==0
#     BEFORE_DCT,DURING_DCT,AFTER_DCT,CONTINUING=
          
    
class ds:
    #2    170/84    physical exam    high bp    VBN
    DICT_HEAD={'timeValue':0,'annoText':1,"secName":2, "indicator":3,"POS":4}
    #label, id of the instance
    def __init__(self,dirIn):
        self.instances={0:[],1:[],2:[],3:[],4:[],5:[],6:[],7:[]}
        self.catFiles(dirIn)
        
    def catFiles(self,dirIn):
        for dirname, dirnames, filenames in os.walk(dirIn):
            for filename in filenames:
                if filename.strip()[0]=='.' :
                    continue
                f = os.path.join(dirname, filename)
                ff=open(f) 
                lines=ff.read().splitlines()
                for line in lines:
                    values=re.split("\t",line)
                    self.instances[int(values[self.DICT_HEAD['timeValue']])].append(line)
   
    def spaceAline(self,timeValue,p_n,of):
        for line in self.instances.get(timeValue):
                featureColumns=[] 
                values=re.split("\t", line)
                alineDS=p_n
                for value in values[1:]:
                    column=dictFeature.get(value)
                    if column is not None and column not in featureColumns:
                        featureColumns.append(column)
                featureColumns.sort()
                for aCol in featureColumns:
                    alineDS+=" "+str(aCol)+":1"
                of.write(alineDS+'\n')
                        
                        
    def continueData(self,dirOut):
        f=open(dirOut+"continue.data",'w')
        self.spaceAline(7, '1', f)
        for qq in [0,1,2,3,4,5,6]:
            self.spaceAline(qq, '-1', f)
        f.close()

    def beforeData(self,dirOut):
        f=open(dirOut+"before.data",'w')
        for qq in [1,3,5,7]:
            self.spaceAline(qq, '1', f)
        for pp in [0,2,4,6]:
            self.spaceAline(pp, '-1', f)
        f.close()
        
    def duringData(self,dirOut):
        f=open(dirOut+"during.data",'w')
        for qq in [2,3,6,7]:
            self.spaceAline(qq, '1', f)
        for pp in [0,1,4,5]:
            self.spaceAline(pp, '-1', f)
        f.close()
        
    def afterData(self,dirOut):
        f=open(dirOut+"after.data",'w')
        for qq in [4,5,6,7]:
            self.spaceAline(qq, '1', f)
        for pp in [1,2,3]:
            self.spaceAline(pp, '-1', f)
        f.close()
    
           
    
if __name__=="__main__":
    dirIn = sys.argv[1]
    dirOut=sys.argv[2]
    a=ds(dirIn)
    a.continueData(dirOut)
    a.beforeData(dirOut)
    a.duringData(dirOut)
    a.afterData(dirOut)
#     a=ds('data/input/')
#     a.continueData('data/output/')
    

        
        
        
        
        