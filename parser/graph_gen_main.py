import os
import pickle
# import torch
import tqdm
import json
import itertools
import pickle
import operator
import argparse
from tkinter import _flatten

# from torch_geometric.data import Data

GuardByList = ["CXXCatchStmt", "SwitchStmt", "ForStmt", "WhileStmt", "DoStmt"]  # ,"GotoStmt"
computedFrom = ["DecompositionDecl", "CompoundAssignOperator", "UnaryOperator", "CXXCtorInitializer", "BinaryOperator",
                "VarDecl", "CXXCtorInitializer"]
# RecurentControlList=["ForStmt","WhileStmt","GotoStmt",]
funCallList = ["CallExpr", "CXXConstructExpr", "CXXMemberCallExpr"]
ConstantNodeList = ["IntegerLiteral", "StringLiteral", "CXXBoolLiteralExpr", "FloatingLiteral", "CharacterLiteral",
                    "EnumConstantDecl", "ConstantExpr"]
ControlList = ["IfStmt", "CXXCatchStmt", "SwitchStmt", "ForStmt", "WhileStmt", "DoStmt", "CXXForRangeStmt", "CaseStmt"]

TokenExcludeSet = ["VarDecl", "IntegerLiteral", "StringLiteral", "CXXBoolLiteralExpr", "FloatingLiteral",
                   "CharacterLiteral", "BindingDecl", "EnumConstantDecl", "referencedDecl", "FieldDecl", "ParmVarDecl",
                   "CXXNullPtrLiteralExpr", "GNUNullExpr", "MemberExpr"]
varTokenExclude = ["IntegerLiteral", "StringLiteral", "CXXBoolLiteralExpr", "FloatingLiteral",
                   "CharacterLiteral", "CXXNullPtrLiteralExpr", "GNUNullExpr"]
FunctionDecl = ["CXXMethodDecl", "FunctionDecl", "CXXConstructorDecl", "CXXDestructorDecl"]
orgDataType = ["std::__cxx11::string", "int", "long", "bool", "char", "float", "short", "double", "void",
               "wchar_t", "unsigned char", "short"]
operatorKind = ["CXXDependentScopeMemberExpr", "UnaryExprOrTypeTraitExpr", "ArraySubscriptExpr", "BinaryOperator",
                "BinaryConditionalOperator", "DecompositionDecl", "CompoundAssignOperator", "UnaryOperator",
                "CXXOperatorCallExpr"]

elementGlobalList = []  # 记录全局的element
# tempElementGlobalList=[]
firsteleRecord = []
operatorList = []
# nodeNum=0
nodeNum = 100000000
StartnodeNum = 100000000
# nodeNumType=dict([])
FuncDict = dict([])
iddict = dict([])  # 用来疾苦ast上的节点ID与IndeX的关系
# ControlRange=dict([])
TokenList = []
mySingleTree = dict([])
# x=dict([]) #记录节点的索引值，名称及其类型，如果没有了；类型就为空
x = []
edges = []  # 记录边及边的属性
currentIndex = 0
constantDict = dict([])
edgePair = []
nodeNumIndexDic = dict([])
edgeTypeList = []
edgedX = []
returnStmtDict = dict([])  # record the returnstmt's function Index and its endnode
return_functionDecl = dict([])
callFuncIndex = dict([])  # record the called function and its endnode
callFuncOpDeclIndex = []  # the operator index(first item) and the function index it calls (last item)
loopCondition = []
FuncDictIndex = []
FuncParaIndex = dict([])


def buildTree(js, thisIndex, ancestors, FunDecIndex, parentIndex, ph, line, Ctrlsignal, inCXX, addIntoFirstEle):
    global mySingleTree
    global currentIndex
    global FuncDict
    global TokenList
    global x
    global edges
    global iddict
    nodeDict = dict([])

    try:
        nodeDict["Index"] = thisIndex
        thisNode = js["kind"]
        nodeDict["ph"] = ph

        nodeDict["kind"] = thisNode
        if thisNode in FunctionDecl:
            FunDecIndex = thisIndex

        nodeDict["ancestors"] = ancestors
        nodeDict["FunDecIndex"] = FunDecIndex
    except:
        nodeDict["kind"] = "empty"
        thisNode = "empty"
        # return 0
    # if thisNode in operatorKind:
    if (thisNode in operatorKind) or (thisNode in funCallList):
        operatorList.append(thisIndex)

    if thisNode == "ReturnStmt":  # returnstmt dict initialization
        return_functionDecl[thisIndex] = FunDecIndex

        # if not (FunDecIndex in returnStmtDict.keys()):
        #     returnStmtDict[FunDecIndex] = [ ]
        # returnStmtDict[thisIndex] = {"fundecl": FunDecIndex, "endnode": -1}

        # if FunDecIndex in returnStmtDict:
        #     returnStmtDict[FunDecIndex].append(thisIndex)
        # else:
        #     returnStmtDict[FunDecIndex] = [thisIndex]

    try:
        nodeDict["id"] = js["id"]
    except:
        nodeDict["id"] = ""
    if (nodeDict["id"] in iddict) and (nodeDict["id"] != ""):
        iddict[nodeDict["id"]].append(thisIndex)
    if (not (nodeDict["id"] in iddict)) and (nodeDict["id"] != ""):
        iddict[nodeDict["id"]] = [thisIndex]
    # if thisNode == "BreakStmt" or thisNode == "ContinueStmt":
    #     ContinueBreak.append([thisIndex,thisNode,nodeDict["pos"],ControlSeq[:]])
    if addIntoFirstEle == 1 and (nodeDict["id"] in elementGlobalList):
        firsteleRecord.append(nodeDict["id"])
    if nodeDict["id"] in elementGlobalList:
        addIntoFirstEle = 0

    try:
        nodeDict["name"] = js["name"]
    except:
        try:
            nodeDict["name"] = js["value"]
        except:
            try:
                nodeDict["name"] = js["opcode"]
                # nodeDict["nodetype"] = "pureNode"
            except:
                nodeDict["name"] = ""
                # nodeDict["nodetype"] = "pureNode"
    if thisNode in TokenExcludeSet and nodeDict["name"] != "cin" and nodeDict["name"] != "cout":
        if thisNode == "CXXNullPtrLiteralExpr":
            nodeDict["name"] = "nullptr"
        if thisNode == "GNUNullExpr":
            nodeDict["name"] = "NULL"
        nodeDict["IsToken"] = "y"
        TokenList.append(thisIndex)

    elif thisNode == "MemberExpr" and inCXX == 1:  # 这个在外面的就不会被认成变量
        # elif thisNode == "MemberExpr" and (not (nodeDict["name"] in FuncDict)):  #这个会把非用户定义的库函数认成变量
        nodeDict["IsToken"] = "y"
        TokenList.append(thisIndex)
    else:
        nodeDict["IsToken"] = "n"

    # if thisNode in FunctionDecl:
    #     FuncDict[nodeDict["name"]]=thisIndex
    if thisNode in ConstantNodeList:
        if nodeDict["name"] in constantDict:
            constantDict[nodeDict["name"]].append(thisIndex)
        else:
            constantDict[nodeDict["name"]] = [thisIndex]

    try:
        tempType = js["type"]["qualType"]
    except:

        tempType = "void"
    tempTypeList = tempType.split(" ")
    tag = 0
    for splitType in tempTypeList:
        if splitType in orgDataType:
            tag = 1
            break
    if tag == 1:
        nodeDict["type"] = tempType
    else:
        nodeDict["type"] = "userDefine"
    try:
        nodeDict["valueCategory"] = js["valueCategory"]
    except:

        nodeDict["valueCategory"] = ""

    innerJs = []
    innerLen = 0

    # singlex = dict([])
    # # singlex["index"]=thisIndex
    # singlex["name"] = nodeDict["name"]
    # singlex["type"] = nodeDict["type"]
    # singlex["Index"] = nodeDict["Index"]
    # x.append(singlex)
    # singleEdge = dict([])
    # singleEdge["between"] = [parentIndex, thisIndex]
    # singleEdge["edgeType"] = "child"
    # edges.append(singleEdge)
    # if parentIndex!=-1:
    #     addEdge(parentIndex, thisIndex,"child")

    children = []
    nextAns = ancestors[:]
    nextAns.append(thisIndex)
    try:
        innerJs = innerJs + js["inner"]
        innerLen = len(innerJs)
    except:
        innerLen = len(innerJs)
    try:
        refarea = js["referencedDecl"]
        # print(refarea)
        if refarea["kind"] in TokenExcludeSet:
            innerJs = innerJs + [refarea]
        if refarea["kind"] == "FunctionDecl" and (not ("inner" in refarea.keys())):
            refarea["kind"] = "FunctionCallName"
            innerJs = innerJs + [refarea]
        innerLen = len(innerJs)
    except:
        innerLen = len(innerJs)
    if thisNode in FunctionDecl:
        FuncDictIndex.append(thisIndex)
        # FuncDict[nodeDict["name"] + str(innerLen)] = thisIndex
        # FuncDict[nodeDict["name"]] = thisIndex
        # if innerLen > 0:
        #     FuncDict[nodeDict["name"]+str(innerLen-1)]=thisIndex
        # else:
        #     FuncDict[nodeDict["name"]+str(0)]=thisIndex
    for i in range(0, innerLen):
        if thisNode == "ForStmt" or innerJs[i] != "{}":
            # if thisNode=="WhileStmt":
            #     print(thisIndex,i)
            currentIndex += 1
            children.append(currentIndex)
            ctrlTag = []
            if thisNode == "CXXRecordDecl":
                inCXX = 1
            buildTree(innerJs[i], currentIndex, nextAns[:], FunDecIndex, thisIndex, i, line, ctrlTag, inCXX,
                      addIntoFirstEle)

    nodeDict["children"] = children
    offspring = []
    for child in children:
        offspring.append(child)
        offspring = offspring + mySingleTree[child]["offspring"]
    nodeDict["offspring"] = offspring
    # nodeDict["nodeNum"]=-1
    mySingleTree[thisIndex] = nodeDict
    # x.append(dict({"Index":nodeDict["Index"],"kind":nodeDict["kind"],"name":nodeDict["name"],"type":nodeDict["type"]}))


