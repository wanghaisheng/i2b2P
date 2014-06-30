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
from nltk.tokenize.punkt import PunktWordTokenizer
from nltk.tokenize import WordPunctTokenizer
from nltk.tokenize import WhitespaceTokenizer

import numpy as ny
from scipy.stats import mode
import pandas as pd

import csv



labelSeq=['during DCT','before DCT','after DCT']
diabetesIndicator=['mention','A1C','glucose']
cadIndicator=['mention','event','test','symptom']
hypertensionIndicator=['mention','high bp']
hyperlipidemiaIndicator=['mention','high chol.','high LDL']
obeseIndicator=['mention','BMI','waist circum.']
diseaseIndi=['mention','event','test','symptom','A1C','glucose','event ','test ','symptom','high bp','high chol.','high LDL''BMI','waist circum.']


def IsMed(type):
    if not type.upper() in 'DIABETES CAD HYPERTENSION HYPERLIPIDEMIA OBESE'.split():
        return 1
    else:
        return 0
    
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def collect(l,index):
    return map(itemgetter(index),l)



numbSpace = lambda s:len(nltk.word_tokenize(s.strip()))-1

#PunktWordTokenizer uses a regular expression to divide a text into tokens, leaving all periods attached to words, but separating off other punctuation:
punctWordToken = lambda s:PunktWordTokenizer().tokenize(s)
#Tokenize a text into a sequence of alphabetic and non-alphabetic characters, using the regexp \w+|[^\w\s]+
wordPunctToken = lambda s:WordPunctTokenizer().tokenize(s)
wordToken = lambda s:nltk.word_tokenize(s)
whitespaceToken = lambda s:WhitespaceTokenizer().tokenize(s)
removePunct = lambda s:''.join([i for i in s if i not in string.punctuation])


#removeLineBreak = lambda s:s.replace('\n',' ')


getETAttr = lambda e, s:e.get(s)  #return the value of attribute s of element e
getETTime = lambda e: getETAttr(e,'time')
getETStart = lambda e: int(getETAttr(e,'start'))
getETEnd = lambda e: int(getETAttr(e,'end'))


setETAttr = lambda e, s, v : e.set(s,str(v)) #set value of attribute s of element e
setETTime = lambda e,v: setETAttr(e,'time',v)
setETStart = lambda e,v: setETAttr(e,'start',v)
setETEnd = lambda e,v: setETAttr(e,'end',v)


removeDuplicate = lambda l: list(OrderedDict.fromkeys(l))



#class
class Tag:
    type=''
    start=-1
    end=-1
    text=''
    comment=''
    treeNode=None
    
    sec_id=''
    
    def __init__(self,start, end, text,comment,treeNode):
        self.start = start
        self.end = end
        self.text = text
        self.comment = comment
        self.treeNode=treeNode
        self.type=treeNode.tag
    
    def __eq__(self,other):
        if other==None:
            return False
        else:
            return self.start==other.start and self.end==other.end 
    def __hash__(self):
        return hash((self.start,self.end))
        
    
    def setStart(self,newStart):
        #print "old start: ",self.start
        self.start=newStart
        setETStart(self.treeNode,newStart)
    def setEnd(self,newEnd):
        #print "old end: ", self.end
        self.end=newEnd
        setETEnd(self.treeNode,newEnd)

        
    def setSecID(self,secName):
        self.sec_id=secName
        self.treeNode.set('secName',secName)
        
        
#DIABETES CAD HYPERTENSION HYPERLIPIDEMIA OBESE  
class Tag_Disease(Tag):
    indicator=''
    time=''
    def __init__(self,start, end, text,comment,treeNode, indicator, time):
        Tag.__init__(self, start, end, text,comment,treeNode)
        self.indicator=indicator
        self.time=time
    def __eq__(self,other):
        return Tag.__eq__(self,other)and self.time==other.time
    def __hash__(self):
        return hash((self.start,self.end,self.time))
 
class Tag_Medication(Tag):
    type1=''
    type2=''
    time=''
    def __init__(self, start, end, text,comment,treeNode, type1, type2, time):
        Tag.__init__(self, start, end, text,comment,treeNode)
        self.type1=type1
        self.type2=type2
        self.time=time
    def __eq__(self,other):
        return Tag.__eq__(self,other)and self.time==other.time
    def __hash__(self):
        return hash((self.start,self.end,self.time))


