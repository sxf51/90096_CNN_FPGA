# Reproducing frozen HLS evidence

Completed IDs are immutable. Their recorded tool commands describe the original
execution; running those IDs again is deliberately rejected. From the repository
root on `exp/explore-arch`, use the replay entry point:

```sh
python3 exp/reproduce_exp.py F08 --run
python3 exp/reproduce_exp.py E043 --run
```

Each command allocates a new direction-prefixed ID at or above100, commits a paper
plan, copies the archived design, restores testbench/reference code from the
recorded source commit, then runs the existing remote experiment runner. Inputs,
weights, thresholds, flags and original evidence remain unchanged. New work is
archived and committed separately. An explicit unused ID can be supplied with
`--id`; omit `--run` to prepare a reviewable replay without invoking Vitis.

Implementation/cosim replay automatically synthesizes a fresh frozen parent
before verification. Protected binary datasets and the original Git source
commit must be present. Missing data/source fails explicitly. The existing SSH
configuration and Linux Vitis2026.1 installation are the verified environment.

For a local Windows installation, the runner supports this form, which has not
been executed on Windows:

```powershell
python exp/reproduce_exp.py F08 --run --local --settings C:/AMDDesignTools/2026.1/Vitis/settings64.bat
```

Model analyses retain their documented Python commands. Figures are rerunnable
with `exp/plots/*.py` and read CSV files only; no HLS rerun is needed for plotting.
The missing comic pair still prevents complete Set14 acceptance.

## Recovering completed remote jobs

If SSH or the local queue stopped after a remote job finished, inspect its
processes and archive before resuming. Retrieve the completed result without
uploading sources or launching Vitis:

```sh
python3 exp/remote_exp.py exp/configs/F85.json --collect-only
```

Collection requires a remote metrics archive and no active run lock. It checks
the original paper plan and result identity, appends the CSV record once, updates
progress and commits with the experiment ID. Repeated collection accepts only an
identical existing row; conflicting evidence fails. Continue genuinely unstarted
IDs with `exp/run_queue.py`; completed workspaces remain reserved.
