# AI Feature Implementation Workflow

This document outlines the standard operating procedure (SOP) and internal thought process of the AI Agent when handling a **new feature request**. It ensures consistency, safety, and transparency.

---

## 🧠 Phase 1: Intent Analysis & Context Loading (The "Brain")
**"Before I touch any file, I must understand the 'Why' and the 'Where'."**

1.  **Context Loading**:
    *   Read `AGENTS.md` to align with the project vision.
    *   Read `TODO.md` to check priority and dependencies.
    *   Read `REQUESTS.md` to see if this is a known requirement.
2.  **Intent Parsing**:
    *   What is the *core value* of this feature?
    *   Is this a "Quick Fix" or a "Major Feature"?
    *   Does this conflict with `investment-philosophy.md`?

## 🛡️ Phase 2: Safety & Consistency Check (The "Guardian")
**"First, do no harm."**

1.  **Protocol Enforcement (`.cursorrules`)**:
    *   Check: Am I allowed to edit these files? (Docs are protected).
    *   Check: Will this break existing tests?
    *   Check: Is the encoding safe? (Korean text preservation).
2.  **Risk Assessment**:
    *   **High Risk**: Database schema changes, core logic modification. -> **Requires detailed plan**.
    *   **Low Risk**: UI tweaks, new utility function. -> **Streamlined execution**.

## 📐 Phase 3: Technical Planning (The "Architect")
**"Measure twice, cut once."**

1.  **Drafting `implementation_plan.md`**:
    *   **Goal**: Define "Done".
    *   **Scope**: List exact files to be created/modified.
    *   **Strategy**: "Minimal Diff" approach (add new code rather than rewriting old).
2.  **User Review Loop**:
    *   **Stop**: Notify user (`notify_user`) and request approval for the plan.
    *   *Wait for user signal.*

## 🔨 Phase 4: Atomic Execution (The "Builder")
**"Precision engineering."**

1.  **Step-by-Step Implementation**:
    *   Create new files first.
    *   Implement dependencies next.
    *   Wire up the main logic last.
2.  **Invariant Protection**:
    *   Keep existing function signatures if possible.
    *   Use `TODO` comments for partial implementations.

## 🕵️ Phase 5: Strict Verification (The "Inspector")
**"Trust, but verify."**

1.  **Automated Verification**:
    *   Run `pytest` or specific script.
    *   Check for lint errors.
2.  **Manual Verification Sim**:
    *   "If I were the user, how would I test this?"
    *   Execute a dry-run command.
3.  **Proof of Work**:
    *   Generate `walkthrough.md` or capture screenshots/logs.

## 📚 Phase 6: Documentation & Handoff (The "Librarian")
**"Leave the campsite cleaner than you found it."**

1.  **Log Update**:
    *   Update `docs/development_log_YYYY-MM-DD.md`.
    *   Update `TODO.md` (Check off items).
2.  **User Notification**:
    *   "Here is what I did, here is how you test it, and here is what to do next."

---

## 🔄 Summary of "Mental Modes"

| Mode | Role | Key Question |
|:---|:---|:---|
| **PLANNING** | Architect | "How do I build this safely?" |
| **EXECUTION** | Builder | "How do I implement this with minimal diff?" |
| **VERIFICATION** | Inspector | "Does it actually work?" |
