# Agent School: Session 4 - Multi-Agent Systems

Welcome to **Session 4** of the Agent School curriculum, designed specifically for **Technical Sales Professionals, Customer Engineers, and Solutions Architects**.

In this module, you will learn how to articulate the value proposition, architectural design patterns, and enterprise use cases for **Multi-Agent Systems** built with the Google Agent Development Kit (ADK 3.12).

---

## Why Multi-Agent Systems? (The Sales Pitch)

Single LLM agents are powerful, but they can become monolithic, difficult to debug, and prone to hallucination when burdened with too many disparate tools and instructions.

**Multi-Agent Architectures solve this by introducing:**
1. **Specialization**: Each sub-agent has a narrow, focused scope, specific tools, and optimized instructions. This dramatically increases accuracy and reliability.
2. **Modularity**: Teams can develop, test, and update individual agent components without risking regression across the entire system.
3. **Efficiency**: Complex workflows can be broken down into parallel tasks or sequential pipelines, optimizing latency and token usage.

---

## Core Architecture Patterns (7 Enterprise Deployed Patterns)

This repository provides complete, runnable ADK implementations of seven fundamental multi-agent patterns.

---

### 1. Coordination / Dispatcher Pattern
- **Concept**: A central LLM agent acts as a "router" or coordinator, managing a suite of specialized expert sub-agents.
- **How it Works**: It interprets ambiguous user intent and dynamically delegates execution to the correct specialist.
- **Value**: Excellent for Customer Service Portals, IT Helpdesks, and Multi-domain Virtual Assistants.

### 2. Sequential Pipeline Pattern
- **Concept**: An orchestrator (`SequentialAgent`) executes a series of sub-agents in a strictly predefined order.
- **How it Works**: Agents share the same `InvocationContext` and pass structured data sequentially via shared session state.
- **Value**: Ideal for Data ETL pipelines, Document Processing workflows, and Multi-stage Code Auditing.

### 3. Parallel Fan-out / Gather Pattern
- **Concept**: An orchestrator (`ParallelAgent`) triggers multiple sub-agents to run concurrently on distinct context branches.
- **How it Works**: Sub-agents perform independent tasks simultaneously, reducing latency, followed by a synthesis step.
- **Value**: Crucial for Executive Briefings, Comprehensive Research / Threat Analysis, and Multi-source Intelligence Gathering.

### 4. Hierarchical Task Decomposition
- **Concept**: A multi-level parent_agent/sub_agents tree where higher-level agents break down complex goals and delegate tasks.
- **How it Works**: Parent agents use `AgentTool` to invoke child agents as tools. Results flow back up the tree for synthesis.
- **Value**: Perfect for structured content writing, large-scale software design, and highly complex problem decomposition.

### 5. Review / Critique Pattern (Generator-Critic)
- **Concept**: A sequential workflow pairing a Generator that drafts content and a Reviewer/Critic that evaluates the output.
- **How it Works**: Generator saves to `"draft_text"`; Reviewer fact-checks `"draft_text"` and sets `"review_status"`.
- **Value**: Enforces strict quality assurance, formatting compliance, and factual accuracy in automated content workflows.

### 6. Iterative Refinement Pattern
- **Concept**: LoopAgent contains generator and checker agents executing repeatedly over a task until a threshold is met.
- **How it Works**: The generator writes code and uses `BuiltInCodeExecutor` to self-verify. The checker reviews and the loop stops once quality passes.
- **Value**: Essential for automated code refinement, document polishing, and self-correcting automation tasks.

### 7. Human-in-the-Loop (HITL) Pattern
- **Concept**: Integrates human intervention, oversight, or approval points within an agent workflow.
- **How it Works**: A tool is invoked which asynchronously waits or requests human input. The workflow pauses and resumes only upon receiving approval.
- **Value**: Crucial for high-risk transactions, spend approval systems, infrastructure deletions, and administrative governance.

---

## How to Run the Demonstrations via ADK Web UI

To showcase these patterns to clients using the premium graphical UI, ensure you are using a virtual environment with google-adk and launch the dev UI server:

```bash
# Start the ADK Web Server
adk web
```

Access the UI at **http://127.0.0.1:8000** to interactively test and demonstrate all seven patterns!

---

## Discussion Guide for Customer Conversations

When speaking with enterprise clients about Multi-Agent Systems, focus on these key discussion points:

1. **"How do you handle complex, multi-step business processes today?"**
   - *Positioning*: Explain how the **Sequential Pipeline Pattern** replaces rigid scripts with adaptive, intelligent stages that handle edge cases gracefully.

2. **"Are your users overwhelmed by having to select from dozens of specialized AI bots?"**
   - *Positioning*: Highlight the **Coordination / Dispatcher Pattern** as a unified frontdoor that dynamically delegates work to the correct specialists without user friction.

3. **"How do you guarantee reliability, truthfulness, and prevent AI hallucinations in content workflows?"**
   - *Positioning*: Pitch the **Generator-Critic** and **Iterative Refinement** patterns as automated self-correcting loops that continuously test, review, and polish outputs until they meet perfect standards.

4. **"How do you maintain governance and prevent AI agents from taking unauthorized high-risk actions?"**
   - *Positioning*: Explain how the **Human-in-the-Loop Pattern** integrates policy gates, pausing agent execution before sensitive operations to request explicit human review.
