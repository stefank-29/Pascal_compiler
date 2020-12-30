from grapher import Visitor
from symbolizer import Symbol
from token import Token
from class_ import Class
from astComponents import *
import re


# todo 4

# cita ast 
class Runner(Visitor):
    def __init__(self, ast):
        self.ast = ast
        self.global_ = {} # globalni scope
        self.local = {} # mapa stekova tabela simbola
        self.scope = []
        self.call_stack = [] # stek naziva funkcija koje poziva #? sluzi za detekciju rekurzije
        self.search_new_call = True # ako je rekurzivni poziv #? main() -> fib(5) -> fib(4)
        self.return_ = False                                             # false    true
    
    # call_stack = ['12435125153', 'fib', 'print', 'fib'] #? ako se neki poziv nalazi vec u steku onda je rekurzija
    # main() -> fib(5) -> print() -> fib(4) 

    
    #  ?scope=1 (scope = id(program)) # 12435125153
    #  int main(){ #?scope=2 (scope = id(main))
    #     char x = 'a'; 
    #     if(...){ #? scope=3 (scope = id(if))
    #         int y = 5; 
    #     }

    #     x = x + 1;
    # }

    #? self.scope = [1, 2, 3] <<< sa desna na levo prolazim kroz blokove u kojima sam bio (trenutno sam u poslednjem) (nije tu globalni)
    def get_symbol(self, node): # Id(value= 'n')
        recursion = self.is_recursion()
        ref_call = -2 if not self.search_new_call else -1
        ref_scope = -2 if recursion and not self.search_new_call else -1 # ako jeste rekurzija i search_new_call=false
        id_ = node.value # ime simbola
        if len(self.call_stack) > 0:
            #fun = self.call_stack[ref_call]
            for scope in reversed(self.scope): # za svaki scope u steku
                if scope in self.local:  
                    curr_scope = self.local[scope][ref_scope] # trenutni scope
                    if id_ in curr_scope: # da li se u tom scope-u nalazi simbol
                        return curr_scope[id_] # -> Symbol('y', 'int', 'if', value=5)
        return self.global_[id_] # ako u celom steku nema simbola onda je u globalnom scope-u

    

    # self.local = {
    #     7651623113: [{
    #         'n': Symbol('n', 'int', id(fib)),
    #         'm': Symbol('m', 'int', id(fib))
    #     }, {}, {}] #? stek koji odgovara jednom scope-u (kod rekurzije za svaki poziv iste fje po jedna tabela simbola)
    # }
    def init_scope(self, node): # ulazak u blok
        scope = id(node) # scope trenutnog bloka
        if scope not in self.local: # ako ga nema u globalnoj tabeli doda se sa praznim nizom tabela
            self.local[scope] = []
        self.local[scope].append({}) # doda se dict
        for s in node.symbols: 
            self.local[scope][-1][s.id_] = s.copy() # dodaju se simboli u tabelu

    def clear_scope(self, node): # izlazak iz bloka    
        scope = id(node)
        self.local[scope].pop() # skine se tabela iz steka


    
# int main() { ->#? Symbol('main', 'int', program)
#       symbols = {'x': Symbol('x', 'char', main)}
#     char x = 'a'; #? Symbol('x', 'char', main)
#     if(...){
#         int y = 5; #? Symbol('y', 'int', if)
#     }

