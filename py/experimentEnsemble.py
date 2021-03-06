'''
This is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This software is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this source.  If not, see <http://www.gnu.org/licenses/>.
'''

import math
import os
import pickle
import sys

import competitors
import fastr
import metric

"""
This script runs and ensembles the results of the FAST-R algorithms using the Budget scenario.
"""

SIR = [("flex", "v3"), ("grep", "v3"), ("gzip", "v1"), ("sed", "v6"), ("make", "v1")]
D4J = [("math", "v1"), ("closure", "v1"), ("time", "v1"), ("lang", "v1"), ("chart", "v1")]

def run_algorithm(script, covType, algorithm, prog, v, red):

    ## Removed since we are only running once with a large B
    ## Reduced from 50 for development efficiency
    ## Increase this number when generating data
    #repeats = 5
    print(f"running {algorithm} {covType}.....")
    # FAST-R parameters
    k, n, r, b = 5, 10, 1, 10
    dim = 10

    # FAST-f sample size
    def all_(x): return x
    def sqrt_(x): return int(math.sqrt(x)) + 1
    def log_(x): return int(math.log(x, 2)) + 1
    def one_(x): return 1


    inputFile = "input/{}_{}/{}-bbox.txt".format(prog, v, prog)
    wBoxFile = "input/{}_{}/{}-{}.txt".format(prog, v, prog, covType)
    numOfTCS = sum((1 for _ in open(inputFile)))
    selection = set()

    # Change this number to determine the fraction of the total tests we want
    reduction = float(red)

    B = int(numOfTCS * reduction)

    #if algorithm == "FAST++":
    #        pTime, rTime, sel = fastr.fastPlusPlus(inputFile, dim=dim, B=B)
    #        selection = sel

    #elif algorithm == "FAST-CS":
    #    for run in range(repeats):
    #        pTime, rTime, sel = fastr.fastCS(inputFile, dim=dim, B=B)
    #        selection = sel

    #elif algorithm == "FAST-pw":
    #    for run in range(repeats):
    #        pTime, rTime, sel = fastr.fast_pw(inputFile, dim=dim, B=B)
    #        selection = sel

    if algorithm == "GA":
        pTime, rTime, sel = competitors.ga(wBoxFile, B=B)
        selection = sel   
 
    elif algorithm == "ART-D":
        pTime, rTime, sel = competitors.artd(wBoxFile, B=B)
        selection = sel
   
    elif algorithm == "ART-F":
        pTime, rTime, sel = competitors.artf(wBoxFile, B=B)
        selection = sel

    else:
        print('Not a supported algorithm: {}'.format(algorithm))
        exit()

    return selection

def ga_multi(prog, v, red):

    ## Removed since we are only running once with a large B
    ## Reduced from 50 for development efficiency
    ## Increase this number when generating data
    #repeats = 5
    print("running ga_multi.....")
    covs = ["branch","line","function"]
    inputFile = "input/{}_{}/{}-bbox.txt".format(prog, v, prog)
    wBoxFiles = ["input/{}_{}/{}-{}.txt".format(prog, v, prog, covType) for covType in covs]
    numOfTCS = sum((1 for _ in open(inputFile)))
    selection = set()
    # Change this number to determine the fraction of the total tests we want
    reduction = float(red)
    B = int(numOfTCS * reduction)

    pTime, rTime, sel = competitors.ga_multi(wBoxFiles, B=B)
    selection = sel

    return selection


def ensemble_selections(selection_sets, method):

    final_selections = set()

    if method == 'majority':

        counts = {}
        cases = len(selection_sets)
        threshold = cases // 2

        for selections in selection_sets:
            for selection in selections:
                if selection in counts:
                    counts[selection] += 1
                else:
                    counts[selection] = 1

        for selection in counts:
            if counts[selection] > threshold:
                final_selections.add(selection)

    elif method == 'union':
        
        selection_sets = [set(selection) for selection in selection_sets]

        for selections in selection_sets:
            final_selections.update(selections)

    elif method == 'intersection':

        selection_sets = [set(selection) for selection in selection_sets]

        ssiter = iter(selection_sets)
        final_selections = next(ssiter)

        for selections in ssiter:
            final_selections = final_selections.intersection(selections)

    else:
        print('Not a supported ensembling method: {}'.format(method))
        exit()

    return list(final_selections)


def rate_selection(selection, prog, v):

    javaFlag = True if v == 'v0' else False
    if javaFlag:
        faultMatrix = "input/{}_{}/fault_matrix.pickle".format(prog, v)
    else:
        faultMatrix = "input/{}_{}/fault_matrix_key_tc.pickle".format(prog, v)
    inputFile = "input/{}_{}/{}-bbox.txt".format(prog, v, prog)

    fdl = metric.fdl(selection, faultMatrix, False)
    tsr = metric.tsr(selection, inputFile)
    fft = metric.fft(selection, faultMatrix,False)
    apfd = metric.apfd(selection,faultMatrix,False)
    return (fdl,fft,apfd,tsr)


if __name__ == "__main__":

    usage = """USAGE: python3 py/experimentEnsemble.py <algorithm> <ensemble> <program> <version> <reduction>
OPTIONS:
  <algorithm>: The algorithm to use for generating test cases to be ensembled.
    options: GA, ART-D, ART-F
  <ensemble>: The method of ensembling the different generated test suites together.
    options: majority, union, intersection
  <program> <version>: The target subject and its respective version.
    options: flex_v3, grep_v3, gzip_v1, make_v1, sed_v6, chart_v0, closure_v0, lang_v0, math_v0, and time_v0.
    options: positive float value, e.g. 0.25"""

    if len(sys.argv) != 6:
        print(usage)
        exit()

    script, algorithm, method, prog, v, red = sys.argv

    selections = {}

    selections['function'] = run_algorithm(script, 'function', algorithm, prog, v, red)
    selections['line']     = run_algorithm(script, 'line',     algorithm, prog, v, red)
    selections['branch']   = run_algorithm(script, 'branch',   algorithm, prog, v, red)

    ensemble = ensemble_selections([selections[m] for m in selections], method)

    selections['ga_multi'] = ga_multi(prog,v,red)
    for coverageType in selections:
        (fdl, ffd,apfd,tsr) = rate_selection(selections[coverageType], prog, v)
        print('Results with algorithm {} using {} coverage:'.format(algorithm, coverageType))
        print('  Fault detection loss: {}'.format(fdl))
        print('  Test suite reduction: {}'.format(tsr))
        print(f"  Position of the First fault detected:{ffd}")
        print(f"  Average Percentage of Faults Detected:{apfd}\n")

    (fdl,ffd,apfd, tsr) = rate_selection(ensemble, prog, v)
    print('Results with algorithm {} using ensembled results:'.format(algorithm))
    print('  Fault detection loss: {}'.format(fdl))
    print('  Test suite reduction: {}'.format(tsr))
    print(f"  Position of the First fault detected:{ffd}")
    print(f"  Average Percentage of Faults Detected:{apfd}")


