# Host rules: irteam GPU server

Installed by `ar_init` to `~/.config/ar/host.md` on machines where persist.py exists.

## GPU jobs: notify persist.py

`/home1/irteam/data-vol1/persist.py` fills idle GPUs with synthetic load (~90% memory). Any GPU job (training, eval, inference, benchmarks) MUST notify it before touching the GPU, or it may OOM:

- Shell: `python /home1/irteam/data-vol1/persist_notify.py run -- <your command>`
- Python: `sys.path.insert(0, "/home1/irteam/data-vol1"); from persist_notify import gpu_claim` then `with gpu_claim("<exp-name>"): ...`
- Manual: `persist_notify.py start <tag>` before, `persist_notify.py done <tag>` after.

persist pauses within ~2s on a claim and resumes when the claim is released. Unannounced jobs are only detected by an nvidia-smi check every 30s.
