# Tools and example scripts for interacting with the BedreFlyt Digital Twin API

## Quick start
`process_data.py` simulates a sample, worst case and common case scenario with the provided scenario file.
By default this uses `scenarios.txt` to run 10 simulations at risk 0.5 and stores simulation results in `./results.json` for reuse.
```bash
python3 process_data.py
```
Use `python3 process_data.py --help` for more information

## Festschrift example
To run the illustrative example from the Festschrift with 100 simulations and risk 0.8, storing results in `/tmp/results.json` use:
``` bash
./process_data.py --scenario example_scenario.txt --results /tmp/results.json --repetitions 100 --risk 0.8
```

## Rebuilding
If changes are made to the contents of `z3/`, the Docker image will need to be rebuilt with:
``` bash
docker compose up -d --no-deps --build solver
```
