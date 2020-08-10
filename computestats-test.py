from computestats import *

def test_gen_pbp():
    intp = [{'result':['EM','TXST-NICK ED'],'time':'0003','offense':'TXST'},{'result':['TB','TAMU-SHANIAH CARROLL','TEXAS-DAVIS ROE'],'time':'2433','offense':'TEXAS'}]
    test_val = ['(00:03)TXST possession: Missed shot by TXST-NICK ED. Turnover','(24:33)TEXAS possession: Beat by TAMU-SHANIAH CARROLL on TEXAS-DAVIS ROE forces a TURNOVER.']
    for i, j in zip(intp,test_val):
        assert gen_pbp(i)==j