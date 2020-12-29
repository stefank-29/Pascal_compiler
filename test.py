from lexer import Lexer
from parser import Parser
from generator import Generator
from symbolizer import Symbolizer
from runner import Runner
#from grapher import *
id = '03'
path = f'./Datoteke/Druga faza/{id}/src.pas'
with open(path, 'r') as source:
    text = source.read()
    lexer = Lexer(text)
    tokens = lexer.lex()

    parser = Parser(tokens)
    ast = parser.parse()

    # doda simbole ast-u (modifikuje ast)
    symbolizer = Symbolizer(ast)
    symbolizer.symbolize()

    runner = Runner(ast)
    runner.run()

    # generator = Generator(ast)
    # code = generator.generate('main.c') # ime fajla
    # print(ast)


#grapher = Grapher(ast)
#img = grapher.graph()
# Image(img) 
# print(ast)
# for t in tokens:
#     print(t)