def expressionTokenFind(rootIndex, tokenList=[]):
    if mySingleTree[rootIndex]["children"] == []:
        if mySingleTree[rootIndex]["IsToken"] == "y":
            tokenList.append(rootIndex)
        # return -1
    else:
        if mySingleTree[rootIndex]["IsToken"] == "y":
            tokenList.append(rootIndex)
        for child in mySingleTree[rootIndex]["children"]:
            expressionTokenFind(child, tokenList)
    return tokenList


def getSingleTokenInfo(index):
    tokenIndex = index
    tokenDict = dict([])
    if mySingleTree[tokenIndex]["name"] in ConstantNodeList:
        return 0, tokenDict
    tokenDict["name"] = mySingleTree[tokenIndex]["name"]
    tokenDict["index"] = tokenIndex
    tokenDict["controlSeq"] = mySingleTree[tokenIndex]["ControlSeq"]
    tokenDict["pos"] = mySingleTree[tokenIndex]["pos"]
    tokenDict["id"] = mySingleTree[tokenIndex]["id"]
    # if mySingleTree[tokenIndex]["kind"]:
    return 1, tokenDict


def addEdge(index1, index2, edgeType, atrribute=""):
    if edgeType[0:13] == "UserDefineFun":
        edgeType = "UserDefineFun"
    elif edgeType[0:6] == 'printf':
        edgeType = 'printf'
    elif edgeType[0:5] == 'scanf':
        edgeType = 'scanf'
    # elif edgeType[0] == "&":
    #     edgeType = "&"
    if (not (edgeType in edgeTypeList)):
        edgeTypeList.append(edgeType)
    if edgeType in ["ComputedFrom", "GuardedBy", "GuardedByNegation"] and \
            ((mySingleTree[index1]["kind"] in varTokenExclude) or (mySingleTree[index2]["kind"] in varTokenExclude)):
        return 0
    if index1 == -1 or index2 == -1:
        return 0
    singleEdge = dict([])
    singleEdge["between"] = [index1, index2]
    singleEdge["edgeType"] = edgeType
    # singleEdge["attribute"] = atrribute
    if singleEdge in edges:
        return 0
    #
    # if not (index1 in edgedX):
    #     edgedX.append(index1)
    # if not (index2 in edgedX):
    #     edgedX.append(index2)
    edges.append(singleEdge)


def getcombinSeq(varlist, ans):
    OpleftToRIGHT = ["[]", "()", ".", ".", "->", "/", "*", "%", "+", "-", "<<", ">>", ">", "<=", "<", "<=", "==", "!=",
                     "&", "^", "|", "&&", "||", ","]
    OprightToleft = ["?:", "=", "/=", "*=", "%=", "+=", "-=", "<<=", ">>=", "&=", "^=", "|="]
    seq = []
    children = mySingleTree[ans]["children"]
    childrenLen = len(children)

    if childrenLen == 0:
        return seq
    if mySingleTree[ans]["name"] in OpleftToRIGHT:
        for i in range(0, childrenLen):
            # for i in range(childrenLen - 1, -1, -1):
            if children[i] in varlist:
                seq.append([children[i], len(mySingleTree[children[i]]["ancestors"])])
            else:
                seq = seq + getcombinSeq(varlist, children[i])
    elif mySingleTree[ans]["name"] in OprightToleft:
        # for i in range(0, childrenLen):
        for i in range(childrenLen - 1, -1, -1):
            if children[i] in varlist:
                seq.append([children[i], len(mySingleTree[children[i]]["ancestors"])])
            else:
                seq = seq + getcombinSeq(varlist, children[i])
    else:
        varlisttemp = list(set(varlist).intersection(mySingleTree[ans]["offspring"]))
        for var in varlisttemp:
            seq.append([var, len(mySingleTree[var]["ancestors"])])
        seq = sorted(seq, key=(lambda x: x[1]))
        # return seq
    return seq


