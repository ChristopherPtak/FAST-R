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
This file runs and ensembles the results of the FAST-R algorithms using the Budget scenario.
"""

def run_algorithm(script, covType, algorithm, prog, v, rep):

    SIR = [("flex", "v3"), ("grep", "v3"), ("gzip", "v1"), ("sed", "v6"), ("make", "v1")]
    D4J = [("math", "v1"), ("closure", "v1"), ("time", "v1"), ("lang", "v1"), ("chart", "v1")]

    repetitions = int(rep)

    # Reduced from 50 for development efficiency
    # Increase this number when generating data
    repeats = 5

    ## Commented out until output is restored
    #directory = "outputEnsemble-{}/{}_{}/".format(covType, prog, v)
    #if not os.path.exists(directory):
    #    os.makedirs(directory)
    #if not os.path.exists(directory + "selections/"):
    #    os.makedirs(directory + "selections/")
    #if not os.path.exists(directory + "measures/"):
    #    os.makedirs(directory + "measures/")

    # FAST-R parameters
    k, n, r, b = 5, 10, 1, 10
    dim = 10

    # FAST-f sample size
    def all_(x): return x
    def sqrt_(x): return int(math.sqrt(x)) + 1
    def log_(x): return int(math.log(x, 2)) + 1
    def one_(x): return 1

    # BLACKBOX
    javaFlag = True if ((prog, v) in D4J) else False

    inputFile = "input/{}_{}/{}-bbox.txt".format(prog, v, prog)
    wBoxFile = "input/{}_{}/{}-{}.txt".format(prog, v, prog, covType)
    if javaFlag:
        faultMatrix = "input/{}_{}/fault_matrix.txt".format(prog, v)
    else:
        faultMatrix = "input/{}_{}/fault_matrix_key_tc.pickle".format(prog, v)

    ## Commented out until output is restored
    #outpath = "outputEnsemble-{}/{}_{}/".format(covType, prog, v)
    #sPath = outpath + "selections/"
    #tPath = outpath + "measures/"

    numOfTCS = sum((1 for _ in open(inputFile)))

    selection = set()

    for reduction in range(1, repetitions+1):

        B = int(numOfTCS * reduction / 100)

        if algorithm == "FAST++":
            for run in range(repeats):
                pTime, rTime, sel = fastr.fastPlusPlus(inputFile, dim=dim, B=B)
                selection.update(sel)

        elif algorithm == "FAST-CS":
            for run in range(repeats):
                pTime, rTime, sel = fastr.fastCS(inputFile, dim=dim, B=B)
                selection.update(sel)

        elif algorithm == "FAST-pw":
            for run in range(repeats):
                pTime, rTime, sel = fastr.fast_pw(inputFile, dim=dim, B=B)
                selection.update(sel)

        elif algorithm == "GA":
            for run in range(repeats):
                pTime, rTime, sel = competitors.ga(wBoxFile, B=B)
                selection.update(sel)

        elif algorithm == "ART-D":
            for run in range(repeats):
                pTime, rTime, sel = competitors.artd(wBoxFile, B=B)
                selection.update(sel)

        elif algorithm == "ART-F":
            for run in range(repeats):
                pTime, rTime, sel = fastr.artf(wBoxFile, B=B)
                selection.update(sel)

        else:
            print('Not a supported algorithm: {}'.format(algorithm))
            exit()

    return selection


def ensemble_selections(selection_sets):

    # TODO: Add more ensembling methods so we can compare them

    counts = {}
    cases = len(selection_sets)
    threshold = cases // 2

    for selections in selection_sets:
        for selection in selections:
            if selection in counts:
                counts[selection] += 1
            else:
                counts[selection] = 1

    final_selections = []
    for selection in counts:
        if counts[selection] > threshold:
            final_selections.append(selection)

    return final_selections


def rate_selection(selection):
    # TODO: Implement this function
    # This should calculate the FDL and TSR metrics for the selection and return them in a tuple
    raise NotImplementedError


if __name__ == "__main__":

    usage = """USAGE: python3 py/experimentEnsemble.py <program> <version> <repetitions>
OPTIONS:
  <program> <version>: the target subject and its respective version.
    options: flex v3, grep v3, gzip v1, make v1, sed v6, chart v1, closure v1, lang v1, math v1, time v1
  <repetitions>: number of times the test suite reduction should be computed.
    options: positive integer value, e.g. 50"""

    if len(sys.argv) != 5:
        print(usage)
        exit()

    script, algorithm, prog, v, rep = sys.argv

    selections = {}

    selections['function'] = run_algorithm(script, 'function', algorithm, prog, v, rep)
    selections['line']     = run_algorithm(script, 'line',     algorithm, prog, v, rep)
    selections['branch']   = run_algorithm(script, 'branch',   algorithm, prog, v, rep)

    ensemble = ensemble_selections([selections[m] for m in selections])

    for method in selections:
        (fdl, tsr) = rate_selection(selections[method])
        print('Results with algorithm {} using {} coverage:'.format(algorithm, method))
        print('  Fault detection loss: {}'.format(fdl))
        print('  Test suite reduction: {}'.format(fdl))

    (fdl, tsr) = rate_selection(ensemble)
    print('Results with algorithm {} using ensembled results:'.format(algorithm))
    print('  Fault detection loss: {}'.format(fdl))
    print('  Test suite reduction: {}'.format(fdl))


