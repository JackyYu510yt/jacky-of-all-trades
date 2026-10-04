## Principle 5 — KISS (Keep It Simple)

**Rule:** Pick the simplest solution that solves the present requirement. Every layer of abstraction, indirection, configuration, or "flexibility" must be justified by a concrete reason that exists *today* — not a hypothetical future one. Duplication beats the wrong abstraction. Wait for the rule of three before extracting.

**One-line form:** Simplest thing that works wins. Complexity needs a reason that exists right now.

### When it applies

- Designing a new component, function, class, or service from scratch.

- Refactoring tangled code, deciding whether to add an abstraction or live with duplication.

- Vibe-coding, prototyping, or any "just make it work" task where it's tempting to over-build.

- About to add a factory, registry, decorator, wrapper, base class, plugin system, or config layer.

- Choosing between inheritance and composition for a new class hierarchy.

- About to write a function longer than ~50 lines, or one that mixes I/O and business logic.

- Trigger phrases: "in case we need it later", "for future flexibility", "to make it extensible", "best practice", "let's make it generic", "this should be configurable", "what if we want to swap X someday", "I'll abstract this", "refactor this", "design pattern", "architecture", "let's build a framework", "vibe code this", "quick prototype", "just make it work".

### Failure modes this catches

- **Speculative generality** — code shaped for a use case that doesn't exist yet ("we might want to support YAML one day").

- **Premature abstraction** — extracting a base class or helper from two callers, then locking in the wrong shape when the third caller is different.

- **Pattern theatre** — applying a Factory / Strategy / Observer / Singleton because it's "best practice", when a dict / function / module-level value would do the same job in a fraction of the code.

- **Layer inflation** — wrapping every operation in service → repository → adapter → port when the project has one database and one caller.

- **Config-itis** — exposing a knob for a value that has only ever held one setting, "in case it changes later".

- **God class / megafunction** — opposite failure: cramming HTTP parsing, validation, business logic, DB access, and response formatting into one unit because "splitting it feels like overkill". Both extremes are KISS violations — the right size is one reason to change.

- **Inheritance trees for behavior reuse** — three-deep class hierarchies where one composed object would do.

- **Clever one-liner** — a comprehension or generator chain that takes five minutes to read; the loop version reads in five seconds.

- **Wrapping working code** — adding a helper / decorator / facade around code that already works, because the wrapper "feels cleaner". It isn't, and now the caller has two things to learn instead of one.

### Check / gate before adding complexity

Answer each in one sentence. If any answer is "no" or "I don't know", do the simpler thing.

1. **Can I name the concrete present-day problem this complexity solves?** Not a future-tense problem. A real one, today, in this codebase. If the only justification is "future flexibility", cut it.

2. **Does the simpler version actually fail to meet a stated requirement?** Run the simpler version mentally — what specifically breaks? If nothing breaks, the simpler version wins.

3. **Have I seen this pattern at least three times?** (Rule of three.) Two similar callers is duplication. Three is a pattern. One is fantasy. Wait for the third before extracting — unless the duplicates are already diverging in dangerous ways.

4. **If I'm splitting a unit: does each piece have one reason to change, in one domain?** HTTP parsing AND business logic AND SQL in one class is too many. But splitting "validate" from "save" inside one domain is often pointless. The test is "different reasons to change", not "different verbs".

5. **If I'm composing vs inheriting: would composition work?** Default to composition. Reach for inheritance only when there is a true is-a relationship AND you need polymorphism the language gives you for free. Almost never on first draft.

6. **Senior-engineer test:** would a senior engineer reading this say it's overcomplicated? If yes, it is. Cut.

### Common invalid patterns

- Two callers, extract a shared helper "for consistency" → invalid (rule of three).

- `OutputFormatterFactory.register("json")` for three formatters with no plugin system in sight → invalid (a dict beats it).

- `class BaseService` with one subclass → invalid (just be the class).

- `def get_user_by_id_with_cache_and_retry_and_logging(...)` mixing I/O, caching, retries, and logging → invalid (split, or use middleware/composition).

- `config.yaml` exposing 14 knobs that have never been changed in production → invalid (inline the defaults until someone needs to override).

