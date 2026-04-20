---
name: strict-mode
description: Enforce strict code modification rules — only change what's discussed, replicate proven patterns exactly, never "improve" working code
disable-model-invocation: false
---

# STRICT MODE ACTIVATED

You MUST follow these rules for ALL code modifications in this conversation:

## Rule 1: Only Change What's Discussed
- ONLY modify code explicitly discussed in this conversation
- Make surgical, minimal changes — touch ONLY the lines related to the fix
- Treat the codebase as a finished product

## Rule 2: Replicate Proven Patterns Exactly
- BEFORE writing new code: scan ALL existing scripts for patterns that accomplish similar tasks
- IF a matching pattern exists: replicate it VERBATIM — same function calls, same parameters, same timing values, same structure
- IF no matching pattern exists: only then use your own judgment
- NEVER substitute a working pattern with a "better" or "more modern" alternative
- NEVER say "exact same code" unless you have verified EVERY line matches the original

## Rule 3: Never Modify Working Code
- NEVER refactor, "improve", optimize, or restructure code that already works
- NEVER change variable names, formatting, comments, imports, or logic flow unless explicitly asked
- NEVER remove features, functionality, or "unused" code
- NEVER introduce new dependencies or alternative approaches
- NEVER add error handling, comments, or type annotations to unchanged code

## Rule 4: Verify Before Claiming
- Before claiming code is "the same" as proven code, diff every parameter, value, and function call
- If you changed ANY value (timeout, max_workers, sleep duration, etc.) from the proven version, you MUST explicitly call it out
- Never silently change parameters while claiming the code is unchanged

## Execution Protocol
1. Identify ONLY the specific issue/feature being discussed
2. Locate the minimal code section that needs change
3. Verify what the PROVEN working version looks like
4. Make ONLY the surgical change discussed
5. Verify no unintended changes were made
6. Confirm all original features still present

## Forbidden Behaviors
- Rewriting working code "better"
- Consolidating or splitting functions unless requested
- Adding error handling unless discussed
- Removing "unused" code
- Changing working logic flow
- Optimizing performance unless explicitly asked
- Introducing new libraries or techniques
- Changing ANY parameter values from proven versions without explicit discussion
