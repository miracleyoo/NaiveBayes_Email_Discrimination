#!/usr/bin/python2.7
# _*_ coding: utf-8 _*_

from sqlite3 import dbapi2 as sqlite
import re
import math
import os

def getwords(doc):
  splitter=re.compile(r'[a-zA-Z]*')
  # print doc
  # Split the words by non-alpha characters
  words=[s.lower() for s in splitter.findall(doc) 
          if len(s)>2 and len(s)<20]
  # print words
  # Return the unique set of words only
  if(flag==1):
      if(len(words)>400):
          # print len(words)
          words=words[:400]
  # print dict([(w,1) for w in words])
  return dict([(w,1) for w in words])

class classifier:
  def __init__(self,getfeatures,filename=None):
    # Counts of feature/category combinations
    self.fc={}
    # Counts of documents in each category
    self.cc={}
    self.getfeatures=getfeatures
    
  def setdb(self,dbfile):
    self.con=sqlite.connect(dbfile)  
    self.con.text_factory = str    
    self.con.execute('create table if not exists fc(feature,category,count)')
    self.con.execute('create table if not exists cc(category,count)')
    self.con.execute('create table if not exists res(category,wr,count)')
    
  def incf(self,f,cat):
    count=self.fcount(f,cat)
    if count==0:
      self.con.execute("insert into fc values (?,?,1)" 
                       , (f,cat))
    else:
      self.con.execute(
        "update fc set count=? where feature=? and category=?" 
        , (count+1,f,cat)) 
  
  def fcount(self,f,cat):
    res=self.con.execute("select count from fc where feature=? and category=?" , (f,cat)).fetchone()
    if res==None: return 0
    else: return float(res[0])

  def incc(self,cat):
    count=self.catcount(cat)
    if count==0:
        #print cat
        self.con.execute("insert into cc values (?,1)" , (cat,))
    else:
        self.con.execute("update cc set count=? where category=?" 
                       , (count+1,cat))    

  def catcount(self,cat):
    #print cat
    res=self.con.execute('select count from cc where category=?',(cat,)).fetchone()
    if res==None: return 0
    else: return float(res[0])

  def categories(self):
    cur=self.con.execute('select category from cc');
    return [d[0] for d in cur]

  def totalcount(self):
    res=self.con.execute('select sum(count) from cc').fetchone();
    if res==None: return 0
    return res[0]

  def inres(self,cat,wr):
    count=self.rescount(cat,wr)
    if count==0:
        #print cat
        self.con.execute("insert into res values (?,?,1)" , (cat,wr))
    else:
        self.con.execute("update res set count=? where category=? and wr=?" 
                       , (count+1,cat,wr))    

  def rescount(self,cat,wr):
      #print cat
      res=self.con.execute('select count from res where category=? and wr=?',(cat,wr)).fetchone()
      if res==None: return 0
      else: return float(res[0])
    
    
  def train(self,item,cat):
    features=self.getfeatures(item)
    # Increment the count for every feature with this category
    for f in features:
      self.incf(f,cat)

    # Increment the count for this category
    self.incc(cat)
    self.con.commit()

  def fprob(self,f,cat):
    if self.catcount(cat)==0: return 0

    # The total number of times this feature appeared in this 
    # category divided by the total number of items in this category
    return self.fcount(f,cat)/self.catcount(cat)

  def weightedprob(self,f,cat,prf,weight=1.0,ap=0.5):
    # Calculate current probability
    basicprob=prf(f,cat)

    # Count the number of times this feature has appeared in
    # all categories
    totals=sum([self.fcount(f,c) for c in self.categories()])

    # Calculate the weighted average
    bp=((weight*ap)+(totals*basicprob))/(weight+totals)
    #print "bp: ",bp
    return bp