# def visitcfg(singleVarIndexset, xIndex_eleId, elerw, cfgOpSeq, elePoint,
#              visitedList, pathstr,
#              pre):  # elerw是字典{ele_id: {ele_id:【这条指令的对应的lastread】,w:[这条指令对应的lastwrite]，{x1（这条指令包含的token）}}}
#     if elePoint == '':
#         return 0
#     # print(iddict[elePoint][0])
#     varinEle = []
#     lastwrite = dict([])
#     lastread = dict([])
#     if elePoint in iddict:
#         varinEle = list(set(mySingleTree[iddict[elePoint][0]]["offspring"]).intersection(singleVarIndexset))
#     if varinEle != []:
#         # inEleIndex_Len =dict([])
#         # inEleIndex_Len = dict([])
#
#         varinEleLen = len(varinEle)
#         inEleIndex_Len = []
#
#         xlast = dict([])
#         # xlast={"r":{},"w":{}}
#         # if elerw[elePoint][elePoint]["w"]!={}:
#         #     for k in elerw[elePoint][elePoint]["w"].keys():
#         #         xlast["w"][pathstr] = elerw[elePoint][elePoint]["w"][k]
#         #
#         # if elerw[elePoint][elePoint]["r"]!={}:
#         #     for k in elerw[elePoint][elePoint]["r"].keys():
#         #         xlast["r"][pathstr] = elerw[elePoint][elePoint]["r"][k]
#         xlast["r"] = elerw[elePoint][elePoint]["r"]
#         xlast["w"] = elerw[elePoint][elePoint]["w"]
#         finalStateIndex = 0
#         if varinEleLen == 1:
#             xIndex_eleId[varinEle[0]].append(elePoint)
#             elerw[elePoint][varinEle[0]] = xlast
#             finalStateIndex = varinEle[0]
#         else:
#             for pervar in varinEle:
#                 xIndex_eleId[pervar].append(elePoint)
#                 # inEleIndex_Len[pervar] = len(mySingleTree[pervar]["ancestors"])
#                 # inEleIndex_Len.append([pervar, len(mySingleTree[pervar]["ancestors"])])
#             # inEleIndex_Len = sorted(inEleIndex_Len, key=(lambda x: x[1]))
#             # print(varinEle)
#             inEleIndex_Len = getcombinSeq(varinEle, iddict[elePoint][0])
#             inEleIndex_Len.reverse()
#             # print(inEleIndex_Len)
#             next = varinEleLen - 1
#             # state=[[]]*varinEleLen
#             elerw[elePoint][inEleIndex_Len[next][0]] = xlast
#             prenext = next
#             next = next - 1
#             while next >= 0:
#                 xlast = {"r": {}, "w": {}}
#                 xIndex = inEleIndex_Len[next][0]
#                 prexIndex = inEleIndex_Len[prenext][0]
#                 if xIndex_eleId[prexIndex][0] == "r":
#                     xlast["r"][pathstr] = prexIndex
#                     xlast["w"] = elerw[elePoint][prexIndex]["w"]
#
#                 elif xIndex_eleId[prexIndex][0] == "w":
#                     xlast["r"] = elerw[elePoint][prexIndex]["r"]
#                     xlast["w"][pathstr] = prexIndex
#
#                 elif xIndex_eleId[prexIndex][0] == "rw":
#                     xlast["r"][pathstr] = prexIndex
#                     xlast["w"][pathstr] = prexIndex
#
#                 elerw[elePoint][xIndex] = xlast
#                 next = next - 1
#                 prenext = prenext - 1
#             finalStateIndex = xIndex
#
#         if xIndex_eleId[finalStateIndex][0] == "r":
#             # lastread=[finalStateIndex]
#             # lastwrite=elerw[elePoint][finalStateIndex]["w"]
#             lastread = dict({elePoint: finalStateIndex})
#             for k in elerw[elePoint][finalStateIndex]["w"].keys():
#                 lastwrite[pathstr] = elerw[elePoint][finalStateIndex]["w"][k]
#             # lastwrite=elerw[elePoint][finalStateIndex]["w"]
#         elif xIndex_eleId[finalStateIndex][0] == "w":
#             for k in elerw[elePoint][finalStateIndex]["r"].keys():
#                 lastread[pathstr] = elerw[elePoint][finalStateIndex]["r"][k]
#             # lastread=elerw[elePoint][finalStateIndex]["r"]
#             lastwrite = dict({elePoint: finalStateIndex})
#             # lastread=elerw[elePoint][finalStateIndex]["r"]
#             # lastwrite=[finalStateIndex]
#         elif xIndex_eleId[finalStateIndex][0] == "rw":
#             lastread = dict({elePoint: finalStateIndex})
#             lastwrite = dict({elePoint: finalStateIndex})
#             # lastread=[finalStateIndex]
#             # lastwrite=[finalStateIndex]
#     else:
#         # xlast={"r":{},"w":{}}
#         if elerw[elePoint][elePoint]["w"] != {}:
#             for k in elerw[elePoint][elePoint]["w"].keys():
#                 lastwrite[pathstr] = elerw[elePoint][elePoint]["w"][k]
#         if elerw[elePoint][elePoint]["r"] != {}:
#             for k in elerw[elePoint][elePoint]["r"].keys():
#                 lastread[pathstr] = elerw[elePoint][elePoint]["r"][k]
#
#         # lastread = elerw[elePoint][elePoint]["r"]
#         # lastwrite = elerw[elePoint][elePoint]["w"]
#     sucs = cfgOpSeq[elePoint][1]
#     if sucs == []:
#         return 0
#     ##pathCheck: get the path has visited
#     # pathes = []
#     # for keys in elerw[elePoint][elePoint]["r"].keys():
#     #     pathes.append(keys)
#     ##pathCheck
#     for suc in sucs:
#
#         if elePoint in iddict:
#             pkey = pathstr + str(iddict[elePoint][0])
#         else:
#             pkey = pathstr + ""
#         if not (pathstr in elerw[suc][suc]["r"]):
#             # elerw[suc][suc]["r"][pathstr]=lastread
#             for k in lastread.keys():
#                 elerw[suc][suc]["r"][pkey] = lastread[k]
#         if not (pathstr in elerw[suc][suc]["w"]):
#             # elerw[suc][suc]["r"][pathstr] = lastwrite
#             for k in lastwrite.keys():
#                 elerw[suc][suc]["w"][pkey] = lastwrite[k]
#
#         if elerw[elePoint]["visitedSuc"].count(suc + pre) <= elerw[suc]["path"]:
#             elerw[elePoint]["visitedSuc"].append(suc + pre)
#             visitcfg(singleVarIndexset, xIndex_eleId, elerw, cfgOpSeq, suc, visitedList, pkey, elePoint)
def visitcfg(singleVarIndexset, xIndex_eleId, elerw, cfgOpSeq, elePoint,
             visitedList,pathstr,pre):  # elerw是字典{ele_id: {ele_id:【这条指令的对应的lastread】,w:[这条指令对应的lastwrite]，{x1（这条指令包含的token）}}}
    if elePoint=='':
        return 0
    # print(iddict[elePoint][0])
    varinEle = []
    lastwrite = dict([])
    lastread = dict([])
    if elePoint in iddict:
        varinEle = list(set(mySingleTree[iddict[elePoint][0]]["offspring"]).intersection(singleVarIndexset))
    if varinEle != []:
        # inEleIndex_Len =dict([])
        # inEleIndex_Len = dict([])

        varinEleLen = len(varinEle)
        inEleIndex_Len = []

        xlast = dict([])
        # xlast={"r":{},"w":{}}
        # if elerw[elePoint][elePoint]["w"]!={}:
        #     for k in elerw[elePoint][elePoint]["w"].keys():
        #         xlast["w"][pathstr] = elerw[elePoint][elePoint]["w"][k]
        #
        # if elerw[elePoint][elePoint]["r"]!={}:
        #     for k in elerw[elePoint][elePoint]["r"].keys():
        #         xlast["r"][pathstr] = elerw[elePoint][elePoint]["r"][k]
        xlast["r"]=elerw[elePoint][elePoint]["r"]
        xlast["w"]=elerw[elePoint][elePoint]["w"]
        finalStateIndex=0
        if varinEleLen == 1:
            xIndex_eleId[varinEle[0]].append(elePoint)
            elerw[elePoint][varinEle[0]]=xlast
            finalStateIndex=varinEle[0]
        else:
            for pervar in varinEle:
                xIndex_eleId[pervar].append(elePoint)
                # inEleIndex_Len[pervar] = len(mySingleTree[pervar]["ancestors"])
                # inEleIndex_Len.append([pervar, len(mySingleTree[pervar]["ancestors"])])
            # inEleIndex_Len = sorted(inEleIndex_Len, key=(lambda x: x[1]))
            # print(varinEle)
            inEleIndex_Len=getcombinSeq(varinEle,iddict[elePoint][0])
            inEleIndex_Len.reverse()
            # print(inEleIndex_Len)
            next = varinEleLen - 1
            # state=[[]]*varinEleLen
            elerw[elePoint][inEleIndex_Len[next][0]]=xlast
            prenext=next
            next=next-1
            while next >= 0:
                xlast = {"r":{},"w":{}}
                xIndex=inEleIndex_Len[next][0]
                prexIndex=inEleIndex_Len[prenext][0]
                if xIndex_eleId[prexIndex][0] == "r":
                    xlast["r"][pathstr] = prexIndex
                    xlast["w"] = elerw[elePoint][prexIndex]["w"]

                elif xIndex_eleId[prexIndex][0] == "w":
                    xlast["r"] = elerw[elePoint][prexIndex]["r"]
                    xlast["w"][pathstr] = prexIndex

                elif xIndex_eleId[prexIndex][0] == "rw":
                    xlast["r"][pathstr] = prexIndex
                    xlast["w"][pathstr] = prexIndex

                elerw[elePoint][xIndex]=xlast
                next=next-1
                prenext=prenext-1
            finalStateIndex=xIndex

        if xIndex_eleId[finalStateIndex][0]=="r":
            # lastread=[finalStateIndex]
            # lastwrite=elerw[elePoint][finalStateIndex]["w"]
            lastread=dict({elePoint:finalStateIndex})
            for k in elerw[elePoint][finalStateIndex]["w"].keys():
                lastwrite[pathstr] = elerw[elePoint][finalStateIndex]["w"][k]
            # lastwrite=elerw[elePoint][finalStateIndex]["w"]
        elif xIndex_eleId[finalStateIndex][0]=="w":
            for k in elerw[elePoint][finalStateIndex]["r"].keys():
                lastread[pathstr] = elerw[elePoint][finalStateIndex]["r"][k]
            # lastread=elerw[elePoint][finalStateIndex]["r"]
            lastwrite=dict({elePoint:finalStateIndex})
            # lastread=elerw[elePoint][finalStateIndex]["r"]
            # lastwrite=[finalStateIndex]
        elif xIndex_eleId[finalStateIndex][0]=="rw":
            lastread = dict({elePoint: finalStateIndex})
            lastwrite = dict({elePoint: finalStateIndex})
            # lastread=[finalStateIndex]
            # lastwrite=[finalStateIndex]
    else:
        # xlast={"r":{},"w":{}}
        if elerw[elePoint][elePoint]["w"]!={}:
            for k in elerw[elePoint][elePoint]["w"].keys():
                lastwrite[pathstr] = elerw[elePoint][elePoint]["w"][k]
        if elerw[elePoint][elePoint]["r"]!={}:
            for k in elerw[elePoint][elePoint]["r"].keys():
                lastread[pathstr] = elerw[elePoint][elePoint]["r"][k]

        # lastread = elerw[elePoint][elePoint]["r"]
        # lastwrite = elerw[elePoint][elePoint]["w"]
    sucs = cfgOpSeq[elePoint][1]
    if sucs == []:
        return 0
    ##pathCheck: get the path has visited
    # pathes = []
    # for keys in elerw[elePoint][elePoint]["r"].keys():
    #     pathes.append(keys)
    ##pathCheck
    for suc in sucs:
        # if suc =="0x7023c30":
        #     print("test")

        # if elePoint =="0x70256b8" and suc=="0x7025450":
        #     print(elerw[suc][suc]["r"].values())
            # pathlist=[]
            # for key in elerw[suc][suc]["r"].keys():
            #     pathlist=key.split("0x")
            #     pathstr1=""
            #     for item in pathlist:
            #         pathstr1+=item[5:]+'-'
                # print(elerw[suc][suc]["r"][key])
            # print(elerw[suc][suc]["r"],pathstr)
        # if not (lastread in elerw[suc][suc]["r"]):
        #     elerw[suc][suc]["r"].append(lastread)
        # if not (lastwrite in elerw[suc][suc]["w"]):
        #     elerw[suc][suc]["w"].append(lastwrite)
        # signal=0
        # pathstrLen=len(pathstr)
        # sucLen=len(suc)
        # elePointPos = pathstr.find(elePoint)
        # startPos=elePointPos+len(elePoint)
        # print(startPos)
        # for path in pathes:
        #     if path[startPos:startPos+sucLen]==suc:
        #         return


        if not (pathstr in elerw[suc][suc]["r"]) :
            # elerw[suc][suc]["r"][pathstr]=lastread
            for k in lastread.keys():
                elerw[suc][suc]["r"][pathstr+elePoint] = lastread[k]
        if not (pathstr in elerw[suc][suc]["w"]) :
            # elerw[suc][suc]["r"][pathstr] = lastwrite
            for k in lastwrite.keys():
                elerw[suc][suc]["w"][pathstr+elePoint] = lastwrite[k]
        # if not (suc in visitedList):
        # if not (suc in elerw[elePoint]["visitedSuc"]):
        # if elerw[elePoint]["visitedSuc"].count(suc)>2:
        #     elerw[elePoint]["visitedSuc"].append(suc)
        # if not ([suc,pre] in elerw[elePoint]["visitedSuc"]):
        #     elerw[elePoint]["visitedSuc"].append([suc,pre])
        # if elerw[elePoint]["visitedSuc"].count(suc+pre)<2:
        # print(elerw[suc]["path"])
        if elerw[elePoint]["visitedSuc"].count(suc + pre) <= elerw[suc]["path"]:

            elerw[elePoint]["visitedSuc"].append(suc+pre)
            visitcfg(singleVarIndexset, xIndex_eleId, elerw, cfgOpSeq, suc, visitedList, pathstr + elePoint,elePoint)
        # if visitedList.count(suc)<10:
        #     visitedList.append(suc)
        #     visitcfg(singleVarIndexset, xIndex_eleId,elerw, cfgOpSeq, suc, visitedList,pathstr+elePoint)


        # else:
        #     if pathstr in elerw[suc]

        # else:


def IsLeft(opIndex, TokenIndex):
    x = 0
    signal = 0
    if mySingleTree[opIndex]["children"] != []:
        for child in mySingleTree[opIndex]["children"]:
            if mySingleTree[child]['IsToken'] == 'y':
                signal = 1
                if child == TokenIndex:
                    x = 1

            else:
                x, signal = IsLeft(child, TokenIndex)
            if signal == 1:
                break
    return x, signal


# def getFunctionName(fIndex, inIndex):
#     # print(fIndex)
#     fname = ""
#     # if mySingleTree[fIndex]["name"] != "" and mySingleTree[fIndex]["name"] != False and  mySingleTree[fIndex]["name"] != True :
#     if mySingleTree[fIndex]["name"] != "" and type(mySingleTree[fIndex]["name"]) == str:
#         fname = mySingleTree[fIndex]["name"]
#     else:
#         child = -1
#         for child in mySingleTree[fIndex]["children"]:
#             fname = getFunctionName(child, inIndex)
#             if fname != "" and type(fname) == str:
#                 break
#         # if fname == False:
#         #     fname = mySingleTree[fIndex]["name"]
#         if child != -1 and fIndex == inIndex:
#             ans = mySingleTree[child]["ancestors"] + [inIndex]
#             ans.reverse()
#             for a in ans:
#                 if mySingleTree[a]["kind"] in funCallList:
#                     childLen = len(mySingleTree[fIndex]["children"])
#                     fname += str(childLen - 1)
#                     break;
#     return fname

