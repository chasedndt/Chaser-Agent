# Model Licenses — Chaser Agent

Chaser Agent does **not bundle or redistribute any model weights**. It is a
source-intelligence and harness layer; model inference is performed by external
providers the operator configures (via their own credentials) or by local runtimes
the operator installs.

| Model / weights | Bundled? | Source | Licence |
|---|---|---|---|
| Pocket Alba (operator-supplied speech library) | No | `E:\Projects\Chaser Agent\Shared Speech Library` on this operator's machine; see that library's own receipts | See operator-supplied library notices; not redistributed here |
| Systran faster-whisper-tiny.en, revision `0d3d19a32d3338f10357c0889762bd8d64bbdeba` | No; explicit optional setup download to an external local directory | [Model repository](https://huggingface.co/Systran/faster-whisper-tiny.en/tree/0d3d19a32d3338f10357c0889762bd8d64bbdeba) | MIT per model card |

Any further model bundle or download path must be listed here with its source,
licence and usage restrictions (e.g. non-commercial or acceptable-use) surfaced
to the operator. Provider-hosted models are governed by the provider's terms,
not by Chaser Agent's MIT licence.

The `scripts/setup_local_stt.py --accept-download` path is an explicit one-time
download, not an implicit runtime fetch. It pins the revision and records SHA-256
hashes outside the repository. Model weights are not in this Git tree.
