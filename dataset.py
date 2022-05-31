import tqdm

import os
import pickle
import logging as log

import torch
from torch.utils import data
from torch_geometric.data import Data, Batch

class Dataset(data.Dataset):
    def __init__(self, root_dir, split='train'):
        super().__init__()
        self.SUBGS = None
        self.EDGE_TYPE = None
        self.node_input_dim = None
        self.edge_input_dim = None
        self.root_dir = root_dir
        print('root_dir:', root_dir)
       
        
        self.output_dim = 109
        print('output_dim:', self.output_dim)
        if 'ggnn' in root_dir.lower():
            self.SUBGS = ['comp']
            try:
                with open(self.root_dir + 'edge_types.pkl', 'rb') as fp:
                    self.EDGE_TYPE = [pickle.load(fp)]
            except:
                self.EDGE_TYPE = [
                ['child', 'NextToken', 'ReturnsTo', 'ComputedFrom', 'GuardedBy', 'GuardedByNegation', 'FormalArgName', 'LastLexicalUse','LastRead','LastWrite']
                ]
            # print(self.EDGE_TYPE)
        elif 'devign' in root_dir.lower():
            self.SUBGS = ['comp']
            self.EDGE_TYPE = [['child', 'NextToken', 'ComputedFrom', 'LastRead', 'LastWrite', 'cfg_edge']]

        else:
            if os.path.exists(self.root_dir + 'edge_types.pkl'):
                with open(self.root_dir + 'edge_types.pkl', 'rb') as fp:
                    edges_info = pickle.load(fp)
                if len(edges_info) == 2:
                    self.EDGE_TYPE = edges_info[0]
                    self.SUBGS = edges_info[1]
                else:
                    self.EDGE_TYPE = edges_info
            else:
                assert False
             
        print(self.EDGE_TYPE)
        print(self.SUBGS)
        self.data_list = []
        self.raw_path = os.path.join(root_dir, split)

        log.info('Processing data...')
        self.process()
        log.info('Processing data done!')

    def __len__(self):
        return len(self.data_list)

    def __getitem__(self, index):
        return self.data_list[index]

    def collate(self, batch):
        data_subg_list, y_list  = [[] for _ in range(len(self.SUBGS))], []
     
        for data in batch:
            data_subgs, y = data
            for subg in range(len(self.SUBGS)):
                data_subg_list[subg].append(data_subgs[subg])
            y_list.append(y)
        data_subgs = []
        for subg in range(len(self.SUBGS)):

            data_subgs.append(Batch.from_data_list(data_subg_list[subg]))
        y = torch.cat(y_list, dim=0)
        return data_subgs, y

    def data_reader(self, raw_data, yDict):
        '''
        @params:
            raw_data: graph constructed by parser
            yDict: label dict
        @returns:
            data_subgs: list of subgraph data, each of type torch_geometric.data.Data
            y: label
        '''
        # _, ast = raw_data
        nodes, edges, targ = raw_data
        # print(nodes)
        ### predefined types
        # TODO
        NODE_TYPE = ['root_super', 'astsub_super','rwsub_super', 'dfgsub_super', 'cfgsub_super', 'EnumType','temp','empty', 'CompoundStmt', 'CXXFunctionalCastExpr', 'ForStmt', 'InitListExpr', 'CXXDefaultArgExpr', 'CXXConversionDecl', 'IndirectFieldDecl', 'BinaryOperator', 'MaxFieldAlignmentAttr', 'CXXConstCastExpr', 'DeclStmt', 'UnresolvedMemberExpr', 'CXXTryStmt', 'UnaryExprOrTypeTraitExpr', 'InlineCommandComment', 'RecordType', 'ClassTemplatePartialSpecializationDecl', 'PureAttr', 'NonTypeTemplateParmDecl', 'BindingDecl', 'CXXDeleteExpr', 'InjectedClassNameType', 'TemplateSpecializationType', 'MaterializeTemporaryExpr', 'CXXTypeidExpr', 'CXXDefaultInitExpr', 'IfStmt', 'CaseStmt', 'ImplicitCastExpr', 'GCCAsmStmt', 'CXXDestructorDecl', 'CXXOperatorCallExpr', 'CXXReinterpretCastExpr', 'CompoundLiteralExpr', 'CXXConstructorDecl', 'CompoundAssignOperator', 'CXXScalarValueInitExpr', 'IntegerLiteral', 'fileAST', 'EnumDecl', 'FunctionDecl', 'WhileStmt', 'GotoStmt', 'ContinueStmt', 'NamespaceDecl', 'VarDecl', 'AccessSpecDecl', 'CXXThisExpr', 'ImplicitValueInitExpr', 'HTMLStartTagComment', 'ConditionalOperator', 'CXXThrowExpr', 'ParamCommandComment', 'CXXBoolLiteralExpr', 'CStyleCastExpr', 'TemplateTypeParmDecl', 'GNUNullExpr', 'BuiltinType', 'DependentScopeDeclRefExpr', 'ArrayInitIndexExpr', 'MemberExpr', 'ArraySubscriptExpr', 'QualType', 'CXXMethodDecl', 'CXXTemporaryObjectExpr', 'SwitchStmt', 'NonNullAttr', 'CXXStdInitializerListExpr', 'UnaryOperator', 'TypedefDecl', 'ConstantArrayType', 'TemplateTypeParmType', 'CharacterLiteral', 'CXXStaticCastExpr', 'CXXNewExpr', 'StringLiteral', 'PointerType', 'ParmVarDecl', 'LambdaExpr', 'ParenType', 'ParenListExpr', 'CXXNullPtrLiteralExpr', 'CXXCatchStmt', 'NullStmt', 'VAArgExpr', 'ClassTemplateDecl', 'LValueReferenceType', 'DoStmt', 'UsingShadowDecl', 'CXXRecordDecl', 'TypedefType', 'CallExpr', 'CXXConstructExpr', 'ExprWithCleanups', 'StmtExpr', 'ParenExpr', 'ReturnStmt', 'PackExpansionExpr', 'ConstantExpr', 'TemplateArgument', 'FriendDecl', 'CXXBindTemporaryExpr', 'BlockCommandComment', 'BinaryConditionalOperator', 'LabelStmt', 'DeclRefExpr', 'TextComment', 'FullComment', 'TypeAliasDecl', 'BreakStmt', 'ConstAttr', 'EmptyDecl', 'CXXDependentScopeMemberExpr', 'UsingDirectiveDecl', 'TypeAliasTemplateDecl', 'ClassTemplateSpecializationDecl', 'NoThrowAttr', 'UnresolvedUsingValueDecl', 'UsingDecl', 'FunctionTemplateDecl', 'UnresolvedLookupExpr', 'DependentNameType', 'DecompositionDecl', 'CXXCtorInitializer', 'CXXForRangeStmt', 'FloatingLiteral', 'FileScopeAsmDecl', 'CXXUnresolvedConstructExpr', 'ElaboratedType', 'EnumConstantDecl', 'OpaqueValueExpr', 'DefaultStmt', 'ParagraphComment', 'IncompleteArrayType', 'CXXPseudoDestructorExpr', 'FieldDecl', 'PredefinedExpr', 'FunctionProtoType', 'CXXMemberCallExpr', 'ArrayInitLoopExpr', 'FunctionCallName']
        NODE_TYPE_DICT = {name: idx for idx, name in enumerate(NODE_TYPE)}
        NODE_VALUE_TYPE = ['root', 'sub_root', '*', 'userDefine', 'void', 'int', 'long', 'short', 'double', 'float', 'bool', 'char', 'string', 'auto']
        self.node_input_dim = len(NODE_TYPE) + len(NODE_VALUE_TYPE)
          
        EDGE_TYPE_DICT = [{name: idx for idx, name in enumerate(edge_type_list)} for edge_type_list in self.EDGE_TYPE]
        self.edge_input_dim = [len(edge_type_list) for edge_type_list in self.EDGE_TYPE]
        # print(self.SUBGS)

        ### enumerate edges
        in_subg = [[False for node in nodes] for subg in self.SUBGS] # raw_idx
        for edge in edges:
            u, v = edge['between'] # raw index
            for subg in range(len(self.SUBGS)):
                if edge['edgeType'] in self.EDGE_TYPE[subg]:
                    in_subg[subg][u] = True
                    in_subg[subg][v] = True
        
        ### process nodes
        def node_value_type_dict(value_type):
            for _, predifined in enumerate(NODE_VALUE_TYPE):
                if predifined in value_type: return _
            raise NotImplementedError

        x = [[] for _ in range(len(self.SUBGS))]
        node_raw2new = [dict([]) for _ in range(len(self.SUBGS))]
        indexstr = 'ID' # 'Index' if self.type[-5: ] == 'GGNN/' else 'ID'
        if "ggnn" in self.root_dir.lower() or "devign" in self.root_dir.lower() or 'lrpg' in self.root_dir.lower():
            indexstr = 'Index'
        # print(indexstr, 'sssssssss')
        for node in nodes:
            idx = node[indexstr]
            for subg in range(len(self.SUBGS)):
                if not in_subg[subg][idx]: continue
                node_raw2new[subg][idx] = len(x[subg])
                node_type = [0 for _ in range(len(NODE_TYPE))]
                node_value_type = [0 for _ in range(len(NODE_VALUE_TYPE))]
                node_type[NODE_TYPE_DICT[node['kind']]] = 1
                node_value_type[node_value_type_dict(node['type'])] = 1
                x[subg].append(node_type + node_value_type)
        for subg in range(len(self.SUBGS)):
            x[subg] = torch.tensor(x[subg]).float()
        
        ### process edges

        edge_index = [[[], []] for _ in range(len(self.SUBGS))]
        edge_attr = [[] for _ in range(len(self.SUBGS))]
        for edge in edges:
            u, v = edge['between'] # raw index
            for subg in range(len(self.SUBGS)):
                # print(self.SUBGS, edge['edgeType'])
                # print(subg, self.EDGE_TYPE[subg])
                if edge['edgeType'] in self.EDGE_TYPE[subg]:
                    # print(edge['edgeType'], u, v,self.EDGE_TYPE[subg], node_raw2new[subg], 'ffff')
                    # print(subg, u)
                    edge_index[subg][0].append(node_raw2new[subg][u])
                    edge_index[subg][1].append(node_raw2new[subg][v])
                    edge_type = [0 for _ in range(len(self.EDGE_TYPE[-1]))]
                    edge_type[EDGE_TYPE_DICT[-1][edge['edgeType']]] = 1
                    edge_attr[subg].append(edge_type)

        for subg in range(len(self.SUBGS)):
            edge_index[subg] = torch.tensor(edge_index[subg])
            edge_attr[subg] = torch.tensor(edge_attr[subg]).float()

        ### process data
        # TODO

        y = torch.tensor(yDict[targ]).reshape(-1, self.output_dim)
        data_subgs = []
        for subg in range(len(self.SUBGS)):
            data_subgs.append(Data(
                x=x[subg],
                edge_index=edge_index[subg],
                edge_attr=edge_attr[subg]
            ))
        return data_subgs, y

    def process(self):
        yDict=dict([])
        with open(os.path.join(self.root_dir, 'ymap.pkl'), 'rb') as fh:
            yDict = pickle.load(fh)
        
        file_names = os.listdir(self.raw_path)
        file_names.sort()

        with open('file_names.pkl', 'wb') as fp:
            pickle.dump(file_names, fp)
        for file_name in tqdm.tqdm(file_names):
 
            if not file_name.endswith('.pkl'): continue

            with open(os.path.join(self.raw_path, file_name), 'rb') as f:
                data = self.data_reader(pickle.load(f), yDict)
                self.data_list.append(data)

