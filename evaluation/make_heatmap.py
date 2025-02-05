#!/usr/bin/env python3

import json
import pathlib
import argparse

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib as mpl

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--data'
                        , help="path to directory of results of the form [number_of_cat_3_beds].json"
                        )
    parser.add_argument('--store'
                        , help="path to store resulting heatmap")
    args = parser.parse_args()

    ## collecting and organizing the data
    experiments = []
    for p in pathlib.Path(f'./{args.data}/').glob("*.json"):
        experiments += [{p.stem : json.loads(p.read_text())}]

    values = [{'beds':int(beds), 'risk':risk, 'unsatDays':float(sim['avgUnsatProp']), 'changes':float(sim['avgChanges'])}
              for experiment in experiments
              for beds, ex in experiment.items()
              for risk, sim in ex.items()
              ]

    ## plotting
    if args.store:
        mpl.use("pgf")
    else:
        mpl.use("QtAgg")

    # first plot the proportion of unsatisfiable days
    fig, ax = plt.subplots()
    data = pd.DataFrame(values).pivot(index='beds', columns='risk', values='unsatDays')
    unsat_hm = sns.heatmap(data, ax=ax, vmin=0, vmax=1, annot=True, fmt=".2f", cmap="flare")

    xlabels = [t.get_text() for t in unsat_hm.xaxis.get_ticklabels()]
    unsat_hm.set_xticklabels([f"{float(x):.1f}" for x in xlabels])
    unsat_hm.invert_yaxis()
    plt.title("Proportion of days in scenario with no solution")

    if args.store:
        plt.savefig(args.store + "_unsat.pgf")
    else:
        plt.show()

    # then the number of bed changes (this turns out not to be very interesting)
    fig, ax = plt.subplots()
    data = pd.DataFrame(values).pivot(index='beds', columns='risk', values='changes')
    changes_hm = sns.heatmap(data, ax=ax, annot=True, fmt=".1f", cmap="crest")

    xlabels = [t.get_text() for t in changes_hm.xaxis.get_ticklabels()]
    changes_hm.set_xticklabels([f"{float(x):.1f}" for x in xlabels])
    changes_hm.invert_yaxis()
    plt.title("Number of bed changes")

    if args.store:
        plt.savefig(args.store + "_changes.pgf")
    else:
        plt.show()
