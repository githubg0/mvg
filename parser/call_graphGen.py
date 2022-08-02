import os
import tqdm
import threading
from threading import Thread
import argparse
import pickle
# command="python3 graphGen.py --path "
# command = "python3 graphGenSolution1.py --path "
# rootpath = "../data/CLQ-code16-AST/"
parser = argparse.ArgumentParser(description = 'manual to this script')
parser.add_argument('--writepath', type=str, default=None)
parser.add_argument('--runfile', type=str, default='graph_gen_main.py')
parser.add_argument('--astpath', type=str, default=None, help='path of parsed ast')
parser.add_argument('--cfgpath', type=str, default=None,help='path of parsed cfg')
parser.add_argument('--picky', type=str, default=None, help = '取文件名作为label（WebCode）：1，取文件夹的名字作为label（POJ， SOJ）：0')
parser.add_argument('--load_file_or_not', type=int, default=None)
args = parser.parse_args()
# WriteDir="../DetectSummary/data/CLQ-code16-PKL-Solution2-Graph/"
rootpath = args.astpath
astpath = args.astpath
cfgpath = args.cfgpath
WriteDir = args.writepath

command = "python3 "+args.runfile+".py --astpath " + astpath + " --cfgpath " +cfgpath + ' --picky ' + args.picky + " --path "



# command="ls "
# rootpath="testGetJson/"
typeListTemp=[]
lock=threading.Lock()
detectSignal=0
def add1(ls):
    lock.acquire()
    global typeListTemp
    global detectSignal
    detectSignal=detectSignal+1
    typeListTemp = typeListTemp + ls
    lock.release()
def getResult(file,doc):
    # print("123444")
    global typeListTemp
    global detectSignal
    # print(command + file + "/" + doc+ " --writepath "+ WriteDir)
    os.system(command + file + "/" + doc+ " --writepath "+ WriteDir)
    # print(command + rootpath + file + "/" + doc )
    # os.system(command + rootpath + file + "/" + doc )


"""
load files
"""
if args.load_file_or_not == 1:
    with open('CLQ_file_name.pkl', 'rb') as fp:
        file_info = pickle.load(fp)

    files = file_info.keys()
else:
    files = os.listdir(rootpath)
# print("")
# typeList=[]
# typeListSet=[]
# WriteDir="../DetectSummary/data/CLQ-code16-PKL-Solution2-Graph/"
# WriteDir="/newNAS/Share/longting/PycharmProjects/algorithm-detection-master/data/CLQ-code16-PKL/"
print(len(files))
print(files)
for file in tqdm.tqdm(files):
# for file in files:
#     print(file)
    if file == ".txt":
        continue
    if args.load_file_or_not == 1:
        docs = file_info[file]
    else:
        docs=os.listdir(rootpath+file)
    docsLen = len(docs)
    # threadNum = 800
    #if docsLen == 0 or docsLen < 500:
    #    continue
    if not(os.path.exists(WriteDir+file)):
        # print("data/CLQ-code16-PKL/"+file)
        os.mkdir(WriteDir+file)

    threadNum = 1200
    if threadNum > docsLen:
        threadNum = docsLen
    # print("******************",file,threadNum,docsLen)
    threadTime=int(docsLen/threadNum+1)
    for j in tqdm.tqdm(range(0,threadTime)):
        threadNumThisTurn=threadNum
        nextTarget=threadNum*j+threadNum
        lowerBound=threadNum*(j-1)+threadNum
        if nextTarget>docsLen:
            threadNumThisTurn=docsLen-lowerBound
        # print("aaaaaaaaaaaaaaa")
        for i in tqdm.tqdm(range(0,threadNumThisTurn)):
            # print("processing ",file+"/"+docs[lowerBound+i])
            t=Thread(target=getResult, args=(file,docs[lowerBound+i],),name=docs[lowerBound+i])
            t.start()