def getFunctionName(fIndex, inIndex):
    # print(fIndex)
    fname = ""
    # if mySingleTree[fIndex]["name"] != "" and mySingleTree[fIndex]["name"] != False and  mySingleTree[fIndex]["name"] != True :
    if mySingleTree[fIndex]["name"] != "" and type(mySingleTree[fIndex]["name"]) == str:
        fname = mySingleTree[fIndex]["name"]
    else:
        # child = -1
        for child in mySingleTree[fIndex]["children"]:
            fname = getFunctionName(child, inIndex)
            if fname != "" and type(fname) == str:
                break
        # if fname == False:
        #     fname = mySingleTree[fIndex]["name"]
    if fIndex == inIndex:
        ans = mySingleTree[inIndex]["ancestors"] + [inIndex]
        ans.reverse()
        for a in ans:
            if mySingleTree[a]["kind"] in funCallList:
                childLen = len(mySingleTree[a]["children"])
                fname += str(childLen - 1)
                break;
    return fname


def checkFC(tokenIndex):  # 检查是否在cin和cout中
    ans = mySingleTree[tokenIndex]["ancestors"]
    for an in ans:
        if mySingleTree[an]["name"] == "cin" or mySingleTree[an]["name"] == "scanf":
            return "w"


def distanceCount(offs, searchAnsIndex):  # 计算offspring到ancestor的距离
    ans = mySingleTree[offs]["ancestors"]
    j = len(ans) - 1
    count = 1
    while ans[j] != searchAnsIndex:
        j = j - 1
        count = count + 1
    return count


def visitOpSubtree(Index, Endnode, writeOpIndex,
                   belongNodeNum):  # writeOpIndex记录writeOp的Idnex和操作符被赋值的节点所在children子树的编号,assignal 表示是不是从赋值那里传过来的，1表示是，0表示否
    global nodeNum
    global FuncDict
    global returnStmtDict
    global callFuncIndex
    global FuncParaIndex
    global callFuncOpDeclIndex
    addEdge(Index, Endnode, "write")
    edgeType = ""
    # splitChar=chr(5)
    splitChar = ""
    if mySingleTree[Index]["kind"] in funCallList:
        edgeType = "UserDefineFun"
        """
        record the called function's Endnode
        """
        fname = getFunctionName(Index, Index)
        if fname in FuncDict.keys():
            fundeclIndex = FuncDict[fname]
            callFuncOpDeclIndex.append([Index, fundeclIndex])
            if fundeclIndex in callFuncIndex.keys():
                callFuncIndex[fundeclIndex].append(Endnode)
            else:
                callFuncIndex[fundeclIndex] = [Endnode]


    elif mySingleTree[Index]["name"] != "":
        edgeType = mySingleTree[Index]["name"]
    else:

        edgeType = mySingleTree[Index]["kind"] + "edge"

    if mySingleTree[Index]["kind"] == "DeclStmt":
        child = mySingleTree[Index]["children"][0]
        # addEdge(child, Endnode, "ValueSource")
        # addEdge(Endnode, child, "ValueSource")
        addEdge(Endnode, child, "ValueSourceTotal")
        addEdge(child, Index, "read")
        childc = mySingleTree[child]["children"]
        i = 0
        for ci in childc:
            childOffSpring = mySingleTree[ci]["offspring"] + [ci]
            chidOffOp = list(set(childOffSpring).intersection(operatorList))

            if chidOffOp != []:
                nextOp = min(chidOffOp)
                addEdge(nodeNum, Endnode, edgeType + str(i))
                addEdge(nodeNum, Index, "read")
                visitOpSubtree(nextOp, nodeNum, writeOpIndex, belongNodeNum)
                nodeNum = nodeNum + 1
            else:
                childToken = list(set(childOffSpring).intersection(set(TokenList)))
                if childToken != []:
                    addEdge(childToken[0], Endnode, edgeType + str(i))

            i = i + 1

    elif mySingleTree[Index]["kind"] == "ReturnStmt":
        declFuncIndex = return_functionDecl[Index]
        rtoff = mySingleTree[Index]["offspring"]
        offOp = list(set(rtoff).intersection(operatorList))
        if offOp != []:
            next = min(offOp)
            # visitOpSubtree(next, nodeNum, writeOpIndex, belongNodeNum)
            visitOpSubtree(next, Endnode, writeOpIndex, belongNodeNum)
            if not (declFuncIndex in returnStmtDict.keys()):
                returnStmtDict[declFuncIndex] = [Endnode]
            else:
                returnStmtDict[declFuncIndex].append(Endnode)
        else:
            rtnToken = list(set(mySingleTree[Index]["offspring"] + [Index]).intersection(TokenList))
            if rtnToken != []:
                if not (declFuncIndex in returnStmtDict.keys()):
                    returnStmtDict[declFuncIndex] = [rtnToken[0]]
                else:
                    returnStmtDict[declFuncIndex].append(rtnToken[0])


    elif Index in writeOpIndex:
        if mySingleTree[Index]["kind"] == "DecompositionDecl":
            # nodeNum=nodeNum-1
            childrIndexes = mySingleTree[Index]["chilren"][1:]
            tempEndnodes = []
            for child in childrIndexes:  # (左边未必就只有一个，比如说数组，左边可能是a[i])
                interSec = list(set(TokenList).intersection(mySingleTree[child]['offspring']))
                # addEdge(mySingleTree[interSec[0]]["nodeNum"], Endnode, "ValuePartialSource")
                addEdge(interSec[0], Endnode, "ValuePartialSource")
                addEdge(interSec[0], Index, "read")
                # addEdge(interSec[0],Endnode,"ValuePartialSource")
                tempEndnodes = tempEndnodes + interSec
            # otherIndex=0
            rightOffstpring = mySingleTree[mySingleTree[Index]["children"][0]]["offspring"]
            tempEndnodes = sorted(tempEndnodes)
            opUnderRoot = sorted(list(set(rightOffstpring).intersection(operatorList)))
            tokensUnderRoot = set(rightOffstpring).intersection(TokenList)
            tokeUndersubOp = []
            for op in opUnderRoot:
                subopOffspring = mySingleTree[op]["offspring"]
                tokeUndersubOp += list(set(subopOffspring).intersection(TokenList))

            deComElePureToken = tokensUnderRoot - set(tokeUndersubOp)
            alignSeq = sorted(deComElePureToken + opUnderRoot)
            endnodeLen = len(tempEndnodes)
            for i in range(0, endnodeLen):
                if alignSeq[i] in opUnderRoot:#
                    addEdge(nodeNum, tempEndnodes[i], "ValuePartialSource")
                    # addEdge(nodeNum, tempEndnodes[i], "ValueSource")
                    addEdge(nodeNum, Index, "read")
                    addEdge(Index, tempEndnodes[i], "write")
                    visitOpSubtree(alignSeq[i], nodeNum, writeOpIndex, belongNodeNum)

                    nodeNum = nodeNum + 1

                else:
                    addEdge(alignSeq[i], tempEndnodes[i], "ValuePartialSource")
                    # addEdge(alignSeq[i], tempEndnodes[i], "ValueSource")
                    addEdge(alignSeq[i], Index, "read")
                    addEdge(Index, tempEndnodes[i], "write")
                addEdge(tempEndnodes[i], Endnode, "ValuePartialSource")
                # addEdge(tempEndnodes[i], Endnode, "ValueSource")
                addEdge(tempEndnodes[i], Index, "read")
            # getSq(deComElePureToken,opUnderRoot)
        elif mySingleTree[Index]["kind"] == "UnaryOperator":
            if edgeType == '-':
                edgeType = 'Neg'
            elif edgeType == '&':
                edgeType = 'Address'
            ThisOpSpring = mySingleTree[Index]["offspring"]
            HasOp = list(set(ThisOpSpring).intersection(operatorList))
            if HasOp == []:
                tokens = list(set(mySingleTree[Index]["offspring"]).intersection(TokenList))[0]

                addEdge(tokens, Endnode, edgeType)
                addEdge(tokens, Index, "read")
                # addEdge(Endnode, tokens, "ValueSource")
                addEdge(Endnode, tokens, "ValueSourceTotal")
                addEdge(Endnode, Index, "read")
                addEdge(Index, tokens, "write")
            else:  # 说明是数组
                arrayNode = min(list(set(ThisOpSpring).intersection(TokenList)))
                # addEdge(Endnode,arrayNode,"ValuePartialSource")
                # addEdge(Endnode, mySingleTree[arrayNode]["nodeNum"], "ValuePartialSource")
                addEdge(Endnode, arrayNode, "ValuePartialSource")
                addEdge(Endnode, Index, "read")
                addEdge(Index, arrayNode, "write")
                # addEdge(nodeNum, Endnode, "ValueSource")
                addEdge(nodeNum, Endnode, "ValueSourceTotal")
                addEdge(nodeNum, Index, "read")
                NextOP = min(HasOp)
                # addEdge(nodeNum, belongNodeNum, "belongTo")

                # x.append(dict({"ID": nodeNum, "kind": "temp", "type": mySingleTree[Index]["type"], "name": ""}))
                visitOpSubtree(NextOP, nodeNum, writeOpIndex, belongNodeNum)
                nodeNum = nodeNum + 1
        else:  # 等于的情况
            tempEndnodes = -1
            # leftHasOp=list(set(mySingleTree[Index]["offspring"]).intersection(operatorList))
            ministChildToken = min(list(set(mySingleTree[Index]["offspring"]).intersection(TokenList)))
            # addEdge(Endnode,mySingleTree[ministChildToken]["nodeNum"],"ValueSource")
            addEdge(Endnode, ministChildToken, "ValueSourceTotal")
            # addEdge(Endnode, Index, "read")
            # addEdge(Index, ministChildToken, "write")
            leftIndex = mySingleTree[Index]["children"][0]

            leftHasOp = list(set(mySingleTree[leftIndex]["offspring"] + [leftIndex]).intersection(operatorList))
            if leftHasOp == []:
                # try:
                #     tempEndnodes = list(set(mySingleTree[leftIndex]["offspring"]+[leftIndex]).intersection(TokenList))[0]
                # except:
                #     print(mySingleTree[leftIndex])
                # addEdge(tempEndnodes,Endnode,"ValueSource")
                tempEndnodes = list(set(mySingleTree[leftIndex]["offspring"] + [leftIndex]).intersection(TokenList))
                if tempEndnodes != []:
                    # addEdge(mySingleTree[tempEndnodes[0]]["nodeNum"], Endnode, "ValueSource")
                    addEdge(tempEndnodes[0], Endnode, "ValuePartialSource")
                    addEdge(tempEndnodes[0], Index, "read")
            else:
                tempEndnodes = Endnode
                nextOp = min(leftHasOp)
                addEdge(nodeNum, Endnode, "ValuePartialSource")
                # addEdge(nodeNum, belongNodeNum, "belongTo")
                addEdge(nodeNum, Index, "read")
                # x.append(dict({"ID": nodeNum, "kind": "temp", "type": mySingleTree[Index]["type"], "name": ""}))
                visitOpSubtree(nextOp, nodeNum, writeOpIndex, belongNodeNum)
                nodeNum = nodeNum + 1

            # edgePair.append([tempEndnodes,Endnode,"ValueSource"])
            # addEdge(mySingleTree[tempEndnodes]["nodeNum"],Endnode,"ValueSource")
            rightIndex = mySingleTree[Index]["children"][1]
            rightHandOp = list(set(mySingleTree[rightIndex]["offspring"] + [rightIndex]).intersection(operatorList))
            if rightHandOp == []:
                token = list(set(mySingleTree[rightIndex]["offspring"] + [rightIndex]).intersection(TokenList))
                # edgePair.append([token,tempEndnodes,"ValueSource"])
                # addEdge(mySingleTree[token]["nodeNum"],tempEndnodes,"ValueSource")
                if token != []:
                    addEdge(token[0], Endnode, "ValuePartialSource")
                    addEdge(token[0], Index, "read")
                    # addEdge(mySingleTree[token[0]]["nodeNum"], Endnode, "ValueSource")
            else:
                nextVisitIndex = min(rightHandOp)

                # edgePair.append([nodeNum,Endnode,"ValueSource"])
                addEdge(nodeNum, Endnode, "ValuePartialSource")
                # addEdge(nodeNum, belongNodeNum, "belongTo")
                addEdge(nodeNum, Index, "read")
                # x.append(dict({"ID": nodeNum, "kind": "temp", "type": mySingleTree[Index]["type"],"name":""}))

                # visitOpSubtree(nextVisitIndex, nodeNum, writeOpIndex, belongNodeNum)
                # nodeNum = nodeNum + 1
                nodeNum = nodeNum + 1
                visitOpSubtree(nextVisitIndex, nodeNum - 1, writeOpIndex, belongNodeNum)


    else:
        Currentchildren = mySingleTree[Index]["children"]
        i = 0
        # childCount=0
        # addEdge(nodeNum, Endnode, edgeType)
        # addEdge(nodeNum, Index, "read")
        for child in Currentchildren:
            childOffSpring = mySingleTree[child]["offspring"] + [child]
            chidOffOp = list(set(childOffSpring).intersection(operatorList))
            # if child in operatorList:
            if chidOffOp != []:
                nextOp = min(chidOffOp)
                addEdge(nodeNum, Endnode, edgeType + str(i))
                # addEdge(nodeNum, Endnode, edgeType)
                addEdge(nodeNum, Index, "read")
                if (mySingleTree[Index]["kind"] in funCallList) and (getFunctionName(Index, Index) in FuncDict):
                    callFunName = getFunctionName(Index, Index)
                    if len(FuncParaIndex[callFunName]) > 0 and i - 1 >= 0:
                        addEdge(nodeNum, FuncParaIndex[callFunName][i - 1], "FormalArgName")

                    # paraNum = len(mySingleTree[Index]["children"]-1)
                    # funcDeclIndex = FuncDict[getFunctionName(Index)+str(paraNum)]
                    # funcDeclIndex = FuncDict[getFunctionName(Index, Index)]
                    # if mySingleTree[funcDeclIndex]["children"] != []:
                    #     # print("*********************", i, "****************")
                    #     addEdge(nodeNum, mySingleTree[funcDeclIndex]["children"][i-1], "FormalArgName")

                    # functionName = getFunctionName(Index)
                    # fname = getFunctionName(mySingleTree[ansIndex]["children"][0])
                    # if functionName in FuncDict:

                visitOpSubtree(nextOp, nodeNum, writeOpIndex, belongNodeNum)
                nodeNum = nodeNum + 1
            else:

                childToken = list(set(childOffSpring).intersection(set(TokenList)))
                if childToken != []:
                    addEdge(childToken[0], Endnode, edgeType + str(i))
                    # addEdge(childToken[0], Endnode, edgeType)
                    addEdge(childToken[0], Index, "read")

                    if (mySingleTree[Index]["kind"] in funCallList) and (getFunctionName(Index, Index) in FuncDict):
                        callFunName = getFunctionName(Index, Index)
                        if len(FuncParaIndex[callFunName]) > 0 and i - 1 >= 0:
                            addEdge(childToken[0], FuncParaIndex[callFunName][i - 1], "FormalArgName")

                    # if (mySingleTree[Index]["kind"] in funCallList) and (getFunctionName(Index, Index) in FuncDict):
                    #     # paraNum = len(mySingleTree[Index]["children"] - 1)
                    #     # funcDeclIndex = FuncDict[getFunctionName(Index) + str(paraNum)]
                    #     funcDeclIndex = FuncDict[getFunctionName(Index, Index)]
                    #     if mySingleTree[funcDeclIndex]["children"] != []:
                    #         # print("*********************", i ,"****************")
                    #     # if i < len(mySingleTree[funcDeclIndex]["children"]):
                    #         addEdge(childToken[0], mySingleTree[funcDeclIndex]["children"][i-1], "FormalArgName")
            i = i + 1

    # elif mySingleTree[Index]["kind"] in funCallList:


