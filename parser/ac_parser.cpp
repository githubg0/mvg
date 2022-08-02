#include <cstdio>
#include <string>
#include <iostream>
#include <sstream>
#include <fstream>

#include "clang/AST/AST.h"
#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/ASTConsumers.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Rewrite/Core/Rewriter.h"
#include "clang/Tooling/CommonOptionsParser.h"
#include "clang/Tooling/Tooling.h"
#include "llvm/Support/raw_ostream.h"
#include "clang/AST/ASTContext.h"
#include "clang/Analysis/CFG.h"

#include "clang/AST/JSONNodeDumper.h"
#include "clang/Lex/Lexer.h"
#include "llvm/ADT/StringSwitch.h"
#include "clang/AST/ASTDumperUtils.h"

using namespace clang;
using namespace clang::driver;
using namespace clang::tooling;
using namespace std;
int endLineTag=0;
int perDigit=4;
string returnCFGstr="";
string returnstr="{\n\"kind\":\"fileAST\",\n\"inner\":[\n";
static llvm::cl::OptionCategory MyOptionCategory("MyOptions");
static llvm::cl::opt<std::string> OutputFilename("o",
                                                 llvm::cl::desc("Specify output filename that contains stmt:type"),
                                                 llvm::cl::value_desc("output_filename"), llvm::cl::cat(MyOptionCategory));
string findstr=".cpp:";
LangOptions MyLangOpts;
SourceManager *ptrMySourceMgr;
Rewriter MyRewriter;
ASTContext *TheContext;
std::string createPointerRepresentation(const void *Ptr) {
    return "0x" + llvm::utohexstr(reinterpret_cast<uint64_t>(Ptr), true);
}