class naivebayes(classifier):
  
  def __init__(self,getfeatures):
    classifier.__init__(self,getfeatures)
    self.thresholds={}
  
  def docprob(self,item,cat):
    features=self.getfeatures(item)   

    # Multiply the probabilities of all the features together
    p=1
    for f in features: p*=self.weightedprob(f,cat,self.fprob)
    # print "p=",p
    return p

  def prob(self,item,cat):
    catprob=self.catcount(cat)/self.totalcount()
    # print "catprob is: "
    # print catprob
    docprob=self.docprob(item,cat)
    # print "docprob is: "
    # print docprob
    return docprob*catprob
  
  def setthreshold(self,cat,t):
    self.thresholds[cat]=t
    
  def getthreshold(self,cat):
    if cat not in self.thresholds: return 1.0
    return self.thresholds[cat]
  
  def classify(self,item,default=None):
    probs={}
    # Find the category with the highest probability
    max=0.0
    # best=default
    # print self.categories()
    for cat in self.categories():
      probs[cat]=self.prob(item,cat)
      # print "probs[cat] is: ",probs[cat]
      # print probs[cat]
      if probs[cat]>max: 
        max=probs[cat]
        best=cat
    #     print "cat is: "
    #     print cat
    # print "best is: "
    # print best
    # Make sure the probability exceeds threshold*next best
    for cat in probs:
      if cat==best: continue
      if probs[cat]*self.getthreshold(best)>probs[best]: return default
    print "best is: ",best
    return best

class fisherclassifier(classifier):
  def cprob(self,f,cat):
    # The frequency of this feature in this category    
    clf=self.fprob(f,cat)
    if clf==0: return 0

    # The frequency of this feature in all the categories
    freqsum=sum([self.fprob(f,c) for c in self.categories()])

    # The probability is the frequency in this category divided by
    # the overall frequency
    p=clf/(freqsum)
    
    return p
  def fisherprob(self,item,cat):
    # Multiply all the probabilities together
    p=1
    features=self.getfeatures(item)
    for f in features:
      p*=(self.weightedprob(f,cat,self.cprob))

    # Take the natural log and multiply by -2
    fscore=-2*math.log(p)

    # Use the inverse chi2 function to get a probability
    return self.invchi2(fscore,len(features)*2)
  def invchi2(self,chi, df):
    m = chi / 2.0
    sum = term = math.exp(-m)
    for i in range(1, df//2):
        term *= m / i
        sum += term
    return min(sum, 1.0)
  def __init__(self,getfeatures):
    classifier.__init__(self,getfeatures)
    self.minimums={}

  def setminimum(self,cat,min):
    self.minimums[cat]=min
  
  def getminimum(self,cat):
    if cat not in self.minimums: return 0
    return self.minimums[cat]
  def classify(self,item,default=None):
    # Loop through looking for the best result
    best=default
    max=0.0
    for c in self.categories():
      p=self.fisherprob(item,c)
      # Make sure it exceeds its minimum
      if p>self.getminimum(c) and p>max:
        best=c
        max=p
    return best


def sampletrain(cl):
  cl.train('Nobody owns the water.','good')
  cl.train('the quick rabbit jumps fences','good')
  cl.train('buy pharmaceuticals now','bad')
  cl.train('make quick money at the online casino','bad')
  cl.train('the quick brown fox jumps','good')

   
    
def GetFileList(dir, fileList):
    newDir = dir
    if os.path.isfile(dir):
        fileList.append(dir.decode('gbk'))
    elif os.path.isdir(dir):  
        for s in os.listdir(dir):
            #if s == "xxx":
                #continue
            newDir=os.path.join(dir,s)
            GetFileList(newDir, fileList)  
    return fileList
 
def doctrain(cl):
    dir=os.getcwd()
    dirham=dir+r'\data_set\hw1_data\train\ham'
    # print dirham+'\n'
    dirspam=dir+r'\data_set\hw1_data\train\spam'
    list1 = GetFileList(dirspam, [])
    list2 = GetFileList(dirham, [])
    # print list1+'\n'
    for item in list1:
        f=open(item)
        words=f.read()
        #words = textParser(f)
        print 'This is a spam: '+item+'\n'
        cl.train(words,'spam')
    for item in list2:
        f=open(item)
        words=f.read()
        #words = textParser(f)
        print 'This is a ham: '+item+'\n'
        cl.train(words,'ham')

        

if __name__ == '__main__':
    flag=0
    c1=naivebayes(getwords)
    c1.setdb('test1.db')
    #doctrain(c1)
else:
    flag=1
    #c1=naivebayes(getwords)
    #c1.setdb('test1.db')   
    #print c1.classify('quick',default='unknown')