from . import (contract, run_planning_stats, run_planning,
    jobs_visualization)
from collections import defaultdict
from compmake import comp, comp_stage_job_id
from diffeoplan.library import UncertainImage
from diffeoplan.programs.bench.tables import results2stats_dict, jobs_tables
from reprep import Report
from reprep.report_utils import ReportManager, StoreResults


def create_bench_jobs(config, algos, testcases, outdir):
    # dict(id_algo, id_tc, id_discdds, plan_length) => PlanningResults
    allplanning = StoreResults()
    # dict(id_algo, id_tc, id_discdds, plan_length) => resultstats
    allruns = StoreResults() 
    # dict(id_algo, id_tc) => DiffeoPlanningAlgorithm
    algoinit = StoreResults()
    
    rm = ReportManager(outdir)
    
    # Let's instantiate all test cases and sort them by discdds
    # so that we do only one initialization per algorithms
    id_discdds2testcases = defaultdict(lambda: {}) 
    for id_tc in testcases:
        tc1 = config.testcases.instance(id_tc) 
        id_discdds2testcases[tc1.id_discdds][id_tc] = tc1
            
        
    # for each algorithm
    for id_algo in algos:
        config.algos[id_algo] # check it is in the configuration
            
        # for each dynamics
        for id_discdds in id_discdds2testcases:
            job_id = 'init-%s-%s' % (id_algo, id_discdds)
            
            # initialize the algorithm for that dynamics
            algo = comp(init_algorithm, config,
                        id_algo, id_discdds, job_id=job_id)
            algoinit[dict(id_algo=id_algo, id_discdds=id_discdds)] = algo
            
            # for each test case in that dynamics
            for id_tc, tc in id_discdds2testcases[id_discdds].items():
                
                # run the planning
                job_id = 'plan-%s-%s' % (id_algo, id_tc)
                result = comp(run_planning, config, id_algo,
                              id_tc, algo, job_id=job_id)
                
                # compute statistics
                result_stats = comp(run_planning_stats, config, result,
                                    job_id=job_id + '-stats') 
    
                attrs = dict(id_algo=id_algo, id_tc=id_tc,
                             id_discdds=tc.id_discdds,
                             true_plan_length=len(tc.true_plan))
                allruns[attrs] = result_stats
                allplanning[attrs] = result
    
    jobs_report_algo_init(config, rm, algoinit)
    jobs_report_tc(config, rm, testcases)
    jobs_report_dds(config, rm, id_discdds2testcases.keys())

    allstats = StoreResults()
    for key in allruns:
        run = allruns[key]
        job_id = comp_stage_job_id(run, 'statsdict')
        allstats[key] = comp(results2stats_dict, run, job_id=job_id)

    jobs_tables(allstats, rm)
    jobs_visualization(config, allruns, rm)
    
    rm.create_index_job()

def jobs_report_tc(config, rm, testcases):
    for id_tc in testcases:
        tc = config.testcases.instance(id_tc)
        report = comp(report_tc, config, id_tc)
        rm.add(report, 'tc', id_tc=id_tc, id_discdds=tc.id_discdds)

def jobs_report_dds(config, rm, discdds):
    for id_discdds in discdds:
        report = comp(report_dds, config, id_discdds)
        rm.add(report, 'dds', id_discdds=id_discdds)
        
def jobs_report_algo_init(config, rm, algoinit): #@UnusedVariable
    """ add the initialization report for each algorithm """
    for k, algo in algoinit.items():
        id_algo = k['id_algo'] 
        id_discdds = k['id_discdds']
        job_id = 'init-%s-%s-report' % (id_algo, id_discdds)
        report = comp(report_init_algorithm, id_algo, id_discdds, algo, job_id=job_id)
        rm.add(report, 'init', id_algo=id_algo, id_discdds=id_discdds)
        
def init_algorithm(config, id_algo, id_discdds):
    """ Returns the instanced DiffeoPlanninAlgorithm """
    # instance the algorithm
    algo = config.algos.instance(id_algo)    
    # initialize the algorithm with the dynamics
    discdds = config.discdds.instance(id_discdds)
    # TODO: add computation time
    #t0 = time.clock()
    algo.set_name_for_log(id_algo)
    algo.init(id_discdds, discdds) 
    #init_time = time.clock() - t0
    return algo

@contract(returns=Report)
def report_init_algorithm(id_algo, id_discdds, algo):
    """ Creates a report for the initialization phase of the algorithm """
    r = Report('init-%s-%s' % (id_algo, id_discdds)) 
    algo.init_report(r)
    return r
    
@contract(returns=Report)
def report_tc(config, id_tc):
    r = Report('tc-%s' % (id_tc))
    tc = config.testcases.instance(id_tc)
    tc.display(r)
    return r

@contract(returns=Report)
def report_dds(config, id_discdds, image='lena'):
    r = Report('dds-%s' % (id_discdds))
    dds = config.discdds.instance(id_discdds)
    image = config.images.instance(image)
    y0 = UncertainImage(image)
    dds.display(r, y0)
    return r