def getOpSeq(Oplist, ansTreeIndex,
             ansListIndex):  # 其中这个Oplist是只描述element下操作符的树型关系的字典其中包括{OP的index，op的孩子op，但可能并不一定是ast上的孩子关系},ans表示在opList下当前节点的索引（不是ast上的索引）
    OpleftToRIGHT = ["[]", "()", ".", ".", "->", "/", "*", "%", "+", "-", "<<", ">>", ">", "<=", "<", "<=", "==", "!=",
                     "&", "^", "|", "&&", "||", ","]
    OprightToleft = ["?:", "=", "/=", "*=", "%=", "+=", "-=", "<<=", ">>=", "&=", "^=", "|="]
    seq = []
    children = Oplist[ansListIndex]["children"]
    childrenLen = len(children)

    if childrenLen == []:
        # return seq
        return seq + [ansTreeIndex]

    if mySingleTree[ansTreeIndex]["name"] in OprightToleft:
        for i in range(childrenLen - 1, -1, -1):
            # if Oplist[i]["children"] != []:
            if Oplist[children[i]]["children"] != []:
                seq = seq + getOpSeq(Oplist, Oplist[children[i]]["Index"], children[i])
            else:
                seq = seq + [Oplist[children[i]]["Index"]]
        seq = seq + [ansTreeIndex]
    # elif mySingleTree[ansTreeIndex]["name"] in OpleftToRIGHT:
    else:
        for i in range(0, childrenLen):
            # if Oplist[i]["children"] != []:
            if Oplist[children[i]]["children"] != []:
                seq = seq + getOpSeq(Oplist, Oplist[children[i]]["Index"], children[i])
            else:
                seq = seq + [Oplist[children[i]]["Index"]]
            # seq = seq + [Oplist[children[i]]["Index"]]
        seq = seq + [ansTreeIndex]

    return seq


def getOpList(opList, oplistIndexDict):  # oplistIndexDict 记录的是oplist 在mysingletree中的Index 和 在oplist中的索引的关系
    opListLen = len(opList)
    for i in range(0, opListLen):
        ans = mySingleTree[opList[i]["Index"]]["ancestors"][:]
        ans.reverse()
        for a in ans:
            if a in oplistIndexDict.keys():
                alistPos = oplistIndexDict[a]
                opList[alistPos]["children"].append(i)
                break


def InControl(eleIndex):
    # control = ["IfStmt","SwitchStmt","ForStmt","WhileStmt","DoStmt"]
    iws = ["IfStmt", "SwitchStmt", "WhileStmt"]
    ans = mySingleTree[eleIndex]["ancestors"]
    for a in ans:
        if mySingleTree[a]["kind"] in iws and mySingleTree[a]["children"][0] == eleIndex:
            return [mySingleTree[a]["kind"], a]  # eleIndex is in the condition; part

        elif mySingleTree[a]["kind"] == "DoStmt" and mySingleTree[a]["children"][1] == eleIndex:
            return ["DoStmt", a]

        elif mySingleTree[a]["kind"] == "ForStmt" and mySingleTree[a]["children"][2] == eleIndex:
            return ["ForStmt", a]

        # if mySingleTree[a]["kind"] in iws and mySingleTree[a]["children"][0] == eleIndex:
        #     return [mySingleTree[a]["kind"],1] # eleIndex is in the condition; part
        # elif (mySingleTree[a]["kind"] in iws) and (eleIndex in  mySingleTree[mySingleTree[a]["children"][1]]["offspring"]):
        #     return [mySingleTree[a]["kind"],2]  #eleIndex is in the componet part
        # elif mySingleTree[a]["kind"] == "DoStmt" and mySingleTree[a]["children"][1] == eleIndex:
        #     return ["DoStmt", 1]
        # elif (mySingleTree[a]["kind"] == "DoStmt") and (eleIndex in mySingleTree[mySingleTree[a]["children"][1]]["offpring"]):
        #     return ["DoStmt", 2]
        # elif mySingleTree[a]["kind"] == "ForStmt" and mySingleTree[a]["children"][2] == eleIndex:
        #     return ["ForStmt", 1]
        # elif mySingleTree[a]["kind"] == "ForStmt" and \
        #         ((eleIndex in (mySingleTree[mySingleTree[a]["children"][3]]["offpring"] + mySingleTree[a]["children"][3])) or
        #          (eleIndex in mySingleTree[mySingleTree[a]["children"][4]]["offpring"])):
        #     return ["ForStmt", 2]
    return -1


