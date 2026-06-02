# Architecture

`agent-ops-kit` is deliberately small and readable. Every module does one
thing, and the orchestration in `agent.py` is the only place they meet.

## Modules

| Module | Responsibility |
|---|---|
| `_match.py` | Lexical relevance scoring (`relevance()`), shared by routing, guide loading, and memory recall. Tokenize → overlap → keyword boost → normalize by query length. No embeddings dependency. |
| `frontmatter.py` | Parse the small YAML-frontmatter dialect used by every resource file (scalars + inline lists). |
| `skills.py` | `Skill` (a markdown unit of instruction) and `SkillRegistry.route()`, pick the top-N relevant skills above a threshold. |
| `guides.py` | `Guide` + `GuideLibrary.relevant()`, index guides cheaply, load full text only when a request matches. |
| `memory.py` | `MemoryStore` over a directory of markdown facts. `recall()` (read) and `learn()` (write-back, persisted). |
| `permissions.py` | `Permissions.load()` merges a durable layer with a local layer; `is_allowed()` is default-deny with `deny` winning over `allow`, supporting `*` suffix wildcards. |
| `hooks.py` | `HookRegistry` with a `session_start` lifecycle point and a built-in orientation hook. |
| `llm.py` | The `LLMClient` protocol, the real `AnthropicLLM` (Messages API + prompt caching), and the offline `EchoLLM`. |
| `agent.py` | `Agent` orchestrator. `plan()` makes all the routing/loading/recall decisions and assembles the system prompt; `run()` calls the backend; `learn()` writes memory. |

## The routing algorithm

All three "what's relevant?" decisions (skills, guides, memory) use the same
`relevance()` function:

```
score = (Σ query-token overlaps with the resource text
         + 2 x exact keyword/trigger hits) / number of query tokens
```

- Curated `triggers`/`keywords` are weighted 2x because a hit there is a
  stronger signal than incidental prose overlap.
- Normalizing by query length keeps long questions from inflating scores, so a
  single threshold (default `0.3`) works across short and long requests.
- It's intentionally explainable: you can read a score and know why a skill
  fired. Swapping in an embedding model means replacing this one function.

## Prompt-cache strategy

Prompt caching is a prefix match, any byte change in the prefix invalidates
everything after it. So `agent.plan()` assembles the system prompt in two tiers:

1. **Stable prefix (cache-eligible):** framework instructions → domain config →
   loaded guides. These rarely change between requests in a session.
2. **Volatile suffix:** orientation, the routed skills' instructions, recalled
   memory. These vary per request.

`AnthropicLLM._build_system()` orders all stable blocks first and places a
single `cache_control: {"type": "ephemeral"}` breakpoint on the *last* stable
block, caching everything up to and including it. On repeated requests within
the cache window, the expensive stable context is served from cache (~0.1x
cost) while only the small volatile tail is processed fresh.

The model call itself uses adaptive thinking (`thinking: {"type": "adaptive"}`)
with `effort: "high"` on `claude-opus-4-8`.

## Extension points

- **New domain** → new workspace directory. No framework code.
- **New lifecycle behavior** → register a `session_start` hook.
- **Different relevance model** → replace `_match.relevance()`.
- **Different LLM backend** → implement the `LLMClient` protocol.

## Testing

`EchoLLM` makes the entire pipeline runnable with no API key, so the 26-test
suite (`tests/`) exercises routing, guide loading, memory round-trips,
permission merging, and prompt assembly offline and deterministically.
