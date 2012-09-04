from . import np, contract
from collections import deque
from diffeoplan.library import TestCase, UncertainImage
from diffeoplan.library.logs import LogItem
from itertools import ifilter
import random

    
    
@contract(delta='int,>=1', n='int,>=1')
def make_logcases(config, id_stream, n, delta, id_tc_pattern, id_discdds, discdds):
    stream = config.streams.instance(id_stream)
    stream_data = stream.read_all()
    blocks = read_sequences_delta(stream_data, delta)
    miniplans = (make_plan(x, simplify=True) for x in blocks)
    sampled = reservoir_sample(miniplans, N=n)
    
    for i, m in enumerate(sampled):
        id_tc = id_tc_pattern % i
        I0 = UncertainImage(m.y0)
        I1 = UncertainImage(m.y1)
        plan = discdds.commands_to_indices(m.u)
        tc = TestCase(id_tc=id_tc, id_discdds=id_discdds,
                      y0=I0, y1=I1, true_plan=plan)
        yield tc


def iterate_testcases(it, delta):
    blocks = read_sequences_delta(it, delta)
    miniplans = (make_plan(x, simplify=True) for x in blocks)
    
    def accept_right_delta(c):
        return len(c.u) == delta
    
    filtered = ifilter(accept_right_delta, miniplans)
    return filtered
    

def reservoir_sample(it, N):
    """ Reservoir sample. 
        See http://en.wikipedia.org/wiki/Reservoir_sampling 
        
        print reservoir_sample(range(1000), N=10)
    """
    reservoir = []
    for i, x in enumerate(it):
        if i < N:
            reservoir.append(x)
        else:
    
            # Randomly replace elements in the reservoir
            # with a decreasing probability.              
            # Choose an integer between 0 and index (inclusive)                
            r = random.randrange(i + 1)                
            if r < N:                        
                reservoir[r] = x
    return reservoir
    
    
@contract(returns='tuple( (array,shape(x)), list(array[K]), (array,shape(x)) )')
def make_plan(sequence, simplify=True):
    """ Takes a sequence of lists of LogItems,
        converts them into a plan. """
    y0 = sequence[0].y0
    # last image
    y1 = sequence[-1].y1
    # intermediate commands (ground truth plan)
    u = [np.array(m_i.u) for m_i in sequence]
    #logger.info('Sequence of %d images' % len(sequence))
    #logger.info('Plan: %s' % str(u))
    if simplify:        
        u = simplify_plan(u)
        #logger.info('Plan simplified: %s' % str(u))

    return LogItem(y0=y0, u=u, y1=y1)


def simplify_plan(plan0):
    """ 
        Simplifies the plan assuming that the dynamics is linear.
    """
    # First make it into tuples
    plan = map(tuple, plan0)
    different = set(plan)
    for d in different:
        dm = tuple(-np.array(d))
        if d in plan and dm in plan:
            plan.remove(d)
            plan.remove(dm)
    
    #logger.info('u: %s -> %s' % (plan0, plan))
    plan1 = map(np.array, plan)
    return plan1
    

@contract(delta='int,>=1')
def read_sequences_delta(sequence, delta):
    """ Yields a sequence of lists of delta log records """
    maxlen = delta 
    q = deque(maxlen=maxlen)
    for x in sequence:
        q.append(x)
        if len(q) == maxlen:
            yield list(q)
        