class MyASTVisitor : public RecursiveASTVisitor<MyASTVisitor> {
public:
    MyASTVisitor() {}
//    bool VisitFunctionDecl(FunctionDecl *f) {
    bool VisitDecl(Decl *f) {
//        f->dump();
        string checkstr=f->getDeclKindName();
        string endlineInfo = f -> getEndLoc().printToString(*ptrMySourceMgr);
        string position= f -> getLocation () .printToString(*ptrMySourceMgr);
        int positionLen=position.length() ;
        int endLineNum = stoi(endlineInfo.substr(endlineInfo.find(":")+1, endlineInfo.rfind(":")));
        int astTag=0;
        if (checkstr=="UsingDirective" ||
            ((position.find("/include/")>=0) && (position.find("/include/")<positionLen)) ||
            ((position.find(".h:")>=0) && (position.find(".h:")<positionLen) ))
//            astTag=1;
            return true;
        if (endLineNum<endLineTag)
            astTag=1;
        string fileid="";
        if (astTag==0){
            endLineTag = endLineNum;

            std::string str1;
            llvm::raw_string_ostream os(str1);

            ASTDumpOutputFormat x=ADOF_JSON;
            f->dump(os,true,x );
            string dumpstr=os.str();
            returnstr=returnstr+dumpstr+",\n";
            int dumpi=0;
            while (dumpstr.substr(dumpi,2)!=": ") dumpi++;
            dumpi=dumpi+3;

            while (dumpstr[dumpi]!='\"')
            {
                fileid=fileid+dumpstr[dumpi];
                dumpi++;
            }
        }
//        cout<<"***********"<<fileid<<"************\n";

        if (!((checkstr=="CXXMethod")||(checkstr=="Function") || (checkstr=="CXXConstructor") ||(checkstr=="CXXDestructor")))
            return true;
        if (f->hasBody()) {

            Stmt *funcBody = f->getBody();
            std::unique_ptr<CFG> sourceCFG = CFG::buildCFG(f, funcBody, TheContext, CFG::BuildOptions());

//            string FuncBlock=getPosStartEnd(funcBody);
            string FuncBlock=fileid;
            string EntryID=to_string((sourceCFG->getEntry()).getBlockID());
            FuncBlock=FuncBlock+","+EntryID+"\n";

            for (CFG::const_iterator BI = sourceCFG->begin(), BE = sourceCFG->end(); BI != BE; BI++) {
                // (*BI)->dump();
                string succStr="";
                for (auto I = (*BI)->succ_begin(), E = (*BI)->succ_end(); I != E; ++I)//这里的iterator是针对block的
                {
                    clang::CFGBlock *singleSucc;
                    if (I->isReachable ())

                        singleSucc=I->getReachableBlock();
                    else
                        singleSucc=I->getPossiblyUnreachableBlock ();

                    succStr=succStr+to_string(singleSucc->getBlockID ())+",";
                }
                if (succStr!="")
                    succStr=succStr.substr(0,succStr.length()-1);
                else
                    succStr="N";


                string predStr="";
                for (auto I = (*BI)->pred_begin(), E = (*BI)->pred_end(); I != E; ++I)//这里的iterator是针对block的
                {
                    clang::CFGBlock *singlepred;
                    if (I->isReachable ())
                        singlepred=I->getReachableBlock();
                    else
                        singlepred=I->getPossiblyUnreachableBlock ();
                    predStr=predStr+to_string(singlepred->getBlockID ())+",";
                }
                if (predStr!="")
                    predStr=predStr.substr(0,predStr.length()-1);
                else
                    predStr="N";
                //llvm::outs() <<"pred blocks: "<<succStr<<"\n";

                string BlockID=to_string((*BI)->getBlockID());
//                llvm::outs()<<"**********\nblockid:"<<BlockID<<"\n"<<"succ blocks: "<<succStr<<"\n"<<"pred blocks: "<<succStr<<"\n********\n";
                string elementsInfo="";
//                string BlockInfo="";
                for (clang::CFGBlock::iterator eb = (*BI)->begin(), ee = (*BI)->end(); eb != ee; eb++) {
                    const clang::Stmt* eleStmt=eb->getAs<clang::CFGStmt>()->getStmt();

                    std::string str1;
                    llvm::raw_string_ostream os(str1);
                    eleStmt->dump(os,*ptrMySourceMgr);
                    string newstr=os.str();
//                    printf("%s\n",os.str().c_str());
//                    cout<<str1<<endl;
                    int j=0;
                    string operatorID="";
                    char splitop=' ';
                    while (newstr[j]!=splitop) j++;
                    j++;

                    while(newstr[j]!=splitop)
                    {
                        operatorID=operatorID+str1[j];
                        j++;
                    }
//                    cout<<"end"<<operatorID<<"end"<<endl;

                    elementsInfo=elementsInfo+operatorID+"-";

                }
                elementsInfo=elementsInfo.substr(0,elementsInfo.length()-1);
                FuncBlock=FuncBlock+ BlockID+"|"+predStr+"|"+succStr+"|"+elementsInfo+"\n";

            }
            returnCFGstr=returnCFGstr+FuncBlock.substr(0,FuncBlock.length()-1)+"#\n";
//            cout<<returnCFGstr<<endl;
        }

        return true;
    }

//private:
//    ASTContext  &TheContext;
};
class MyASTConsumer : public ASTConsumer {
public:
    MyASTConsumer(): Visitor() {} //initialize MyASTVisitor

    virtual bool HandleTopLevelDecl(DeclGroupRef DR) {

        for (DeclGroupRef::iterator b = DR.begin(), e = DR.end(); b != e; ++b) {
            Visitor.TraverseDecl(*b);
        }
        return true;
    }

private:
    MyASTVisitor Visitor;
};
class MyFrontendAction : public ASTFrontendAction {
public:
    MyFrontendAction() {}

    void EndSourceFileAction() override { // Fill out if necessary
    }