def defaultSwitchSeq(Index):
    ans = mySingleTree[Index]["ancestors"][:]
    ans.reverse()

    for a in ans:
        if mySingleTree[a]["kind"] == "SwitchStmt":
            return 1
        if mySingleTree[a]["kind"] == "DefaultStmt":
            return 0

    return -1


def buildGraph(cfgOpSeq, functionIDStart):
    global mySingleTree
    global FuncDict
    global FuncDictIndex
    global TokenList
    global edges
    global elementGlobalList
    global constantList
    global nodeNumIndexDic
    global nodeNum
    global constantDict
    global callFuncIndex
    global returnStmtDict
    global loopCondition
    global FuncParaIndex
    global callFuncOpDeclIndex
    # tempElementGlobalList
    """
    get the functions decl
    """
    for fun in FuncDictIndex:
        funChildren = mySingleTree[fun]["children"]
        if funChildren != [] and mySingleTree[funChildren[-1]]["kind"] == "CompoundStmt":
            paraCount = 0
            paraIndexes = []
            for child in funChildren:
                if mySingleTree[child]["kind"] == "ParmVarDecl":
                    paraIndexes.append(child)
                    paraCount += 1
            funName = mySingleTree[fun]["name"]
            FuncDict[funName + str(paraCount)] = fun
            FuncParaIndex[funName + str(paraCount)] = paraIndexes

    VarTokenDict = dict([])
    TokenListLen = len(TokenList)
    writeOpIndex = []
    # singleEdge = dict([])
    ###add NodeNum and child edge
    addChildList = []
    for ele in firsteleRecord:
        eleIndex = iddict[ele][0]
        addChildList.append(eleIndex)
        addChildList = addChildList + mySingleTree[eleIndex]["ancestors"]
    addChildList = list(set(addChildList))
    ###所有树上可用的节点编号
    CountNumList = addChildList + TokenList
    count = 0
    # for node in CountNumList:
    #     mySingleTree[node]["nodeNum"]=count
    #     # x.append(dict({"ID": count, "kind": mySingleTree[node]["kind"], "type": mySingleTree[node]["type"],"name":mySingleTree[node]["name"]}))
    #     nodeNumIndexDic[count]=node
    #     count=count+1
    # nodeNum=count
    for eleIndex in addChildList:
        if eleIndex == -1:
            continue
        childList = mySingleTree[eleIndex]["children"]
        for child in childList:
            if child in addChildList:
                # addEdge(mySingleTree[eleIndex]["nodeNum"],mySingleTree[child]["nodeNum"],"child","")
                addEdge(eleIndex, child, "child", "")
    for key in constantDict.keys():
        valList = constantDict[key]
        srNodeNum = valList[0]
        for nd in valList[1:]:
            addEdge(srNodeNum, nd, "ValueSourceTotal", "")
        # valLen = len(valList)
        # for j in range(1,valLen):
        #     addEdge(valList[j], valList[0], "ValueSource", "")
    var_index_rw = dict([])
    for i in range(0, TokenListLen):
        tokenIndex = TokenList[i]
        tokenDict = dict([])

        tokenDict["Index"] = tokenIndex
        tokenDict["rw"] = "r"
        if checkFC(tokenIndex) == "w":
            tokenDict["rw"] = "w"

        ansList = mySingleTree[tokenIndex]["ancestors"]
        anslistIndex = len(ansList) - 1
        if mySingleTree[tokenIndex]["kind"]=="VarDecl" or mySingleTree[tokenIndex]["kind"]=="CXXCtorInitializer" or mySingleTree[tokenIndex]["kind"]=="EnumConstantDecl":
            if mySingleTree[tokenIndex]["children"]!=[]:
                computedFromListIndex = expressionTokenFind(mySingleTree[tokenIndex]["children"][0],[])
                # for nodei in computedFromListIndex:
                #     addEdge(tokenIndex, nodei, "ComputedFrom")
                if computedFromListIndex!=[]:
                    tokenDict["rw"] = "w"
        while anslistIndex >= 0:
            ansIndex = ansList[anslistIndex]
            nodetype = mySingleTree[ansIndex]["kind"]
            if nodetype in computedFrom:  ##除了VarDecl之外的所有anscestors
                computedFromListIndex = []
                if nodetype == "DecompositionDecl" and \
                        (((anslistIndex + 1 <= len(ansList) - 1) and
                          mySingleTree[ansList[anslistIndex + 1]]["name"] == "BindingDecl")):
                    computedFromListIndex = expressionTokenFind(mySingleTree[ansIndex]["children"][0], [])
                    tokenDict["rw"] = "w"
                    writeOpIndex.append(ansIndex)
                    break
                elif nodetype == "CompoundAssignOperator" and IsLeft(ansIndex, tokenIndex)[0] == 1:
                    computedFromListIndex = expressionTokenFind(mySingleTree[ansIndex]["children"][1], [])
                    computedFromListIndex.append(tokenIndex)
                    tokenDict["rw"] = "rw"
                    writeOpIndex.append(ansIndex)
                    break
                elif nodetype == "UnaryOperator" and (
                        mySingleTree[ansIndex]["name"] == "++" or mySingleTree[ansIndex]["name"] == "--") and \
                        IsLeft(ansIndex, tokenIndex)[0] == 1:
                    computedFromListIndex.append(tokenIndex)
                    tokenDict["rw"] = "rw"
                    writeOpIndex.append(ansIndex)
                    break
                elif nodetype == "BinaryOperator" and mySingleTree[ansIndex]["name"] == "=" and \
                        IsLeft(ansIndex, tokenIndex)[0] == 1:
                    computedFromListIndex = expressionTokenFind(mySingleTree[ansIndex]["children"][1], [])
                    tokenDict["rw"] = "w"
                    writeOpIndex.append(ansIndex)
                    break

                # elif nodetype=="CXXCtorInitializer":这种类型的文件删除掉
            anslistIndex = anslistIndex - 1
        tokenID = mySingleTree[tokenIndex]["id"]
        # if not (mySingleTree[tokenIndex]["kind"] in varTokenExclude):
        var_index_rw[tokenIndex] = tokenDict['rw']
        if tokenID in VarTokenDict:
            VarTokenDict[tokenID].append(tokenDict)
        else:
            VarTokenDict[tokenID] = [tokenDict]
    varTokenList = list(VarTokenDict.values())
    for singleVarList in varTokenList:
        if mySingleTree[singleVarList[0]["Index"]]["kind"] in varTokenExclude:
            continue
        elerw = dict([])
        for cfgkey in cfgOpSeq.keys():
            elerw[cfgkey] = {cfgkey: {"r": dict([]), "w": dict([])}, "visitedSuc": [], "path": cfgOpSeq[cfgkey][2]}
        # newrwList=rwList[:]
        singleVarListLen = len(singleVarList)
        # singleVarList = sorted(TokensInfo, key=operator.itemgetter('pos'))  ##pos需要调整成4位行号加上4位列号
        singleVarIndexset = []
        varrwInfo = dict([])
        for si in range(0, singleVarListLen):
            varrwInfo[singleVarList[si]["Index"]] = [singleVarList[si]["rw"]]  # 其中一个为读，一个为写的last
            # varrwInfo[singleVarList[si]["Index"]] = {"r": dict([]), "w": dict([]),
            #                                          "state": singleVarList[si]["rw"]}  # 其中一个为读，一个为写的last
            singleVarIndexset.append(singleVarList[si]["Index"])
        singleVarIndexset = set(singleVarIndexset)

        # 找cfg根节点的function所对应的Index
        functionIndexList = []
        functionIndexListLen = 0
        for id in functionIDStart.keys():
            if id != '':
                functionIndexList.append(iddict[id][0])
                functionIndexListLen += 1
        function_exist_x = []
        for varIndex in varrwInfo.keys():
            interset = list(set(mySingleTree[varIndex]["ancestors"]).intersection(set(functionIndexList)))
            if interset != []:
                for ele in interset:
                    if not (ele in function_exist_x):
                        function_exist_x.append(ele)
            if len(function_exist_x) == functionIndexListLen:
                break
        for fi in function_exist_x:
            elePoint = functionIDStart[mySingleTree[fi]["id"]]
            visitcfg(singleVarIndexset, varrwInfo, elerw, cfgOpSeq, elePoint, [], "", "")
        # print(varrwInfo)
        for perIndex in varrwInfo.keys():
            # if var_index_rw[perIndex] == 'w':
            #     continue
            # print("sssss")
            wlist = []
            if len(varrwInfo[perIndex]) > 1:
                wlist = list(elerw[varrwInfo[perIndex][1]][perIndex]["w"].values())
            else:
                continue
            # print("heee")
            wlist = list(set(wlist))
            if len(wlist) > 1:
                for w in wlist:
                    addEdge(w, perIndex, "potentialSource")
            if len(wlist) == 1:
                addEdge(wlist[0], perIndex, "ValueSourceTotal")
    elementGlobalList = firsteleRecord
    elementFirstLastOp = dict([])
    elementIDIdx = dict([])
    elementIdxID = dict([])
    # preNext = []
    for element in elementGlobalList:
        elementIndex = iddict[element][0]
        elementIDIdx[element] = elementIndex
        elementIdxID[elementIndex] = element
        nodeNum = nodeNum + 1
        # addEdge(nodeNum - 1, elementIndex, "belongTo")
        # x.append(dict({"ID": nodeNum - 1, "kind": "temp", "type": mySingleTree[eleIndex]["type"],
        #                "name": ""}))
        visitOpSubtree(elementIndex, nodeNum - 1, writeOpIndex, elementIndex)

        eleChildrenOp = list(set(mySingleTree[elementIndex]["offspring"]).intersection(operatorList))
        if eleChildrenOp != []:
            eleChildrenOp += [elementIndex]
            opListCount = 0
            oplist = []
            oplistIndexDict = dict([])
            for i in range(0, len(eleChildrenOp)):
                oplistIndexDict[eleChildrenOp[i]] = i
                oplist.append({"Index": eleChildrenOp[i], "children": []})

            getOpList(oplist, oplistIndexDict)
            seq = getOpSeq(oplist, elementIndex, oplistIndexDict[elementIndex])
            seqLen = len(seq)
        else:
            seq = [elementIndex]
        seqLen = len(seq)
        if seqLen > 1:
            for i in range(0, seqLen - 1):
                addEdge(seq[i], seq[i + 1], "next")
        elementFirstLastOp[element] = [seq[0], seq[-1]]  # connect the op inner element
        # preNext =[s]
    # nextCount = 0
    # for e in edges:
    #     if e['edgeType'] in ['next']:
    #         # cfge.append([e['between'][0], e['between'][1]])
    #         nextCount += 1
    #         print([e['between'][0], e['between'][1]], e['edgeType'])
    # print(nextCount)
    for element in elementGlobalList:  # connect the op between element
        # control = ["IfStmt","SwitchStmt","ForStmt","WhileStmt","DoStmt"]
        loop = ["ForStmt", "WhileStmt", "DoStmt"]
        elementIndex = iddict[element][0]
        locatedIn = InControl(elementIndex)

        if locatedIn != -1:
            locatedType = locatedIn[0]
            locatedIndex = locatedIn[1]
            if locatedType in loop:
                loopCondition.append(elementFirstLastOp[element][0])
            for suc in cfgOpSeq[element][1]:
                if not (suc in iddict.keys()):
                    continue
                sucIndex = iddict[suc][0]
                if suc in iddict.keys():
                    # if suc in elementGlobalList:
                    if locatedType == "IfStmt" and \
                            (sucIndex in (mySingleTree[mySingleTree[locatedIndex]["children"][1]]["offspring"] +
                                          [mySingleTree[locatedIndex]["children"][1]])):
                        if suc in elementFirstLastOp.keys():
                            addEdge(elementFirstLastOp[element][1], elementFirstLastOp[suc][0], "trueNext")
                        else:
                            addEdge(elementFirstLastOp[element][1], iddict[suc][0], "trueNext")
                    elif locatedType == "SwitchStmt" and \
                            (sucIndex in (mySingleTree[mySingleTree[locatedIndex]["children"][1]]["offspring"]) + [mySingleTree[locatedIndex]["children"][1]]) and \
                            not (defaultSwitchSeq(sucIndex) == 1):
                        if suc in elementFirstLastOp.keys():
                            addEdge(elementFirstLastOp[element][1], elementFirstLastOp[suc][0], "trueNext")
                        else:
                            addEdge(elementFirstLastOp[element][1], iddict[suc][0], "trueNext")
                    elif locatedType == "WhileStmt" and \
                            (sucIndex in (mySingleTree[mySingleTree[locatedIndex]["children"][1]]["offspring"]+ [mySingleTree[locatedIndex]["children"][1]])):
                        if suc in elementFirstLastOp.keys():
                            addEdge(elementFirstLastOp[element][1], elementFirstLastOp[suc][0], "trueNext")
                        else:
                            addEdge(elementFirstLastOp[element][1], iddict[suc][0], "trueNext")
                    elif locatedType == "DoStmt" and \
                            (sucIndex in (mySingleTree[mySingleTree[locatedIndex]["children"][0]]["offspring"] + [mySingleTree[locatedIndex]["children"][0]])):
                        if suc in elementFirstLastOp.keys():
                            addEdge(elementFirstLastOp[element][1], elementFirstLastOp[suc][0], "trueNext")
                        else:
                            addEdge(elementFirstLastOp[element][1], iddict[suc][0], "trueNext")
                    elif locatedType == "ForStmt" and \
                            ((sucIndex in (mySingleTree[mySingleTree[locatedIndex]["children"][3]]["offspring"]) + [mySingleTree[locatedIndex]["children"][3]]) or
                             (sucIndex in (mySingleTree[mySingleTree[locatedIndex]["children"][4]]["offspring"] + [mySingleTree[locatedIndex]["children"][4]]))):
                        if suc in elementFirstLastOp.keys():
                            addEdge(elementFirstLastOp[element][1], elementFirstLastOp[suc][0], "trueNext")
                        else:
                            addEdge(elementFirstLastOp[element][1], iddict[suc][0], "trueNext")
                    else:
                        if suc in elementFirstLastOp.keys():
                            addEdge(elementFirstLastOp[element][1], elementFirstLastOp[suc][0], "falseNext")
                        else:
                            addEdge(elementFirstLastOp[element][1], iddict[suc][0], "falseNext")
                """
                暂时不考虑loop，后面可以把指向条件的第一个操作符的且自己又在循环中的操作符所连接的边改成loop

                """
                # if  in loop:  ##看看是不是指向循环的第一句

                # addge(elementIndex, iddict[suc][0], "next", "")
        else:
            for suc in cfgOpSeq[element][1]:
                sucs = suc
                # print("suc")
                sucList = []
                while not (sucs in elementGlobalList) and cfgSeq[sucs][1] != [] and (not (cfgSeq[sucs][1] in sucList)):
                    sucs = cfgSeq[sucs][1][0]
                    sucList.append(cfgSeq[sucs][1])

                if sucs in elementGlobalList:
                    addEdge(elementFirstLastOp[element][1], elementFirstLastOp[sucs][0], "next")

                # if suc in elementGlobalList:
                #     # print("ele", elementFirstLastOp[element][1], element)
                #     # print(suc)
                #     # print(elementFirstLastOp[suc][0])
                #     addEdge(elementFirstLastOp[element][1], elementFirstLastOp[suc][0], "next")
                # #NEW
                # else:
                #     sucs = suc
                #     print("suc")
                #     sucList = []
                #     while not(sucs in elementGlobalList) and cfgSeq[sucs][1] != [] and (not (cfgSeq[sucs][1] in sucList)):
                #         # print(cfgSeq[sucs])
                #         sucs = cfgSeq[sucs][1][0]
                #         sucList.append(cfgSeq[sucs][1])
                #     # print("rrr")
                #     if suc in elementGlobalList:
                #         addEdge(elementFirstLastOp[element][1], elementFirstLastOp[sucs][0], "next")

        # for suc in cfgSeq[element][1]:
        #     # if (suc in iddict) and (mySingleTree[iddict[suc][0]]["nodeNum"]!=-1):
        #     if suc in iddict:
        #         addEdge(elementIndex, iddict[suc][0], "next", "")
        # operands=list(set(TokenList).intersection(set(mySingleTree[elementIndex]["offspring"])))
        # for operandIndex in operands:
        #     addEdge(operandIndex, elementIndex, "belongTo", "")

    """
    add return dfg edges
    """

    for call in callFuncIndex.keys():
        callEndnodes = callFuncIndex[call]
        if call in returnStmtDict.keys():
            returnNodes = returnStmtDict[call]
            for callnode in callEndnodes:
                for rtnnode in returnNodes:
                    addEdge(rtnnode, callnode, "returnTo")

        #
        # for rtn in returnStmtDict.keys():
        #     rtnEndnode = returnStmtDict[rtn]
        #     edges(rtnEndnode, callEndnode, "Return")
    """
    add return and call cfg edges
    """
    funFirstLastOp = dict([])
    for fun in FuncDict.values():
        funFirstLastOp[fun] = {"first": [], "last": []}
        funcOp = list(set(mySingleTree[fun]["offspring"]).intersection(elementIDIdx.values()))
        """
        pick the minist as start, 最小的一定是开始的地方，但是最大的未必就是结束的唯一地方
        """
        if funcOp != []:
            funFirstLastOp[fun]["first"].append(
                elementFirstLastOp[mySingleTree[min(funcOp)]["id"]][0])  # put the fist op in funFirstLastOp
        for op in funcOp:

            # if cfgOpSeq[elementIdxID[op]][0] == []: #pre==[], is the start
            #     funFirstLastOp[fun]["first"].append(elementFirstLastOp[mySingleTree[op]["id"]][0]) #put the fist op in funFirstLastOp
            if cfgOpSeq[elementIdxID[op]][1] == []:
                funFirstLastOp[fun]["last"].append(elementFirstLastOp[mySingleTree[op]["id"]][1])
    for call in callFuncOpDeclIndex:
        for pre in funFirstLastOp[call[1]]["first"]:
            addEdge(call[0], pre, "callNext")
        for ls in funFirstLastOp[call[1]]["last"]:
            addEdge(ls, call[0], "ReturnNext")

        # nodeNum = nodeNum + 1