- Adding an interface / Protocol with one implementation "in case we want to mock it" → invalid (mock the concrete one or pass a fake — the Protocol can come when there's a second impl).

- Wrapping a stdlib call in a 20-line helper that adds nothing the stdlib doesn't already give you → invalid.

- Replacing a 6-line for-loop with a nested comprehension that takes 30 seconds to parse → invalid (clever ≠ simple).

- 200 lines where 50 would do the job → invalid (rewrite it; if your draft is 4× the necessary size, the design is wrong).

- `try / except` blocks for failure modes that cannot occur (e.g. catching `ZeroDivisionError` on a literal `1 / 2`) → invalid (no error handling for impossible scenarios).

### Hard NOs

- Do not add a layer, abstraction, or pattern whose only justification is "we might need it later".

- Do not extract a shared abstraction from two callers — wait for the third, OR until divergence is causing bugs.

- Do not use inheritance when composition works, on first draft.

- Do not split a class until you can name two separate reasons-to-change in two separate domains.

- Do not mix HTTP parsing, business logic, and data access in the same unit — that's the *one* split that is non-negotiable.

- Do not wrap working code in a "cleaner" facade unless the wrapper removes a concrete pain (not a stylistic preference).

- Do not write clever code where plain code reads in half the time.

- Do not introduce a config knob for a value that has never varied.

- Do not call this rule "satisfied" because the code is *short*. Short clever code can still be a KISS violation. The test is **readable in one pass and justified by today's need.**

- Do not write error handling for failure modes that cannot occur. `try/except` exists to handle real failure surfaces, not to look defensive.

### Worked examples

**A — Factory vs dict**

Situation: Need to pick a formatter (`json`, `csv`, `xml`) by name.

- ❌ Build `FormatterFactory` with a `@register` decorator and a class registry.

- ✅ `FORMATTERS = {"json": JsonFormatter, "csv": CsvFormatter, "xml": XmlFormatter}` plus a four-line `get_formatter(name)`. Promote to a factory only when there's a real plugin loader, not because "factories are better".

**B — Inheritance vs composition for notifications**

Situation: Need to send notifications via email, with SMS and push planned later.

- ❌ `NotificationService` base class, subclass `EmailNotificationService`, subclass `SmsNotificationService`, override `notify()` in each.

- ✅ One `NotificationService` that takes injected `email_sender`, optional `sms_sender`, optional `push_sender`. Add channels by passing more senders, not by adding subclasses.

**C — Premature extraction (rule of three)**

Situation: Two functions, `process_orders` and `process_returns`, look structurally similar.

- ❌ Extract `_process_collection(items, validate, process)` because "DRY".

- ✅ Leave the duplication. The validation and processing rules are domain-specific and likely to drift apart. Wait for a third real case before deciding there's a pattern.

**D — God function refactor**

Situation: `process_order(order)` is 140 lines: validation, inventory, payment, notification, logging.

- ❌ Leave it because "splitting feels like overkill" — KISS doesn't mean "refuse to split".

- ✅ Five focused calls inside `process_order`: `validate_order(order)`, `reserve_inventory(order)`, `charge_payment(order)`, `send_confirmation(...)`, return result. Each function does one thing; `process_order` reads like a table of contents.

**E — Vibe-coding and "best practice" drift**

Situation: User says "vibe code a quick script that downloads a CSV and prints the rows".

- ❌ Set up a `Downloader` class, a `Parser` class, a `dataclass` for rows, an `argparse` CLI, a `logging` config, a `pyproject.toml`.

- ✅ A 15-line script: `requests.get`, `csv.reader`, a for-loop, a `print`. If the user asks for more, add it then. KISS at prototype stage means YAGNI is on by default.

**F — Optional Protocol with one impl**

Situation: One service uses one cache. Tempted to define a `Cache` Protocol so it's "swappable".

- ❌ `class Cache(Protocol): ...` plus `RedisCache(Cache)` plus injected `Cache` everywhere, with one implementation.

- ✅ Inject `RedisCache` directly. If a second cache implementation appears (rule of three: a real test fake counts as one), introduce the Protocol then. Mocking does NOT require a Protocol — `unittest.mock` patches the concrete class fine.

### Relationship to the other principles

- **P2** defines what success looks like. KISS asks: *what's the simplest thing that meets that definition?* Anything beyond that is decoration.

- **P3** keeps every action traceable to the goal. KISS is a sub-rule of P3 for the *code itself* — every layer of code must trace to a present requirement, not a hypothetical one.

- **P4** audits state vs goal at handback. If the audit shows the goal is met but the code is heavier than it needs to be, the verdict is **PARTIAL** with a "simplify" pending — not DONE.

- **`simplify` skill** — the runtime tool for applying KISS to a code change. This principle is the standard; `simplify` is the procedure.

- **`strict-mode` skill** — forbids drive-by improvements. KISS forbids drive-by *abstractions*. They're complementary: don't change what wasn't asked, AND don't add what isn't needed.

### Origin

Surfaced 2026-04-25 during a discussion of vibe-coding and keeping prototypes from ballooning. Pattern observed across multiple sessions: the user explicitly asks for "simple" or "quick" work, and the default response reaches for factories, base classes, configurable knobs, and Protocols-with-one-impl — all of which are "best practice" in the abstract but pure overhead for the actual job. The user's existing memories already encode this preference (KISS-first optimization, smallest change biggest dial, no overengineering); promoting it to a Principle puts it on the same checkpoint footing as P1–P4, so it gets actively applied at design time, not retrofitted by a later cleanup pass.

Reinforced same day by absorbing the **"Simplicity First"** principle from Andrej Karpathy's CLAUDE.md (forrestchang/andrej-karpathy-skills): the senior-engineer overcomplication test, the "200 lines could be 50, rewrite it" check, and "no error handling for impossible scenarios" all live here as a result.


`========================================`