class aReport:
    root=None
    text=''
    id=''
    dct=None
    tree_medications=None
    tree_obeses=None
    tree_diabetes=None
    tree_cad=None
    tree_hypertension=None
    tree_hyperlipidemia=None
    tree_smoke=None
    tree_family=None
    
    tree_secName=None
    
    tag_medications=[]
    tag_disease=[]
    tags=[]
    tag_secName=[]
    
    textLines=[]
    
    df_tags=None
    df_secTags=None
    
    def __init__(self,fileName):
        self.id=os.path.basename(fileName)
        tree = ET.parse(fileName)
        self.root = tree.getroot() 
        #self.loadAReport() 
        
    def setXMLText(self,newText):
        #replace < with &lt
        self.root.find('TEXT').text=newText
    def setTextLines(self,newTextLines):
        self.textLines=newTextLines
        
    def setText(self,newText):
        self.text=newText
    
    def setText_lines(self,newText,newTextLine):
        self.setText(newText)
        self.setTextLines(newTextLine)
        
    def makeDiseaseTag(self,treeDisease):
        for subDisease in treeDisease:
            start=int(subDisease.get('start'))
            end=int(subDisease.get('end'))
            text=subDisease.get('text')
            comment=subDisease.get('comment')
            indicator=subDisease.get('indicator')
            time=subDisease.get('time')
        #(self, type, start, end, text,comment,treeNode, indicator, time)  
            tag_temp=Tag_Disease(start, end, text,comment,subDisease,indicator,time) 
            self.tag_disease.append(tag_temp) 
            self.tags.append(tag_temp)
    def makeMedicationTag(self,treeMedicaiton):
        for subMedication in treeMedicaiton:
            start=int(subMedication.get('start'))
            end=int(subMedication.get('end'))
            text=subMedication.get('text')
            comment=subMedication.get('comment')
            type1=subMedication.get('type1')
            type2=subMedication.get('type2')
            time=subMedication.get('time')
            #self, type,  start, end, text,comment,treeNode, type1, type2, time
            tag_temp=Tag_Medication(start,end,text,comment,subMedication,type1,type2,time)
            self.tag_medications.append(tag_temp)
            self.tags.append(tag_temp)  
            

           
        
    
    def getContextLine(self,tag,window):
        pass
    def getContextTag(self,tag,window):
        pass

    def getTagSentText(self,tag):
        return tag.text
    
    def reDupTag(self):
        self.tags=removeDuplicate(self.tags)
    def reDupMed(self):
        self.tag_medications=removeDuplicate(self.tag_medications)
    def reDupDisease(self):
        self.tag_disease=removeDuplicate(self.tag_disease)
        
    
    def getTagTense(self,tag):
        words=whitespaceToken(self.getTagLine(tag))
        print words, tag.start,tag.end, tag.text, ' '.join(words[tag.start:tag.end+1])
        return " ".join(words[tag.start:tag.end+1])
                
  
    def loadReport_tags(self):
        self.loadAReport()
        self.tree2Tag()
        
 
    def writeXMLReport(self,outputName):        
        print prettify(self.root)
          
    ##TODO add new tags for temporal expression, or PHI
    ##TODO do nothing to "SMOKER" and "FAMILY_HIST"
    def loadAReport(self):   
        self.text = self.root.find('TEXT').text
        self.dct=self.parseDCT()
        tree_tag=self.root.find('TAGS')  
        self.tree_medications=tree_tag.findall('MEDICATION')
        self.tree_obeses=tree_tag.findall('OBESE')
        self.tree_diabetes=tree_tag.findall('DIABETES')
        self.tree_cad=tree_tag.findall('CAD')
        self.tree_hypertension=tree_tag.findall('HYPERTENSION')
        self.tree_hyperlipidemia=tree_tag.findall('HYPERLIPIDEMIA')
        self.tree_smoke=tree_tag.findall('SMOKER')
        self.tree_family=tree_tag.findall('FAMILY_HIST')
        
        self.textLines=self.text.splitlines()
        
    def parseDCT(self):
        sentences=self.text.splitlines()
        for aSen in sentences:
            aSen_trimed=aSen.strip().lower()
            if aSen_trimed.startswith('record date:'):
                m=re.search("\d",aSen_trimed)
                if m:
                    return aSen_trimed[m.start():]
                    
        print "file "+self.id+" different dct format"
        return " "
   

        
       
   ##TODO only have disease(diabetes, cad, hypertension, hyperlipidemia), medication
   ##TODO need to add ... 
    def tree2Tag(self):
        map(self.makeMedicationTag,self.tree_medications)
        map(self.makeDiseaseTag,self.tree_obeses)
        map(self.makeDiseaseTag,self.tree_diabetes)
        map(self.makeDiseaseTag,self.tree_cad)
        map(self.makeDiseaseTag,self.tree_hypertension)
        map(self.makeDiseaseTag,self.tree_hyperlipidemia)
        
        self.tags.sort(key=lambda x:(x.start,-x.end), reverse=False)