def cfgsequenceGeneration(cfgfilepath):
    # open("")
    global elementGlobalList
    cfgcontent = open(cfgfilepath, "r").read()
    while cfgcontent != "" and (cfgcontent[-1] == '\n' or cfgcontent[-1] == "#"):
        cfgcontent = cfgcontent[:-1]
    cfgSeq = dict([])
    # cfgdict=dict([])
    functionIDStart = dict([])
    cfgs = cfgcontent.split("#")
    currentEleNum = 0
    for cfg in cfgs:
        if cfg[0] == "\n":
            cfg = cfg[1:]
        if cfg[-1] == "\n":
            cfg = cfg[:-1]
        cfgSp = cfg.split("\n")
        startBlock = cfgSp[0].split(",")[1]
        functionid = cfgSp[0].split(",")[0]

        blockInfo = dict([])
        # functionIDStart[]=str(int(startBlock)+currentEleNum)
        preele0 = ""
        for blockstr in cfgSp[1:]:
            block = blockstr.split("|")
            thisBlockid = block[0]
            # elementList = block[3].split("-")
            if thisBlockid == startBlock:
                # functionIDStart[functionid]=elementList[0]
                functionIDStart[functionid] = preele0
            preList = []
            if block[1] != 'N':
                preList = block[1].split(",")
            sucList = []
            if block[2] != 'N':
                sucList = block[2].split(",")
            if block[3] == "":
                blockInfo[thisBlockid] = {"ele": [], "pre": preList, "suc": sucList}
                continue
            elementList = block[3].split("-")
            preele0 = elementList[0]
            elementGlobalList = elementGlobalList + elementList
            blockInfo[thisBlockid] = {"ele": elementList, "pre": preList, "suc": sucList}
            elementListLen = len(elementList)
            for eleId in range(0, elementListLen):
                tempid = elementList[eleId]
                temppre = []
                tempsuc = []
                if eleId != 0:
                    temppre.append(elementList[eleId - 1])
                if eleId != elementListLen - 1:
                    tempsuc.append(elementList[eleId + 1])
                cfgSeq[tempid] = [temppre, tempsuc, len(preList)]
        # new_block_info = []
        for bl_key in blockInfo:
            bl = blockInfo[bl_key]
            if bl['ele'] != []:
                pre_list = []
                getNext(bl['pre'],pre_list, blockInfo, 'pre')
                suc_list = []
                getNext(bl['suc'], suc_list, blockInfo, 'suc')
                bl['pre'] = pre_list
                bl['suc'] = suc_list
        blockList = list(blockInfo.values())
        for block in blockList:  ##处理block的第一个element前驱和最后一个的后继
            preLen = len(block["pre"])
            for pre in range(0, preLen):
                if block["ele"] != [] and blockInfo[block["pre"][pre]]["ele"] != []:
                    cfgSeq[block["ele"][0]][0].append(blockInfo[block["pre"][pre]]["ele"][-1])
            sucLen = len(block["suc"])
            for suc in range(0, sucLen):
                if block["ele"] != [] and blockInfo[block["suc"][suc]]["ele"] != []:
                    cfgSeq[block["ele"][-1]][1].append(blockInfo[block["suc"][suc]]["ele"][0])
    return cfgSeq, functionIDStart

