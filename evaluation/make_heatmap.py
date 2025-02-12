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
    parser.add_argument('--oldFormat'
                        , action="store_true"
                        , default=False
                        , help="if set, use the data will be parsed with the old format (sorry)"
                        )
    args = parser.parse_args()

    ## collecting and organizing the data
    experiments = []
    for p in pathlib.Path(f'./{args.data}/').glob("*.json"):
        experiments += [{p.stem : json.loads(p.read_text())}]

    if args.oldFormat:
        values = [{'beds':int(beds), 'risk':key, 'unsat':float(sim['avgUnsatProp']), 'changes':float(sim['avgChanges'])}
                for experiment in experiments
                for beds, ex in experiment.items() if int(beds) <= 20
                for key, sim in ex.items() if key not in ["scenario", "repetitions"]]
        repetitions = [int(sim["repetitions"])
                for experiment in experiments
                for ex in experiment.values()
                for key, sim in ex.items() if key not in ["scenario", "repetitions"]]
    else:
        values = [{'beds':int(beds), 'risk': float(sim['risk']), 'unsat': float(sim['avgUnsatProp']), 'changes':float(sim['avgChanges']),}
                for experiment in experiments
                for beds, ex in experiment.items()
                for sim in ex["simulations"]]

        # these *should* all be the same, but lets take the average anyway just in case
        # maybe we're mixing data from different experiments
        repetitions = [int(ex["repetitions"]) for experiment in experiments for ex in experiment.values()]

    avgRep = sum(repetitions) / len(repetitions)

    ## plotting
    if args.store:
        mpl.use("pgf")
    else:
        mpl.use("QtAgg")

    # first plot the proportion of unsatisfiable days
    fig, ax = plt.subplots()
    data = pd.DataFrame(values).pivot(index='beds', columns='risk', values='unsat')
    unsat_hm = sns.heatmap(data, ax=ax, annot=True, fmt=".2f", cmap="flare")

    xlabels = [t.get_text() for t in unsat_hm.xaxis.get_ticklabels()]
    unsat_hm.set_xticklabels([f"{float(x):.1f}" for x in xlabels])
    unsat_hm.invert_yaxis()
    plt.title(f"Proportion of days in scenario with no solution (n={avgRep:.0f})")

    if args.store:
        plt.savefig(args.store + "_unsat.pgf")
    else:
        plt.show()

    fig, ax = plt.subplots()
    data = pd.DataFrame(values).pivot(index='beds', columns='risk', values='changes')
    changes_hm = sns.heatmap(data, ax=ax, annot=True, fmt=".1f", cmap="crest")

    xlabels = [t.get_text() for t in changes_hm.xaxis.get_ticklabels()]
    changes_hm.set_xticklabels([f"{float(x):.1f}" for x in xlabels])
    changes_hm.invert_yaxis()
    plt.title("Average number of bed changes per satisfiable day")

    if args.store:
        plt.savefig(args.store + "_changes.pgf")
    else:
        plt.show()
