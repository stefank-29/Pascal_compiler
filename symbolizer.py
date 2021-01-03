from grapher import Visitor

#* svaki blok ima svoju tabelu simbola
# symbols = {'main': Symbol('main', 'int', program)}

# int main() { ->#? Symbol('main', 'int', program)
      # symbols = {'x': Symbol('x', 'char', main)}
#     char x = 'a'; #? Symbol('x', 'char', main)
#     if(...){
#         int y = 5; #? Symbol('y', 'int', if)
#     }

#     x = x + 1;
# }


# kod rekurzije, vise poziva iste funckije
# stek poziva funckija i svaki poziv ima svoju tabelu simbola tako sto kopiramo tabelu
#? stek blokova (main, if)
#? prvo se proverava u if-u pa u mainu, dok se ne isprazni stek

class Symbol:
    def __init__(self, id_, type_, scope):
        self.id_ = id_
        self.type_ = type_ 
        self.scope = scope

    def __str__(self):
        return "<{} {} {}>".format(self.id_, self.type_, self.scope)

    def copy(self): 
        return Symbol(self.id_, self.type_, self.scope)

# tabela simbola
class Symbols:
    def __init__(self):
        self.symbols = {}

    def put(self, id_, type_, scope): # ubacivanje u mapu
        self.symbols[id_] = Symbol(id_, type_, scope)
    # 'x' => Symbol(...)

    def get(self, id_): # getter
        return self.symbols[id_]

    def contains(self, id_): # da li se simbol nalazi u tabeli
        return id_ in self.symbols

    def remove(self, id_): # brise simbol
        del self.symbols[id_]
    
    def __len__(self): # koliko ih ima
        return len(self.symbols)

    def __str__(self): # ispis za debug
        out = ""
        for _, value in self.symbols.items():
            if len(out) > 0:
                out += "\n"
            out += str(value)
        return out

    # za iteraciju kroz objekat
    def __iter__(self): 
        return iter(self.symbols.values())

    def __next__(self):
        return next(self.symbols.values())
        
    # symbols = Symbols(..)
    # for s in symbols:
    #     ...



class Symbolizer(Visitor):
    def __init__(self, ast):
        self.ast = ast

    def visit_Program(self, parent, node):
        node.symbols = Symbols() # node = program (visit kroz celo stablo)
        for n in node.nodes:
            self.visit(node, n)

    def visit_Decl(self, parent, node): 
        for n in node.ids:
            parent.symbols.put(n.value, node.type_.value, id(parent)) # id vraca unique int objekta (treba za stek)
        
    def visit_stringDecl(self, parent, node): 
        for n in node.ids:
            n.symbols = Symbols() 
            parent.symbols.put(n.value, node.type_.value, id(parent))
    
    # int niz = {1, 2, 3}
    # niz[2] = 4
    # Symbol(1, 'int', niz)
    # Symbol(2, 'int', niz)
    # Symbol(3, 'int', niz)
    #? niz ima svoju tabelu simbola i on je u tabeli simbola programa
    # int niz[] = {1, 2, 3, 4, 5} -> Symbol('niz', 'int', main)
    #              0  1  2  3  4
    # niz.symbols = {
    #     '0': Symbol(0, 'int', None, value=1)
    #     '1': Symbol(1, 'int', None, value=2)
    #     ...
    # }
    # niz ima tabelu simbola ciji su kljucevi indexi u nizu a vrednosti elementi tog niza
    #? niz je simbol i tabela simbola
    def visit_ArrayDecl(self, parent, node):
        for n in node.ids:
            n.symbols = Symbols() 
            parent.symbols.put(n.value, node.type_.value, id(parent)) # dodaju se nizovi u tabelu simbola scope-a

    def visit_ArrayElem(self, parent, node):
        pass

    def visit_Assign(self, parent, node):
        pass

    def visit_If(self, parent, node):
        self.visit(node, node.true)
        if node.false is not None:
            self.visit(node, node.false)

    def visit_While(self, parent, node):
        self.visit(node, node.block)

    def visit_For(self, parent, node):
        self.visit(node, node.block)
    
    def visit_RepeatUntil(self, parent, node):
        self.visit(node, node.block)

    # sama funkcija je simbol u tabeli simbola programa
    def visit_FuncImpl(self, parent, node):
        parent.symbols.put(node.id_.value, node.type_.value, id(parent)) # dodaje se u globalnu tabelu simbola
        self.visit(node, node.block) # obidje se blok
        if node.declBlock is not None:
            self.visit(node, node.declBlock)
        self.visit(node, node.params) # cuvaju se parametri u posebnoj tabeli simbola

    def visit_ProcImpl(self, parent, node):
        parent.symbols.put(node.id_.value, 'void', id(parent)) # dodaje se u globalnu tabelu simbola
        self.visit(node, node.block) # obidje se blok
        if node.declBlock is not None:
            self.visit(node, node.declBlock)
        self.visit(node, node.params) # cuvaju se parametri u posebnoj tabeli simbola

    def visit_FuncCall(self, parent, node):
        pass


    def visit_Block(self, parent, node):
        node.symbols = Symbols()
        for n in node.nodes:
            self.visit(node, n)
    
    #todo proveriti za simbole kom bloku pripadaju (za var da pripada bloku funkcije)
    def visit_VarBlock(self, parent, node):
        node.symbols = Symbols()
        for n in node.nodes:
            self.visit(node, n)        

    def visit_RepeatBlock(self, parent, node):
        node.symbols = Symbols()
        for n in node.nodes:
            self.visit(node, n)

    def visit_FuncBlock(self, parent, node):
        node.symbols = Symbols()
        for n in node.nodes:
            self.visit(node, n)
    
    def visit_MainVarBlock(self, parent, node):
        node.symbols = Symbols()
        for n in node.nodes:
            self.visit(node, n)
    
    def visit_MainBlock(self, parent, node):
        node.symbols = Symbols()
        for n in node.nodes:
            self.visit(node, n)

    def visit_Params(self, parent, node):
        node.symbols = Symbols()
        for p in node.params:
            self.visit(node, p) # cuva se u tabeli simbola parametara
            self.visit(parent.block, p) # i u tabeli lokalnih simbola

    def visit_Args(self, parent, node):
        pass

    def visit_Elems(self, parent, node):
        pass

    def visit_Break(self, parent, node):
        pass

    def visit_Continue(self, parent, node):
        pass

    def visit_Exit(self, parent, node):
        pass

    def visit_Type(self, parent, node):
        pass

    def visit_Int(self, parent, node):
        pass

    def visit_Char(self, parent, node):
        pass

    def visit_String(self, parent, node):
        pass

    def visit_Id(self, parent, node):
        pass

    def visit_BinOp(self, parent, node):
        pass

    def visit_UnOp(self, parent, node):
        pass

    def symbolize(self):
        self.visit(None, self.ast)