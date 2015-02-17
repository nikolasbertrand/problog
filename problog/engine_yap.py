from __future__ import print_function

from .engine import GenericEngine
from .util import subprocess_check_call
from .formula import StringKeyLogicFormula
from .core import LABEL_QUERY, LABEL_EVIDENCE_POS, LABEL_EVIDENCE_NEG, LABEL_NAMED
from .program import PrologFile

import os, tempfile
from collections import defaultdict


class YapEngine(GenericEngine) :
    """Generic interface to a grounding engine."""
    
    def __init__(self, label_all=False) :
        GenericEngine.__init__(self)
        self.label_all = label_all
    
    def prepare(self, db) :
        if db.source_files : 
            return db
        else :
            filename = tempfile.mkstemp('.pl')[1]
            with open(filename, 'w') as f :
                for line in db :
                    print( '%s.' % line, file=f )
            return PrologFile(filename)
        
    def query(self, db, term) :
        raise NotImplementedError('YapEngine.prepare is not implemented.')
        
    def ground(self, db, term, target=None, label=None) :
        raise NotImplementedError('YapEngine.ground is not implemented.')
        
    def ground_all(self, db, target=None, queries=None, evidence=None) :
        assert(queries == None)
        assert(evidence == None)
        
        db = self.prepare(db)
        
        out_gp = tempfile.mkstemp('.gp')[1]
        out_qr = tempfile.mkstemp('.qr')[1]
        out_ev = tempfile.mkstemp('.ev')[1]
        
        scriptname = os.path.join(os.path.dirname(__file__), 'ground_compact.pl')
        
        modelfile = db.source_files[0]
            
        cmd = [ 'yap', '-L', scriptname, '--', modelfile, out_gp, out_ev, out_qr ]
        
        #print (' '.join(cmd))
                
        subprocess_check_call(cmd)
        
        interm = StringKeyLogicFormula()
        with open(out_gp) as f :
            for line in f :
                content, label = line.strip().split('|')
                i, t, c = content.strip().split(None,2)
                if t == 'FACT' :
                    interm.addAtom(i, c)
                    if self.label_all :
                        interm.addName( label.strip(), i, LABEL_NAMED )
                elif t == 'AND' :
                    children = c.split()
                    interm.addAnd( i, children )
                    if self.label_all :
                        interm.addName( label.strip(), i, LABEL_NAMED )
        
        with open(out_qr) as f :
            for line in f :
                key, label = line.split('|')
                interm.addName( label.strip(), key.strip(), LABEL_QUERY )
                
        with open(out_ev) as f :
            for line in f :
                key, label = line.split('|')
                key, value = key.split()
                if value.strip() == 't' :
                    interm.addName( label.strip(), key.strip(), LABEL_EVIDENCE_POS )
                else :
                    interm.addName( label.strip(), key.strip(), LABEL_EVIDENCE_NEG )
        target = interm.toLogicFormula()
        return target