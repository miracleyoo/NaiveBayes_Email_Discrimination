#!/usr/bin/python2.7
# _*_ coding: utf-8 _*_

"""
@Author: Miracle Yoo
"""
import numpy as np
import os

def textParser(text):
    """
    对SMS预处理，去除空字符串，并统一小写
    :param text:
    :return:
    """
    import re
    regEx = re.compile(r'([a-zA-Z])+')  # 匹配非字母或者数字，即去掉非字母非数字，只留下单词
    words = regEx.split(text)
    # 去除空字符串，并统一小写
    words = [word.lower() for word in words if len(word) > 0]
    return words

def GetFileList(dir, fileList):
    newDir = dir
    if os.path.isfile(dir):
        fileList.append(dir.decode('gbk'))
    elif os.path.isdir(dir):  
        for s in os.listdir(dir):
            #如果需要忽略某些文件夹，使用以下代码
            #if s == "xxx":
                #continue
            newDir=os.path.join(dir,s)
            GetFileList(newDir, fileList)  
    return fileList
 
def loadSMSData(fileName):
    classCategory = []  # 类别标签，1表示是垃圾SMS，0表示正常SMS
    smsWords = []
    dir=os.getcwd()
    dirham=dir+'\data set\hw1_data\test\ham'
    dirspam=dir+'\data set\hw1_data\test\spam'
    list1 = GetFileList(dirspam, [])
    list2 = GetFileList(dirham, [])
    
    for item in list1:
        classCategory.append(1)
        f=open(item)
        temp=f.read()
        words = textParser(f)
        smsWords.append(words)
    for item in list2:
        classCategory.append(0)
        f=open(item)
        temp=f.read()
        words = textParser(f)
        smsWords.append(words)
    
    return smsWords, classCategory   
    
    
    
def createVocabularyList(smsWords):
    """
    创建语料库
    :param smsWords:
    :return:
    """
    vocabularySet = set([])
    for words in smsWords:
        vocabularySet = vocabularySet | set(words)
    vocabularyList = list(vocabularySet)
    return vocabularyList


def getVocabularyList(fileName):
    """
    从词汇列表文件中获取语料库
    :param fileName:
    :return:
    """
    fr = open(fileName)
    vocabularyList = fr.readline().strip().split('\t')
    fr.close()
    return vocabularyList


def setOfWordsToVecTor(vocabularyList, smsWords):
    """
    SMS内容匹配预料库，标记预料库的词汇出现的次数
    :param vocabularyList:
    :param smsWords:
    :return:
    """
    vocabMarked = [0] * len(vocabularyList)
    for smsWord in smsWords:
        if smsWord in vocabularyList:
            vocabMarked[vocabularyList.index(smsWord)] += 1
    return vocabMarked


def setOfWordsListToVecTor(vocabularyList, smsWordsList):
    """
    将文本数据的二维数组标记
    :param vocabularyList:
    :param smsWordsList:
    :return:
    """
    vocabMarkedList = []
    for i in range(len(smsWordsList)):
        vocabMarked = setOfWordsToVecTor(vocabularyList, smsWordsList[i])
        vocabMarkedList.append(vocabMarked)
    return vocabMarkedList


def trainingNaiveBayes(trainMarkedWords, trainCategory):
    """
    训练数据集中获取语料库中词汇的spamicity：P（Wi|S）
    :param trainMarkedWords: 按照语料库标记的数据，二维数组
    :param trainCategory:
    :return:
    """
    numTrainDoc = len(trainMarkedWords)
    numWords = len(trainMarkedWords[0])
    # 是垃圾邮件的先验概率P(S)
    pSpam = sum(trainCategory) / float(numTrainDoc)

    # 统计语料库中词汇在S和H中出现的次数
    wordsInSpamNum = np.ones(numWords)
    wordsInHealthNum = np.ones(numWords)
    spamWordsNum = 2.0
    healthWordsNum = 2.0
    for i in range(0, numTrainDoc):
        if trainCategory[i] == 1:  # 如果是垃圾SMS或邮件
            wordsInSpamNum += trainMarkedWords[i]
            spamWordsNum += sum(trainMarkedWords[i])  # 统计Spam中语料库中词汇出现的总次数
        else:
            wordsInHealthNum += trainMarkedWords[i]
            healthWordsNum += sum(trainMarkedWords[i])
    # 计算语料库中词汇的spamicity：P（Wi|S）和P（Wi|H）
    # pWordsSpamicity = []
    #
    # for num in wordsInSpamNum:
    #     if num == 0:
    #         pWordsSpamicity.append(np.log(pSpam))
    #     else:
    #         pWordsSpamicity.append(np.log(num / spamWordsNum))
    #
    # pWordsHealthy = []
    # for num1 in wordsInHealthNum:
    #     if num1 == 0:
    #         pWordsHealthy.append(np.log(1-pSpam))
    #     else:
    #         pWordsHealthy.append(np.log(num1 / healthWordsNum))
    #
    # return np.array(pWordsSpamicity), np.array(pWordsHealthy), pSpam

    pWordsSpamicity = np.log(wordsInSpamNum / spamWordsNum)
    pWordsHealthy = np.log(wordsInHealthNum / healthWordsNum)

    return pWordsSpamicity, pWordsHealthy, pSpam


def getTrainedModelInfo():
    """
    获取训练的模型信息
    :return:
    """
    # 加载训练获取的语料库信息
    vocabularyList = getVocabularyList('vocabularyList.txt')
    pWordsHealthy = np.loadtxt('pWordsHealthy.txt', delimiter='\t')
    pWordsSpamicity = np.loadtxt('pWordsSpamicity.txt', delimiter='\t')
    fr = open('pSpam.txt')
    pSpam = float(fr.readline().strip())
    fr.close()

    return vocabularyList, pWordsSpamicity, pWordsHealthy, pSpam


def classify(vocabularyList, pWordsSpamicity, pWordsHealthy, pSpam, testWords):
    """
    计算联合概率进行分类
    :param vocabularyList:
    :param pWordsSpamicity:
    :param pWordsHealthy:
    :param pSpam:
    :param testWords:
    :return:
    """
    testWordsCount = setOfWordsToVecTor(vocabularyList, testWords)
    testWordsMarkedArray = np.array(testWordsCount)
    # 计算P(Ci|W)，W为向量。P(Ci|W)只需计算P(W|Ci)P(Ci)
    p1 = sum(testWordsMarkedArray * pWordsSpamicity) + np.log(pSpam)
    p0 = sum(testWordsMarkedArray * pWordsHealthy) + np.log(1 - pSpam)
    if p1 > p0:
        return 1
    else:
        return 0

    


