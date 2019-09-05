from problog.clausedb import ClauseDB
from problog.engine import GenericEngine
from problog.formula import LogicFormula
from problog.logic import Term, Var
from problog.prolog_engine.swi_program import SWIProgram
from problog.prolog_engine.swip import register_foreign


class EngineProlog(GenericEngine):

    def __init__(self) -> None:
        super().__init__()
        self.foreign = []

    def prepare(self, db):
        result = ClauseDB.createFrom(db, builtins={})
        result.engine = self
        return result

    def query(self, db, term):
        def_node = db.get_node(db.find(term))
        nodes = [db.get_node(c)for c in def_node.children]
        return [Term(n.functor, *n.args) for n in nodes]

    def ground(self, db, term, target=None, label=None, k=None):
        # print('Grounding {} best'.format(k))
        if target is None:
            target = LogicFormula(keep_all=True)
        translate_program = SWIProgram(db)
        return translate_program.ground(str(term), target=target, k=k)

    def ground_all(self, db, target=None, queries=None, evidence=None, k=None):
        if target is None:
            target = LogicFormula()
        if queries is None:
            # queries = [q.args[0] for q in self.query(db, Term('query', None))]
            queries = [q[0].args[0] for q in self.ground(db, Term('query',Var('X'))).queries()]
        for q in queries:
            self.ground(db, q, target, k=k)
        return target