#         for tag in self.tags:
#             print prettify(tag.treeNode)
    
        

    
    def addSecTag(self,lineIndex,start,end,secName):
        treeNode=ET.Element('SecIndicator')
        setETStart(treeNode,start)
        setETEnd(treeNode,end)
        treeNode.set('text',secName)
        treeNode.set('secName',secName)
        self.root.append(treeNode)
        aTag=Tag(0,0, secName,'',treeNode)
        aTag.start=start
        aTag.end=end
        aTag.type=treeNode.tag
        aTag.sec_id=secName
        self.tag_secName.append(aTag)
        #self.tags.append(aTag)
        
        
    def tagSection(self,refFile='./sec_Names.txt'):
        secFile=open(refFile)
        secNames=secFile.read().splitlines()
        offset=0
        for lineIndex, line in enumerate(self.textLines):
            for sec in secNames:
                if sec.lower() in line.lower():
                    start=self.text.find(line,offset)
                    self.addSecTag(lineIndex,start,start+len(line),sec)
                    offset=start+len(line)
                    break
                    
        secTagIndex=0
        currSec='UNKNOWN'    
        for atag in self.tags:
            while secTagIndex<len(self.tag_secName) and atag.start>=self.tag_secName[secTagIndex].start:
                    currSec=self.tag_secName[secTagIndex].sec_id
                    secTagIndex+=1
            atag.setSecID(currSec)
            
        nextStart=-1
        for asectag in reversed(self.tag_secName):
            if nextStart==-1:
                nextStart=asectag.start
                asectag.end=len(self.text)
            else:
                asectag.end=nextStart
                nextStart=asectag.start
            
            
            

    def print_df_csv(self,file):
         self.df_tags.to_csv(file,sep=',',quoting=csv.QUOTE_ALL,index=False)
         self.df_secTags.to_csv(file,sep=',',quoting=csv.QUOTE_ALL,index=False)
   
    def make_df_tags(self):
        
        #i2b2Tags
        
        texts=[]
        indicatorNames=[]
        disease_indic=[]
        med_diseases=[]
        starts=[]
        ends=[]
        sectionNames=[]
        time_befores=[]
        time_durings=[]
        time_afters=[]
        
        for atag in self.tags:
            texts.append(atag.text)
            indicatorNames.append(atag.type)
            med_diseases.append(IsMed(atag.type))
            starts.append(atag.start)
            ends.append(atag.end)
            sectionNames.append(atag.sec_id)
            
            if isinstance(atag,Tag_Medication):
                disease_indic.append(atag.type1)
            else:
                disease_indic.append(atag.indicator)
            
            if atag.time=='during DCT':
                time_durings.append(1)
                time_befores.append(0)
                time_afters.append(0)
            elif atag.time=='before DCT':
                time_befores.append(1)
                time_durings.append(0)
                time_afters.append(0) 
            elif atag.time=='after DCT':
                time_afters.append(1)
                time_befores.append(0)
                time_durings.append(0)
        
        
        headNames=['b_text','b_indiName','b_diseaseIndic','b_isMed','a_start','a_end','b_sectName','time_before','time_during','time_after']
        columnValues=[ texts,indicatorNames,disease_indic,med_diseases,starts,ends,sectionNames,time_befores,time_durings,time_afters]
        adict=dict(zip(headNames, columnValues))
        self.df_tags=pd.DataFrame(adict)
        
        
        grouped=self.df_tags.groupby(['a_start','a_end'],as_index=False)
        agged=grouped.agg({'b_text':{'b_text':lambda x: x.iloc[0]},
                                    'b_indiName':{'b_indiName':lambda x: x.iloc[0]},
                                    'b_isMed':{'b_isMed':lambda x: x.iloc[0]},
                                    'b_sectName':{'b_sectName':lambda x: x.iloc[0]},
                                   'time_before':{'time_before':lambda x: int(ny.any(x))},
                                   'time_during':{'time_during':lambda x: int(ny.any(x))},
                                   'time_after':{'time_after':lambda x: int(ny.any(x))},
                                   'b_diseaseIndic':{'b_diseaseIndic':lambda x:x.iloc[0]} })
        
        agged.columns=agged.columns.droplevel(1)
        #add the DCT as a column before time_after
        dcts=[self.dct]*len(self.tags)
        agged['b_dct']=pd.Series(dcts)
        self.df_tags=agged.sort_index(axis=1)
        
        #secName tags
        
        sec_texts=[]
        sec_starts=[]
        sec_ends=[]
        
        for asecTag in self.tag_secName:
            sec_texts.append(asecTag.text)
            sec_starts.append(asecTag.start)
            sec_ends.append(asecTag.end)
            
        secheadNames=['b_text','a_start','a_end']
        seccolumnValues=[ sec_texts,sec_starts,sec_ends]
        adict=dict(zip(secheadNames, seccolumnValues))
        self.df_secTags=pd.DataFrame(adict)
        self.df_secTags=self.df_secTags.sort_index(axis=1)
             

if __name__=="__main__":
            f='../data/training-RiskFactors-Complete-Set1/220-01.xml'
            oReport = aReport(f)
            oReport.loadReport_tags()
            oReport.tagSection()
            oReport.make_df_tags()
            dirOut=''
            outFileName=dirOut+re.split('\.',oReport.id)[0]+'.csv'
            outFile=open(outFileName,'w')
            outFile.write(oReport.text)
            oReport.print_df_csv(outFile)
            outFile.close()
            

        
        
        
        
        
        
                
            