#     x = x + 1;
# }
    def is_recursion(self): # proverava da li se poziv fje vec nalazi na steku
        if len(self.call_stack) > 0:
            curr_call = self.call_stack[-1]
            prev_calls = self.call_stack[:-1]
            for call in reversed(prev_calls):
                if call == curr_call:
                    return True
        return False


    # ************************************** #
    def visit_Program(self, parent, node):
        for s in node.symbols: # global je globalni scope
            self.global_[s.id_] = s.copy() # postavlja se simbol u globalni scope #? 'x' -> Symbol('x', ...)
        for n in node.nodes: # obidji svaki node 
            self.visit(node, n)

    def visit_Decl(self, parent, node): 
        for idd in node.ids:
            id_ = self.get_symbol(idd) # uzmem simbol za promenljivu i dodelim joj polje value
            id_.value = None
            
    def visit_stringDecl(self, parent, node): 
        for idd in node.ids:
            id_ = self.get_symbol(idd) # uzmem simbol za promenljivu i dodelim joj polje value
            id_.value = None


    # int niz[] = {1, 2, 3, 4, 5} -> Symbol('niz', 'int', main)
    #              0  1  2  3  4
    # niz.symbols = {
    #     '0': Symbol(0, 'int', None, value=1)
    #     '1': Symbol(1, 'int', None, value=2)
    #     ...
    # }

    def visit_ArrayDecl(self, parent, node):
        # int niz[] = {1, 2, 3, 4, 5};
        # int niz[5];
        id_ = self.get_symbol(node.id_) # uzme se simbol tog niza
        id_.symbols = node.symbols # dodeli se prazna hash mapa
        size, elems = node.size, node.elems
        if elems is not None: # int niz[] = {1, 2, 3, 4, 5};
            self.visit(node, elems) 
        elif size is not None: # int niz[5];
            for i in range(size.value): 
                id_.symbols.put(i, id_.type_, None) # prazni simboli
                id_.symbols.get(i).value = None # vrednost je None

    def visit_ArrayElem(self, parent, node):
        id_ = self.get_symbol(node.id_) # simbol niza
        index = self.visit(node, node.index) # izracuna se index (ako imam niz[4*3])
        return id_.symbols.get(index.value) # mapa od indexa 12


    # niz[5] = 12;
    # x = y; #? hendlovano u if-u
    # x = y + 8; #? hendlovano u BinOp
    def visit_Assign(self, parent, node): 
        id_ = self.visit(node, node.id_) # simbol leve strane
        value = self.visit(node, node.expr) # vrednost izraza sa desne strane
        if isinstance(value, Symbol): # ako je sa desne strane promenljiva uzmem njenu vrednost (x = y)
            value = value.value
        id_.value = value 
        return id_

 
    # scope = id(node) -> id nekog cvora(bloka)
    def visit_If(self, parent, node):
        cond = self.visit(node, node.cond) # unarna ili binarna ili id (cond ima vrednost True ili False)
        if cond: # cond == True
            self.init_scope(node.true) # dodaje scope na stek
            self.visit(node, node.true)
            self.clear_scope(node.true) # skida scope sa steka
        else:
            if node.false is not None:
                self.init_scope(node.false) 
                self.visit(node, node.false)
                self.clear_scope(node.false)

    # kad izvrsavam block stavim< na stek pa skidam sa steka
    def visit_While(self, parent, node):
        cond = self.visit(node, node.cond)
        while cond:
            self.init_scope(node.block)
            self.visit(node, node.block)
            self.clear_scope(node.block)
            cond = self.visit(node, node.cond)

    def visit_For(self, parent, node):
        init = self.visit(node, node.init)
        step = self.visit(node, node.step)
        limit = self.visit(node, node.limit)
        if isinstance(limit, Symbol):
            limit = limit.value
        #print(f'init: {init}, step: {step}, limit {limit}')
        if step == -1: 
            cond = init.value >= limit
        else:
            cond = init.value <= limit
        while cond:
            self.init_scope(node.block)
            self.visit(node, node.block)
            self.clear_scope(node.block)
            init.value += step
            if step == -1: 
                cond = init.value >= limit
            else:
                cond = init.value <= limit

    def visit_RepeatUntil(self, parent, node):
        cond = self.visit(node, node.cond)
        while True:
            self.init_scope(node.block)
            self.visit(node, node.block)
            self.clear_scope(node.block)
            if cond:
                break

    def visit_FuncImpl(self, parent, node):
        id_ = self.get_symbol(node.id_) # mapira se cvor na simbol
        id_.params = node.params
        id_.block = node.block
        
        
        # if node.id_.value == 'main': # ako je main odmah i izvrsavamo (glavni begin u Pascalu #!MainBlock)
        #     self.call_stack.append(node.id_.value)
        #     self.init_scope(node.block) 
        #     self.visit(node, node.block)
        #     self.clear_scope(node.block)
        #     self.call_stack.pop()

    def visit_ProcImpl(self, parent, node):
        id_ = self.get_symbol(node.id_) # mapira se cvor na simbol
        id_.params = node.params
        id_.block = node.block

    # int fib(int n, int ,) { #? Symbol('fib', 'int', id(program), params=[n, m], block{...})
    #     ...
    # }

    def visit_FuncCall(self, parent, node):
        func = node.id_.value
        args = node.args.args
        if func == 'write' or func == 'writeln':
            # format_ = args[0].value
            # format_ = format_.replace('\\n', '\n')
            format_ = ''
            idx = 0
            while idx < len(args): 
                if (idx+1) < len(args) and isinstance(args[idx+1], str): # ako je round
                    idx += 1
                if isinstance(args[idx], Integer):
                    format_ += str(args[idx].value)
                    idx += 1
                elif isinstance(args[idx], Real):
                    format_ +=  str(args[idx].value)
                    idx += 1
                elif isinstance(args[idx], Boolean):
                    format_ +=  str(args[idx].value)
                    idx += 1
                elif isinstance(args[idx], Char):
                    format_ +=  str(args[idx].value)
                    idx += 1
                elif isinstance(args[idx], String):
                    format_ +=  str(args[idx].value)
                    idx += 1
                elif isinstance(args[idx], str): # prva : # round (a + b):0:2
                    valueToRound = self.visit(node.args, args[idx-1])
                    if isinstance(valueToRound, Symbol):
                        valueToRound = float(valueToRound.value)
                    idx += 3
                    decimals = int(args[idx].value)
                    format_ += str(round(valueToRound, decimals))
                    idx += 1
                elif isinstance(args[idx], Id) or isinstance(args[idx], ArrayElem):
                    id_ = self.visit(node.args, args[idx])
                    # if hasattr(id_, 'symbols') and id_.type_ == 'char': #! ? string
                    #     elems = id_.symbols
                    #     ints = [s.value for s in elems]
                    #     non_nulls = [i for i in ints if i is not None]
                    #     chars = [chr(i) for i in non_nulls]
                    #     value = ''.join(chars)
                    # else:
                    value = id_.value
                        # if id_.type_ == 'char':
                        #     value = chr(value)
                    format_ += str(value)
                    idx += 1
                else:
                    value = self.visit(node.args, args[idx])
                    format_ += str(value)
                    idx += 1
            if func == 'write':
                print(format_, end='') 
            elif func == 'writeln':
                print(format_, end='\n')
        elif func == 'read' or func == 'readln':
            inputs = input().split() # input cita do entera i splituje po space-u
            #matches = re.findall('%[dcs]', format_)
            for i, m in enumerate(args):
                id_ = self.visit(node.args, args[i])
                if id_.type_ == 'integer':
                    id_.value = int(inputs[i])
                elif id_.type_ == 'real':
                    id_.value = float(inputs[i])
                elif id_.type_ == 'boolean':
                    id_.value = bool(inputs[i])
                elif id_.type_ == 'char':
                    id_.value = inputs[i][0]
                elif id_.type_ == 'string':
                    id_.value = inputs[i]
        elif func == 'strlen':
            a = args[0] # 1 argument
            if isinstance(a, String): # ako je string
                return len(a.value)
            elif isinstance(a, Id): # ako je promenljiva tipa string
                id_ = self.visit(node.args, a) # vraca simbol
                return len(id_.symbols) # string je niz ascii vrednost (velicina niza simbola) #? ovako je za c
        elif func == 'strcat':
            a, b = args[0], args[1]
            dest = self.get_symbol(a)
            values = []
            if isinstance(b, Id):
                src = self.get_symbol(b) 
                elems = [s.value for s in src.symbols] # kroz sve simbole u tabeli simbola 
                non_nulls = [c for c in elems if c is not None]
                values = [c for c in non_nulls] # uzmem vrednosti drugog argumenta
            elif isinstance(b, String):
                values = [ord(c) for c in b.value] # ascii vrednost karaktera
            i = len(dest.symbols) # indeks na kraju niza
            for v in values: # dodajem vrednosti na kraj stringa
                dest.symbols.put(i, dest.type_, None)
                dest.symbols.get(i).value = v
                i += 1
        elif func == 'ord':
            a = args[0]
            value = self.visit(node.args, a)
            if isinstance(value, Symbol):
                value = value.value # simbol
            return ord(value)

        elif func == 'chr':
            a = args[0]
            value = self.visit(node.args, a)
            if isinstance(value, Symbol):
                value = value.value # simbol
            return chr(value)
        else:
            impl = self.global_[func] # uzima se funkcija iz globalnog scope-a (Symbol(naziv, tip, scope, parametri, blok))
            self.call_stack.append(func) # stavimo naziv u call stack 
            self.init_scope(impl.block) # doda se blok na call_stack (scope)
            self.visit(node, node.args) # mapiraju se argumenti na parametre
            result = self.visit(node, impl.block) # izvrasavanje bloka (cuva se povratna vrednost)
            self.clear_scope(impl.block) # skida se scope sa steka
            self.call_stack.pop()
            self.return_ = False 
            return result # vraca se vrednost #?(int x = 5 + fib(3))
    

    def visit_Block(self, parent, node):
        result = None # rezultat koji vracam iz bloka
        scope = id(node) # pravim blok
        fun = self.call_stack[-1] # trenutna funckija
        self.scope.append(scope)
        for n in node.nodes:
            if self.return_: # ako bude return prekida se blok
                break
            if isinstance(n, Break):
                break
            elif isinstance(n, Continue):
                continue
            elif isinstance(n, Exit):
                self.return_ = True # vracam se iz funkcije (globalni flag)
                if n.expr is not None:
                    result = self.visit(n, n.expr) # vracam expr uz exit
            else:
                self.visit(node, n) # posecujem instrukcije u bloku
        self.scope.pop() # skidam sa steka
        return result 
       

    def visit_MainBlock(self, parent, node):
        result = None # rezultat koji vracam iz bloka
        scope = id(node) # pravim blok (main funkcija)
        #fun = self.call_stack[-1]
        main = Symbol('main', 'int', id(parent))
        main.block = node.nodes
        self.global_['main'] = main
        self.scope.append(scope)
        self.call_stack.append('main')
        self.init_scope(node) 
        # if len(self.local[scope]) > 5: # provera beskonacne rekurzije
        #     exit(0)
        for n in node.nodes:
            if self.return_: # ako bude return prekida se blok
                break
            if isinstance(n, Break):
                break
            elif isinstance(n, Continue):
                continue
            elif isinstance(n, Exit):
                self.return_ = True # vracam se iz funkcije (globalni flag)
                if n.expr is not None:
                    result = self.visit(n, n.expr) # vracam expr uz exit
            else:
                self.visit(node, n) # posecujem instrukcije u bloku
        self.clear_scope(node)
        self.scope.pop() # skidam sa steka
        self.call_stack.pop()
        return result       
    
    def visit_MainVarBlock(self, parent, node):
        for symb in node.symbols: # dodam simbole u globalni scope
            self.global_[symb.id_] = symb.copy()
        for decl in node.nodes: # obidjem declaracije
            self.visit(node, decl)
                                    

    def visit_Params(self, parent, node): # nizovi deklaracija(obisli u symbolizeru)
        pass

    # params = [n, m]
    # args = [4, 5]
    # zip-> [(n, 4), (m, 5)]

    # parent -> child
    # fib(5) -> fib(4)
    # args   -> params
    def visit_Args(self, parent, node): # parent = funcCall, node = args
        print(self.global_)
        fun_parent = self.call_stack[-2] # ime funkcije
        impl = self.global_[fun_parent] # iz globalniog scope-a uzimam funkciju sa tim nazivom
        self.search_new_call = False
        args = [self.visit(impl.block, a) for a in node.args]
        args = [a.value if isinstance(a, Symbol) else a for a in args]
        fun_child = self.call_stack[-1]
        print(fun_child)
        impl = self.global_[fun_child]
        scope = id(impl.block)
        self.scope.append(scope)
        self.search_new_call = True
        for p, a in zip(impl.params.params, args):
            print(impl.params.params, args) # todo izvuci iz dict values vrv (impl.params.params.values())
                id_ = self.visit(impl.block, p.id_)
            id_.value = a
        self.scope[fun_child].pop()


    def visit_Elems(self, parent, node):
        id_ = self.get_symbol(parent.id_) # symbol niza koji ima hash mapu symbols 
        for i, e in enumerate(node.elems): # punim hash mapu (index: vrednost)
            value = self.visit(node, e)
            id_.symbols.put(i, id_.type_, None) # doda se Symbol bez vrednosti
            id_.symbols.get(i).value = value # doda mu se i vrednost

    def visit_Break(self, parent, node):
        pass

    def visit_Continue(self, parent, node):
        pass

    def visit_Exit(self, parent, node):
        pass

    def visit_Type(self, parent, node):
        pass

    def visit_Integer(self, parent, node):
        return int(node.value)
    
    def visit_Real(self, parent, node):
        return float(node.value)

    def visit_Boolean(self, parent, node):
        return bool(node.value)

    def visit_Char(self, parent, node):
        return node.value    # ord(node.value) #?vrv bez ord

    def visit_String(self, parent, node):
        return node.value

    def visit_Id(self, parent, node): # vraca simbol 
        return self.get_symbol(node)

    #todo napraviti wraper koji vraca int ili float zavisno od tipa
    def convert(self, value):
        if type(value) == int:
            return int(value)
        elif type(value) == float:
            return float(value)

    # x = 5 * 3; => x = 15
    # x = y * 3; za y get_symbol vraca simbol
    def visit_BinOp(self, parent, node):
        first = self.visit(node, node.first)
        if isinstance(first, Symbol): # ako je simbol vratim vrednost simbola
            first = first.value
        second = self.visit(node, node.second)
        if isinstance(second, Symbol): # isto i za drugi
            second = second.value
        if node.symbol == '+': # safety check (convert)
            return self.convert(first) + self.convert(second)
        elif node.symbol == '-':
            return self.convert(first) - self.convert(second)
        elif node.symbol == '*':
            return self.convert(first) * self.convert(second)
        elif node.symbol == '/':
            return self.convert(first) / self.convert(second)
        elif node.symbol == 'div':
            return self.convert(first) // self.convert(second)
        elif node.symbol == 'mod':
            return self.convert(first) % self.convert(second)
        elif node.symbol == '=':
            return first == second # ovde mozda treba isto convert
        elif node.symbol == '<>':
            return first != second
        elif node.symbol == '<':
            return self.convert(first) < self.convert(second)
        elif node.symbol == '>':
            return self.convert(first) > self.convert(second)
        elif node.symbol == '<=':
            return self.convert(first) <= self.convert(second)
        elif node.symbol == '>=':
            return self.convert(first) >= self.convert(second)
        elif node.symbol == 'and':
            bool_first = first #* != 0 # u pascalu ima bool (vrv ne treba provera sa nulom) (mozda cast u bool)
            bool_second = second #* != 0
            return bool_first and bool_second
        elif node.symbol == 'or':
            bool_first = first 
            bool_second = second
            return bool_first or bool_second
        elif node.symbol == 'xor':
            bool_first = first 
            bool_second = second
            return bool_first and not bool_second or not bool_first and bool_second
        else:
            return None

    def visit_UnOp(self, parent, node):
        first = self.visit(node, node.first)
        backup_first = first
        if isinstance(first, Symbol):
            first = first.value
        if node.symbol == '-':
            return -first
        elif node.symbol == 'not':
            bool_first = first #* != 0
            return not bool_first
        else:
            return None


    def visit_BinOpPar(self, parent, node):
        first = self.visit(node, node.first)
        if isinstance(first, Symbol): # ako je simbol vratim vrednost simbola
            first = first.value
        second = self.visit(node, node.second)
        if isinstance(second, Symbol): # isto i za drugi
            second = second.value
        if node.symbol == '+': # safety check (convert)
            return self.convert(first) + self.convert(second)
        elif node.symbol == '-':
            return self.convert(first) - self.convert(second)
        elif node.symbol == '*':
            return self.convert(first) * self.convert(second)
        elif node.symbol == '/':
            return self.convert(first) / self.convert(second)
        elif node.symbol == 'div':
            return self.convert(first) // self.convert(second)
        elif node.symbol == 'mod':
            return self.convert(first) % self.convert(second)
        elif node.symbol == '=':
            return first == second # ovde mozda treba isto convert
        elif node.symbol == '<>':
            return first != second
        elif node.symbol == '<':
            return self.convert(first) < self.convert(second)
        elif node.symbol == '>':
            return self.convert(first) > self.convert(second)
        elif node.symbol == '<=':
            return self.convert(first) <= self.convert(second)
        elif node.symbol == '>=':
            return self.convert(first) >= self.convert(second)
        elif node.symbol == 'and':
            bool_first = first #* != 0 # u pascalu ima bool (vrv ne treba provera sa nulom) (mozda cast u bool)
            bool_second = second #* != 0
            return bool_first and bool_second
        elif node.symbol == 'or':
            bool_first = first 
            bool_second = second
            return bool_first or bool_second
        elif node.symbol == 'xor':
            bool_first = first 
            bool_second = second
            return bool_first and not bool_second or not bool_first and bool_second
        else:
            return None

    def run(self):
        self.visit(None, self.ast) # pokrece obilazak stabla