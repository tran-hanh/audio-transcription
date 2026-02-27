# How BMAD Agents Work Together

This project uses multiple BMAD agents (Analyst, PM, Architect, Scrum Master, Developer, QA, Tech Writer, Quick Flow, UX Designer). They work together in two ways: **sequential workflows** (handoffs by phase) and **Party Mode** (multi-agent discussion in one conversation).

---

## 1. Sequential handoffs (phase order)

Agents collaborate by **phase**: each workflow produces artifacts that the next agent uses. Run the right **slash command** (or load the right agent) in order.

| Phase | Who | What | Command / Agent |
|-------|-----|------|------------------|
| **1 – Analysis** | Mary (Analyst) | Brainstorm, research, product brief | `/bmad-brainstorming`, `/bmad-bmm-market-research`, `/bmad-bmm-create-product-brief`, etc. |
| **2 – Planning** | John (PM) | PRD, validate PRD, UX (Sally) | `/bmad-bmm-create-prd`, `/bmad-bmm-validate-prd`, `/bmad-bmm-create-ux-design` |
| **3 – Solutioning** | Winston (Architect), John (PM) | Architecture, epics & stories, readiness | `/bmad-bmm-create-architecture`, `/bmad-bmm-create-epics-and-stories`, `/bmad-bmm-check-implementation-readiness` |
| **4 – Implementation** | Bob (SM) → Amelia (Dev) → Quinn (QA) | Sprint plan, stories, dev, tests, code review | `/bmad-bmm-sprint-planning`, `/bmad-bmm-create-story`, `/bmad-bmm-dev-story`, `/bmad-bmm-qa-automate`, `/bmad-bmm-code-review` |
| **Anytime** | Paige (Tech Writer), Mary (Analyst), Barry (Quick Flow) | Docs, project context, quick spec/dev | `/bmad-agent-bmm-tech-writer`, `/bmad-bmm-document-project`, `/bmad-bmm-generate-project-context`, `/bmad-bmm-quick-spec`, `/bmad-bmm-quick-dev` |

**Flow:** PRD → Architecture → Epics & Stories → Sprint plan → Create Story → Dev Story → (Validate Story) → Code Review → next story or Retrospective. Artifacts live in `_bmad-output/planning-artifacts` and `_bmad-output/implementation-artifacts`.

**To stay on track:** Use `/bmad-help` (e.g. `/bmad-help what should I do next`) to see the next suggested step based on what’s done.

---

## 2. Party Mode (multi-agent discussion)

When you want **several agents to discuss one topic** in a single conversation (e.g. “Is this architecture right?”, “Improve this PRD section”), use **Party Mode**:

1. From **BMad Master**: choose **[PM] Start Party Mode** (or say “party mode”).
2. Or run: **`/bmad-party-mode`**.

A facilitator will bring in the right agents; you can ask questions and get different perspectives (Architect, PM, Developer, QA, etc.) in one thread. Some workflows (e.g. Create PRD, Create Architecture, Create Brief) also offer **“P” for Party Mode** to refine the current artifact with the whole team.

---

## 3. Quick reference

- **Orchestrator:** BMad Master – `/bmad-agent-bmad-master` → menu for List Tasks, List Workflows, Party Mode, Chat, Help.
- **What’s next?** `/bmad-help` or `/bmad-help [your question]`.
- **Multi-agent discussion:** `/bmad-party-mode` or Master → [PM].
- **Full sequence:** Follow BMM phases 1 → 2 → 3 → 4; use `/bmad-help` to decide the next step.

All agents use the same project context and standards (see CONTRIBUTING.md and agent memories in `_bmad/_config/agents/*.customize.yaml`).
