# Pet Studio Orchestration Plan

This is the near-term plan for turning the widget app plus roost into a small
local orchestration layer. It is a plan, not a promise that every item exists.

## Shape

```text
Pet Studio
  Project A
    roost shared state and local classifier
    staff pool assignments
    selected lead endpoint
  Project B
    same roost instance
    different queue and assignments
```

roost is shared. Do not create one LLM or one state manager per project.

## Roles

| Role | Instance | Backend | Job |
| --- | --- | --- | --- |
| roost | shared | script first, optional local LLM/Hermes | queue, event, security, routing hints |
| Staff | pooled | API or local adapter later | execute assigned project tasks |
| Lead | per project | user-selected Codex/Claude/Cursor/etc. | final judgment and implementation |

Rules:

- Script mode must work without an LLM.
- Staff are pooled, then assigned to projects.
- The lead is configurable; do not hardcode Codex as the only lead.
- Backend adapters must share a small interface.

## Security

Per-project security level:

| Level | Behavior |
| --- | --- |
| L0 Allow | allow risky actions |
| L1 Warn | log risky actions, then allow |
| L2 Ask | raise `SecurityError` for risky actions |
| L3 Deny | block risky actions |

Default is L1.

## State

`team_state.json` owns:

- projects
- queues
- event history
- staff records
- security level
- trust field for future auto-approval

`log_event()` records context automatically. Callers should not manually push
context history unless they are migrating old data.

## Backend Interface

Backends classify events with:

```python
classify_event(event, context=None)
```

Current backends:

- `ScriptBackend`: deterministic fallback
- `HermesBackend`: optional subprocess adapter

Future adapters may include Ollama, llama.cpp, vLLM, or remote APIs, but only
after a real call site needs them.

## Milestones

| Version | Target |
| --- | --- |
| 0.6.0 | roost state, presets, security, script/Hermes classifiers, Team Room panel, approval queue |
| 0.7 | Project Hub, mission input, Task Cards, Codex packet export |
| 0.8+ | richer endpoint aliases, trust automation, imported skill review |

## Out Of Scope For Now

- per-project LLM instances
- real-time multi-project monitoring
- cloud sync
- hosted dashboard
- autonomous tool execution without the security layer
