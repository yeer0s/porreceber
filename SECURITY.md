# Security & privacy

## The threat this is designed against

A person analysing an old debt is telling the tool who they owe, how much, since
when, and whether they ever acknowledged it. That is a financial-distress profile —
exactly the material a debt-collection industry would pay for. The design
assumption is that **none of it leaves the user's machine**, including to us.

There is a second, sharper threat: a person in this situation is vulnerable to
being told what they want to hear. A tool that cheerfully announced "your debt is
extinguished" would cause more damage than one that leaked data, because they
would stop opening the letters. That is why "never declare a debt extinguished"
is enforced as a **test**, not a guideline.

## Guarantees, and how they are enforced

| Guarantee | Enforcement |
|---|---|
| No network calls | `scripts/offline_audit.py` parses every shipped file and fails on any networking/`subprocess`/`ctypes` import. Wired into CI |
| No dynamic execution | The same audit fails on builtin `eval`/`exec`/`__import__` |
| No shell-out | Fails on `os.system`, `os.popen`, `os.exec*`, `importlib.import_module` |
| Offline at runtime, not just in theory | CI re-runs **every gate with the socket layer disabled**. Any attempted connection crashes the build |
| No dependencies | Standard library only |
| No telemetry | There is no analytics and no code that could add it without failing the audit |
| Never declares a debt extinguished | `nunca-declara-divida-extinta` in `sweep.py`, with a dedicated mutant in `mutants.py` that proves the check bites |
| Always warns that payment is irreversible | `decorrido-avisa-sempre-art-304`, likewise mutant-tested |
| Every regime cites real captured statute | `regimes-citam-artigos-capturados` — a fabricated article number fails the build |

Verify all of it yourself:

```bash
python scripts/offline_audit.py --selftest   # prove the audit can fail
python scripts/offline_audit.py              # then trust that it didn't
python scripts/mutants.py                    # prove the product invariants bite
```

## What this is not

The offline audit is a **static** audit, not a sandbox. It catches the accidental
and the obvious: a networking import, a shell-out, a dynamic import, a builtin
`eval`. It is **not** a defence against a determined malicious contributor, who
has many routes to a network that no import-level check can see.

The real control there is that this is a small repository where every pull
request is read. Said plainly, rather than implying the audit is a security
boundary it isn't.

Likewise: the engine is only as correct as the **category you choose**. It cannot
verify the legal characterisation of your debt, and mischaracterisation is the
largest source of wrong answers. That is a declared blind spot
(`python scripts/oracle.py --blind-spots`), not a solved problem.

## Reporting a vulnerability

Open a private security advisory on GitHub, or email the address on
[mowei.pt](https://mowei.pt). Please include what you ran and what happened.

The following are treated as security-grade defects, not ordinary bugs:

- any path by which user data could leave the machine;
- any input that makes the engine assert a debt is extinguished;
- any input that suppresses the art. 304.º n.º 2 warning when a period has run;
- any regime citing an article that is not in `assets/law/`.

## Supported versions

The `main` branch. This is a small project — there are no backported branches.