def getNext(next_list, next_n_lits, blockInfo, direct): #direct='pre' or 'suc'

    for n in next_list:
        if blockInfo[n]['ele'] == []:
            getNext(blockInfo[n][direct], next_n_lits, blockInfo,direct)
        else:
            next_n_lits.append(n)

def SameLoop(index1, index2):
    loop = ["ForStmt", "WhileStmt", "DoStmt"]
    ans1 = mySingleTree[index1]["ancestors"][:]
    ans2 = mySingleTree[index2]["ancestors"][:]
    ans2.reverse()
    ans1.reverse()
    ans1Loop = -11
    ans2Loop = -22
    for a in ans1:
        if mySingleTree[a]["kind"] in loop:
            ans1Loop = a
            break
    for a in ans2:
        if mySingleTree[a]["kind"] in loop:
            ans2Loop = a
            break

    if ans1Loop == ans2Loop:
        if mySingleTree[ans1Loop]["kind"] == "ForStmt":
            if list(set([index1, index2]).intersection(mySingleTree[mySingleTree[ans1Loop]["children"][0]]["offspring"] + [mySingleTree[ans1Loop]["children"][0]])) == []:
                return 1
            else:
                return 0
        else:
            return 1
    else:
        return 0


parser = argparse.ArgumentParser(description='PSemG Generation')
parser.add_argument('--path', type=str, default=None)
parser.add_argument('--writepath', type=str, default=None)
parser.add_argument('--astpath', type=str, default=None)
parser.add_argument('--cfgpath', type=str, default=None)
parser.add_argument('--picky', type=str, default=None, help = '取文件名作为label（WebCode）：1，取文件夹的名字作为label（POJ， SOJ）：0')

args = parser.parse_args()
txtpath = args.path
writepath = args.writepath
cfgfilepath = args.cfgpath
astfilepath = args.astpath
picky = int(args.picky)


# txtpath = "1310/4.txt"
# writepath = "/home/longting/PycharmProjects/algoDetec/data/CLQ-code16-PKL/"
# cfgfilepath = "/home/longting/PycharmProjects/algoDetec/data/CLQ-code16-CFG/"
# astfilepath = "/home/longting/PycharmProjects/algoDetec/data/CLQ-code16-AST/"
# picky = 0


edgefilter = ["ValueSourceTotal"]
cfgSeq, functionIDStart = cfgsequenceGeneration(cfgfilepath + txtpath)
js = open(astfilepath + txtpath, "r").read()
# print(jsonfilepath, "doc length:", len(js))
# print(jsonfilepath, "doc length:", len(js))
jsdata = json.loads(js)
buildTree(jsdata, currentIndex, [], [], -1, 0, 0, 0, 0, 1)
buildGraph(cfgSeq, functionIDStart)

# for e in edges:
#     # if e['edgeType'] in ['trueNext', 'falseNext',  'callNext', 'ReturnNext','jump', 'next']:
#     # # if e['edgeType'] in ['trueNext', 'falseNext', 'returnTo', 'callNext', 'ReturnNext', 'jump']:
#     #     # cfge.append([e['between'][0], e['between'][1]])
#     #     print([e['between'][0], e['between'][1]], e['edgeType'])
#     print([e['between'][0], e['between'][1]], e['edgeType'])


# for e in edges:
    # if e['edgeType'] in ['trueNext', 'falseNext', 'callNext', 'ReturnNext', 'jump', 'next']:
    #     print(e['between'][0], e['between'][1], e['edgeType'], mySingleTree[e['between'][0]]['name'], mySingleTree[e['between'][1]]['name'])
    # print(e['between'][0], e['between'][1], e['edgeType'])
    # print(e)


for e in edges:
    if e["edgeType"] == "ValueSourceTotal":
        first = e["between"][0]
        second = e["between"][1]
        for ee in edges:
            for i in range(0, 2):
                if ee["between"][i] == second:
                    ee["between"][i] = first

    if e["edgeType"] == "next" or e["edgeType"] == "trueNext" or e["edgeType"] == "falseNext":
        if e["between"][1] in loopCondition and SameLoop(e["between"][0], e["between"][1]) == 1:
            if e["edgeType"] == 'next':
                e["edgeType"] = 'jump'
            else:
                addEdge(e["between"][0], e["between"][1], "jump")
newe = []
i = 0
j = 0

for e in edges:
    putInOrNot = 1
    if e["edgeType"] in edgefilter:
        putInOrNot = 0
    for ee in newe:
        if ee["between"][0] == e["between"] and ee["between"][1] == e["between"][1] and ee["edgeType"] == e["edgeType"]:
            putInOrNot = 0
            break
    if putInOrNot == 1:
        newe.append(e)
edges = newe
xed = dict([])
xcount = 0
for e in edges:
    bet = [e["between"][0], e["between"][1]]
    for i in range(0, 2):
        if not (bet[i] in xed.keys()):
            xed[bet[i]] = xcount
            if bet[i] >= StartnodeNum:
                x.append(dict({"ID": xcount, "kind": "temp", "type": "auto", "name": "x" + str(bet[i])}))
            else:
                if mySingleTree[bet[i]]["name"] != "":
                    x.append(dict(
                        {"ID": xcount, "kind": mySingleTree[bet[i]]["kind"], "type": mySingleTree[bet[i]]["type"],
                         "name": mySingleTree[bet[i]]["name"]}))
                else:
                    x.append(dict(
                        {"ID": xcount, "kind": mySingleTree[bet[i]]["kind"], "type": mySingleTree[bet[i]]["type"],
                         "name": "node" + str(xcount)}))
            xcount = xcount + 1
        e["between"][i] = xed[bet[i]]

"""
xed is original index -> current Index
xedReverse is current Index -> original Index 
"""

"""
test if contains lonely nodes
"""

# xlist = []
# for tx in x:
#     if not (tx["ID"] in xlist):
#         xlist.append(tx["ID"])
# elist = []
# for e in edges:
#     if not (e["between"][0] in elist):
#         elist.append(e["between"][0])
#     if not (e["between"][1] in elist):
#         elist.append(e["between"][1])
# if list(set(elist) - set(xlist)) != []:
#     print(txtpath, "在边里但没在节点里的")
# if list(set(xlist) - set(elist)) != []:
#     print(txtpath, "在节点里但没在边里")

"""
测试每种边的个数
"""
# astedges = ['child']
# cfgedges = ['trueNext', 'falseNext', 'callNext', 'ReturnNext','jump', 'next']
# rwedges = ['read', 'write']
# edgeNum = [0] * 4 # 0: ast, 1: cfg, 2: rw, 3:dfg
# jumpNum = 0
# for e in edges:
#     if e['edgeType'] == 'jump':
#         jumpNum += 1
#
#     if e['edgeType'] in astedges:
#         edgeNum[0] += 1
#     elif e['edgeType'] in cfgedges:
#         edgeNum[1] += 1
#     elif e['edgeType'] in rwedges:
#         edgeNum[2] += 1
#     else:
#         edgeNum[3] += 1
# print(edgeNum,  "jumpNum:", jumpNum)

"""
change all the control edges into next
"""
# for e in edges:
#     if e['edgeType'] in ["jump", 'ReturnNext', 'callNext', 'falseNext', 'trueNext']:
#         e['edgeType'] = 'next' 

# for e in edges:
#     print(e)

pickfile = writepath + txtpath.replace(".txt", ".pkl")
# y = txtpath.split("/")[1][:-4]
y = "file"
if picky == 0:
    y = txtpath.split("/")[picky]
else: 
    y = txtpath.split("/")[picky][:-4]
# print(txtpath, y)
print(pickfile)
with open(pickfile, 'wb') as file_handler:
    pickle.dump([x, edges, y], file_handler)
    file_handler.close()


