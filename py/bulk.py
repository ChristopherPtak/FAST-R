from experimentEnsemble import run_algorithm, ensemble_selections, rate_selection
import pandas as pd
import sys

def run_test(algorithm, method, prog, v, red):
    """Performs a single run of the ensembling experiment for a given algorithm, ensembling method, program & version,
    and percent reduction. Returns

    Args:
        algorithm (string): The algorithm to use for generating test cases to be ensembled. (GA, ART-D, ART-F)
        method (string): The method of ensembling the different generated test suites together (majority, union, intersection)
        prog (string): target subjects to apply reductions on 
        v (string): target subject's corresponding version
        red (float or string): float-ish percentage of test suite in a reduction

    Returns:
        [(string, float, float)] - 2D list of coverage type, fault detection loss %, test suite reduction %
    """

    script = 'we should remove script from parameters!'

    selections = {}

    selections['function'] = run_algorithm(script, 'function', algorithm, prog, v, red)
    selections['line']     = run_algorithm(script, 'line',     algorithm, prog, v, red)
    selections['branch']   = run_algorithm(script, 'branch',   algorithm, prog, v, red)

    ensemble = ensemble_selections([selections[m] for m in selections], method)

    results = []

    for coverageType in selections:
        (fdl, tsr) = rate_selection(selections[coverageType], prog, v)
        print('Results with algorithm {} using {} coverage:'.format(algorithm, coverageType))
        print('  Fault detection loss: {}'.format(fdl))
        print('  Test suite reduction: {}'.format(tsr))

        results.append([coverageType, fdl, tsr])

    (fdl, tsr) = rate_selection(ensemble, prog, v)
    print('Results with algorithm {} using ensembled results:'.format(algorithm))
    print('  Fault detection loss: {}'.format(fdl))
    print('  Test suite reduction: {}'.format(tsr))

    results.append([method + ' ensemble', fdl, tsr])

    return results

def run_bulk(algorithm, method, prog, v, red, runs=1):

    data = []

    for run in range(runs):
        print("-----Running iteration {}:".format(run))
        temp = run_test(algorithm, method, prog, v, red)
        for t in temp:
            t.insert(0,run)

        data += temp

    df = pd.DataFrame.from_records(data, columns =['Run', 'Method', 'Fault Detection Loss', 'Test Suite Reduction'])
    df.to_csv("output-{}-{}-{}-{}-{}.csv".format(algorithm, method, prog, v, red), index=False)

if __name__ == "__main__":

    usage = """USAGE: python3 py/bulk.py <algorithm> <ensemble> <program> <version> <reduction> <runs>
OPTIONS:
  <algorithm>: The algorithm to use for generating test cases to be ensembled.
    options: GA, ART-D, ART-F
  <ensemble>: The method of ensembling the different generated test suites together.
    options: majority, union, intersection
  <program> <version>: The target subject and its respective version.
    options: flex v3, grep v3, gzip v1, make v1, sed v6, chart v1, closure v1, lang v1, math v1, time v1
  <reduction>: The fraction of the original test suite size to target.
    options: positive float value, e.g. 0.25
  <runs>: The number of runs to perform."""

    if len(sys.argv) != 7:
        print(usage)
        exit()

    script, algorithm, method, prog, v, red, runs = sys.argv
    run_bulk(algorithm, method, prog, v, red, runs=int(runs))

    