    std::unique_ptr<ASTConsumer> CreateASTConsumer(
            CompilerInstance &CI, StringRef file) override {

        MyLangOpts = CI.getLangOpts();
        ptrMySourceMgr= &(CI.getSourceManager());
        MyRewriter= Rewriter(*ptrMySourceMgr, MyLangOpts);
        TheContext=const_cast<ASTContext *>(&CI.getASTContext());
        return llvm::make_unique<MyASTConsumer>();
    }
};
void getKindList(string jsonstr)
{
    int jsonstrLen=jsonstr.length();

    string typeKind="";
    int typeKindLength=0;
    int index=0;
    while ((index=jsonstr.find("\"kind\": \""))>=0 &&  jsonstr.find("\"kind\": \"")<jsonstrLen)
    {
        string tempstr="";
        index=index+9;
        int tempLen=0;
        while (jsonstr[index]!='\"')
        {
            tempstr=tempstr+jsonstr[index];
            index=index+1;
            tempLen=tempLen+1;
        }

        if (!(typeKind.find(tempstr)>=0 && typeKind.find(tempstr)< typeKindLength))
        {
            typeKindLength=typeKindLength+tempLen+2;//一个是加的逗号，一个是tempstr的长度tempLen+1
            typeKind=typeKind+tempstr+",";
        }
        jsonstr=jsonstr.substr(index,jsonstrLen);
        jsonstrLen=jsonstrLen-index;
    }
    if (typeKind!="")
    {
        cout<< "***";
        cout << typeKind<<endl;
    }
}
int main(int argc, const char **argv) {
    // printf("i am comming....\n");
    int rtn_flag=0;
//      cout<<"#";
    // cout << argv[0] <<endl;
    // cout << argv[3] << "\nargv[1]: " << argv[4] << endl;
    // string pre_args[3], *pre_arg_pointer;
    // for (int i = 0; i < 3; i ++)
    //     pre_args[i] = argv[i];
    const char ** str_con = argv;
    // (str_con + 1) = argv[1]


    // cout << pre_args[0] << "\n" << pre_args[1] << "\n" << pre_args[2] << endl;
    // pre_arg_pointer = &pre_args[0];
    // const char *str_con = pre_arg_pointer.c_str();
    // const char *str_con = pre_args.c_str();
//    CommonOptionsParser op(argc, argv, MyOptionCategory);
    cout << str_con[0] << "\n" << str_con[1] << "\n" << str_con[2] << endl;
    CommonOptionsParser op(argc, str_con, MyOptionCategory);

    ClangTool Tool(op.getCompilations(), op.getSourcePathList());

    rtn_flag= Tool.run(newFrontendActionFactory<MyFrontendAction>().get());
    if (rtn_flag==1) return 0;
//    getKindList(returnstr);
    returnstr=returnstr.substr(0,returnstr.length()-2)+"\n]\n}";
    vector<string> tags;
    tags.assign(argv + 1, argv + argc);
    string pathOrg=tags[0];
    int endPos=pathOrg.length()-4;
    string fileTail="";
    for (int i = 80; i<endPos;i++) fileTail=fileTail+pathOrg[i];
    // TODO
    string CFGwritepath="/astpath/";
    string ASTwritepath="/cfgpath/";
    // string CFGwritepath = argv[6];
    // string ASTwritepath = argv[7];
    cout << fileTail << endl;
    CFGwritepath=CFGwritepath+fileTail+".txt";
    ASTwritepath=ASTwritepath+fileTail+".txt";
   cout<<"cfg: "<<CFGwritepath<<endl;
   cout<<"ast: "<<ASTwritepath<<endl;
    ofstream cfgwrite;
    cfgwrite.open(CFGwritepath);
    cfgwrite<<returnCFGstr<<endl;
    cfgwrite.close();

    ofstream astwrite;
    astwrite.open(ASTwritepath);
    astwrite<<returnstr<<endl;
    astwrite.close();
    // cout<< returnCFGstr << '\nast: ' << returnstr << endl;



    return rtn_flag;
}








