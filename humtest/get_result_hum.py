 #!/usr/bin/python2.7
# _*_ coding: utf-8 _*_
 
import docclass as ori
import os

c1=ori.fisherclassifier(ori.getwords)
c1.setdb('test1_05.db')


'''
def getrate(self)
    right=sum(self.con.execute('select count from cc where wr=1',(cat,wr)).fetchall().value())
    wrong=sum(self.con.execute('select count from cc where wr=0',(cat,wr)).fetchall().value())
    rate=right/(right+wrong)
    return rate
'''
    
def doctest(cl):
    right=0.0
    wrong=0.0
    dir=os.getcwd()
    dirham=dir+r'\data_set\hw1_data\test\ham'
    # print dirham+'\n'
    dirspam=dir+r'\data_set\hw1_data\test\spam'
    list1 = ori.GetFileList(dirspam, [])
    list2 = ori.GetFileList(dirham, [])
    # print list1+'\n'
    '''
    for item in list1:
        f=open(item)
        words=f.read()
        #words = textParser(f)
        print 'This is a spam: '+item+'\n'
        temp=c1.classify(words,default='unknown')
        
        if (temp=="spam"):
            right+=1
            c1.inres('spam',1)
        else:
            wrong+=1
            c1.inres('spam',0)
        print ("目前正确").decode("utf-8"),right,("个，错误").decode("utf-8"),wrong,("个，正确率为：").decode("utf-8"),right/(right+wrong)
        '''
    for item in list2:
        f=open(item)
        words=f.read()
        #words = textParser(f)
        # print 'This is a ham: '+item+'\n'
        temp=c1.classify(words,default='unknown')
        if (temp=="ham"):
            right+=1
            c1.inres('ham',1)
        else:
            wrong+=1
            c1.inres('ham',0)
        print ("目前正确").decode("utf-8"),right,("个，错误").decode("utf-8"),wrong,("个，正确率为：").decode("utf-8"),right/(right+wrong)
    return right/(right+wrong)

rate=doctest(c1)
print ("该选择器判断正确率是： ").decode("utf-8") +"%0.2f%%" % rate

