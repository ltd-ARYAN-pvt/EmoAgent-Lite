# EmoAgent Lite 🤖💬

### A modular, multi-agent conversational system built with LangGraph and Ollama

> **EmoAgent Lite** is an evolving multi-agent project for experimenting
> with conversational roles, monitoring, character-driven interaction,
> and evaluation. It starts with two agents discussing a topic and grows
> in planned versions toward a monitored, user-facing emotional-support
> research prototype.

```{=html}
<p align="center">
```
`<a href="#-project-roadmap">`{=html}Roadmap`</a>`{=html} ·
`<a href="#-architecture">`{=html}Architecture`</a>`{=html} ·
`<a href="#-quick-start">`{=html}Quick start`</a>`{=html} ·
`<a href="#-project-structure">`{=html}Project structure`</a>`{=html} ·
`<a href="#-safety-and-scope">`{=html}Safety`</a>`{=html}
```{=html}
</p>
```
```{=html}
<!-- Replace these placeholders with your repository details when publishing. -->
```
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Orchestration](https://img.shields.io/badge/Orchestration-LangGraph-6A5ACD)
![LLM Runtime](https://img.shields.io/badge/Local%20LLM-Ollama-black)
![Status](https://img.shields.io/badge/Status-V1%20in%20development-orange)

------------------------------------------------------------------------

## 📚 Contents

-   [🎯 Project goals](#-project-goals)
-   [🗺️ Project roadmap](#-project-roadmap)
-   [🏗️ Architecture](#-architecture)
-   [🧠 Core concepts](#-core-concepts)
-   [📁 Project structure](#-project-structure)
-   [⚙️ Requirements](#️-requirements)
-   [🚀 Quick start](#-quick-start)
-   [🧪 Run and test](#-run-and-test)
-   [🧩 How the agent module works](#-how-the-agent-module-works)
-   [🔐 Safety and scope](#-safety-and-scope)
-   [🛣️ Current status and next steps](#️-current-status-and-next-steps)

------------------------------------------------------------------------

## 🎯 Project goals

EmoAgent Lite is being developed incrementally, with each version adding
one major capability instead of building the entire system at once.

-   **Learn agent orchestration:** understand how LangGraph nodes,
    shared state, edges, and conditional routing work.
-   **Experiment with distinct roles:** use prompts to give agents
    different conversational personalities.
-   **Keep the system modular:** separate model configuration, agent
    behavior, state, routing, API, and UI.
-   **Support local development:** use Ollama to run a model locally.
-   **Build toward evaluation:** add monitoring and evaluation agents
    before integrating the backend and frontend.
-   **Make progress measurable:** keep each version testable and
    document its results.

## 🗺️ Project roadmap

The roadmap is intentionally versioned. A future version is a **planned
capability**, not a claim that it is already implemented.

```{=html}
<details open>
```
```{=html}
<summary>
```
`<strong>`{=html}V1 --- Agent Conversation (current
foundation)`</strong>`{=html}
```{=html}
</summary>
```
**Goal:** Create a LangGraph workflow in which two prompted agents
discuss a user-supplied topic.

**Planned / core behavior** - Agent A: optimistic, curious, constructive
researcher. - Agent B: analytical, thoughtful, constructively critical
thinker. - Shared conversation state with message history. - Alternating
Agent A / Agent B turns. - Configurable maximum response count. - Ollama
integration through LangChain's `ChatOllama`. - Empty-response checks
and basic debugging output.

**Concepts learned:** `StateGraph`, `START`, `END`, nodes, conditional
edges, reducers, `ChatState`, prompts, and `llm.invoke()`.

**V1 completion checklist** - \[ \] Run both agents through a complete
conversation. - \[ \] Verify the response limit stops the graph at the
expected turn. - \[ \] Test empty or malformed model responses. - \[ \]
Add automated tests for routing and state updates. - \[ \] Record
example conversations and known limitations.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}V2 --- Monitor Agent, Character Agent, and User
Interaction with PHQ-9 data`</strong>`{=html}
```{=html}
</summary>
```
**Goal:** Move beyond a two-agent discussion and explore a user-facing,
character-driven interaction with a monitoring component.

Potential components: - **Character Agent:** maintains a consistent
conversational role and communicates with the user. - **Monitor Agent:**
observes conversation flow and checks configured interaction rules,
quality signals, or safety conditions. - **User interaction:** enables a
user to converse with the character agent. - **PHQ-9 data handling:**
explore how a user-provided PHQ-9 questionnaire result could be
represented and used as structured context, only with appropriate
consent, privacy protections, and careful limits.

**Design questions to settle before implementation** - What is the
Monitor Agent allowed to inspect, flag, or change? - Does monitoring run
after every turn or only at specific checkpoints? - How is questionnaire
data collected, stored, minimized, and deleted? - What should happen
when the user expresses distress or an urgent safety concern? - How will
the system avoid presenting a questionnaire score as a diagnosis?

**V2 exit criteria** - \[ \] Define clear responsibilities and
boundaries for each agent. - \[ \] Define a typed state schema for user
messages, character replies, and monitoring results. - \[ \] Document
consent and data-retention behavior before storing sensitive
information. - \[ \] Test monitor decisions against a small, reviewed
set of scenarios. - \[ \] Keep a human-support pathway visible where
appropriate.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}V3 --- EmoGuard and EmoEval Agents`</strong>`{=html}
```{=html}
</summary>
```
**Goal:** Introduce dedicated agents for guardrails and evaluation.

-   **EmoGuard Agent:** checks interaction outputs against defined
    safety, privacy, and behavior policies. It should flag or route
    concerning cases rather than pretending to provide clinical
    judgment.
-   **EmoEval Agent:** evaluates conversation quality against explicit
    criteria such as relevance, empathy, consistency, instruction
    following, and policy compliance.
-   **Evaluation workflow:** use structured outputs and test cases so
    results can be compared across prompt or model changes.

**V3 exit criteria** - \[ \] Define structured schemas for guard and
evaluation outputs. - \[ \] Create a small, documented test set with
expected outcomes. - \[ \] Measure false positives and false negatives
where applicable. - \[ \] Log evaluation results without unnecessarily
retaining sensitive conversation content. - \[ \] Keep evaluation
separate from user-facing claims of clinical effectiveness.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}V4 --- Backend and Frontend`</strong>`{=html}
```{=html}
</summary>
```
**Goal:** Turn the agent workflow into an application that can be used
through an interface.

**Backend direction** - FastAPI endpoints for starting a session,
sending a message, and retrieving permitted session state. - Pydantic
request/response schemas. - Configuration through environment
variables. - Input validation, error handling, logging, and tests. -
Authentication and persistence only when required by the use case and
designed securely.

**Frontend direction** - A chat interface for the user and character
agent. - Clear loading, error, and session states. - Appropriate display
of monitoring feedback and safety information. - Accessible controls and
privacy notices.

**V4 exit criteria** - \[ \] Document API endpoints and request/response
contracts. - \[ \] Test backend endpoints independently of the
frontend. - \[ \] Connect the UI to the API. - \[ \] Verify that secrets
and sensitive data are not exposed in the browser or logs. - \[ \] Add
setup instructions for local development.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}V5 --- Results Showcase`</strong>`{=html}
```{=html}
</summary>
```
**Goal:** Present project outcomes and evidence rather than only
demonstrating that the application runs.

Potential showcase material: - Example conversations showing the
evolution from V1 to later versions. - Architecture and workflow
diagrams. - Test coverage and reproducible evaluation scenarios. -
EmoGuard and EmoEval evaluation summaries. - Latency and resource
measurements for selected local models. - Screenshots or a short demo
video of the application. - A limitations section explaining what has
and has not been validated.

**V5 exit criteria** - \[ \] Reproduce the documented setup from a clean
environment. - \[ \] Publish representative test results and explain the
methodology. - \[ \] Include limitations, failure cases, and future
work. - \[ \] Avoid unsupported claims about mental-health outcomes or
clinical efficacy.

```{=html}
</details>
```

------------------------------------------------------------------------

## 🏗️ Architecture

### V1 conversation flow

``` mermaid
flowchart TD
    S([START]) --> A[Agent A node]
    A --> R1{Response limit reached?}
    R1 -- No --> B[Agent B node]
    R1 -- Yes --> E([END])
    B --> R2{Response limit reached?}
    R2 -- No --> A
    R2 -- Yes --> E
    A -. uses .-> L[ChatOllama / Ollama]
    B -. uses .-> L
    A -. updates .-> ST[(Shared ChatState)]
    B -. updates .-> ST
```

### Layer responsibilities

  -----------------------------------------------------------------------
  Layer                               Responsibility
  ----------------------------------- -----------------------------------
  `llm/`                              Creates and configures the model
                                      client.

  `agent/state.py`                    Defines shared graph state and
                                      message update behavior.

  `agent/prompts.py`                  Stores agent roles and conversation
                                      instructions.

  `agent/nodes.py`                    Builds the model input, invokes the
                                      LLM, validates output, and returns
                                      state updates.

  `agent/graph.py`                    Registers nodes, wires transitions,
                                      and compiles the workflow.

  `agent/edges.py`                    Optional place for routing
                                      functions if routing grows more
                                      complex. It may remain empty in V1
                                      because routing currently lives in
                                      `graph.py`.

  `api/` *(V4)*                       Exposes agent functionality through
                                      HTTP endpoints.

  `frontend/` *(V4)*                  Provides the user interface.

  `tests/`                            Checks behavior and guards against
                                      regressions.
  -----------------------------------------------------------------------

### Key design principle

> **LangGraph decides who runs next; the LLM generates what that
> participant says.**

The two V1 agents use different prompts but can use the same underlying
model. They are separate roles in the workflow, not separately trained
models.

## 🧠 Core concepts

```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}What is an LLM?`</strong>`{=html}
```{=html}
</summary>
```
A large language model generates text from a supplied context. In this
project, Ollama serves the selected local model and `ChatOllama`
connects it to LangChain.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}What is an agent in V1?`</strong>`{=html}
```{=html}
</summary>
```
An agent is a workflow node that combines a role prompt, conversation
context, an LLM call, and a state update. V1's agents do not yet need
tools or independent long-term memory.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}What is the shared state?`</strong>`{=html}
```{=html}
</summary>
```
`ChatState` holds the message history, topic, current response count,
and maximum response count. Nodes read this state and return partial
updates.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}Why use `add_messages`?`</strong>`{=html}
```{=html}
</summary>
```
The `add_messages` reducer tells LangGraph how to merge message updates
into the existing history, rather than replacing the full message list
on every node execution.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}Why is `edges.py` empty?`</strong>`{=html}
```{=html}
</summary>
```
V1's routing function currently lives in `agent/graph.py`. A separate
`edges.py` is useful once routing becomes complex enough to deserve its
own module; it is not required just because the project has a graph.

```{=html}
</details>
```

------------------------------------------------------------------------

## 📁 Project structure

The structure can evolve with the roadmap. The following is a suggested
target layout; not every directory is implemented in V1.

``` text
EmoAgent-Lite/
├── agent/
│   ├── __init__.py
│   ├── state.py             # Shared LangGraph state
│   ├── prompts.py           # Agent roles and instructions
│   ├── nodes.py              # Agent execution functions
│   ├── edges.py              # Optional routing module
│   └── graph.py              # Graph construction and routing
├── llm/
│   ├── __init__.py
│   └── provider.py           # Ollama / model configuration
├── api/                      # V4: FastAPI backend
├── frontend/                 # V4: chat UI
├── tests/
│   └── test_agent_graph.py
├── run_agent.py              # Local entry point
├── .env.example              # Safe configuration template
├── .gitignore
├── pyproject.toml            # Poetry configuration
├── poetry.lock
└── README.md
```

## ⚙️ Requirements

### Software

-   Python 3.11 or a compatible version supported by your installed
    dependencies.
-   [Ollama](https://ollama.com/) installed and running.
-   [Poetry](https://python-poetry.org/) for dependency and environment
    management.
-   Git (recommended).

### Python packages

The main packages used by the V1 foundation are:

-   `langgraph` --- graph orchestration.
-   `langchain-ollama` --- LangChain integration for Ollama.
-   `langchain-core` --- message types and shared interfaces, installed
    as a dependency of the integration stack.
-   `python-dotenv` --- load local environment configuration.
-   `pytest` --- automated tests.
-   `ruff` --- linting and formatting (optional but recommended).

## 🚀 Quick start

### 1. Clone the repository

``` bash
git clone <YOUR_REPOSITORY_URL>
cd EmoAgent-Lite
```

Replace `<YOUR_REPOSITORY_URL>` with the URL of your repository.

### 2. Install dependencies

If the Poetry project is already configured:

``` bash
poetry install
```

If you are setting up the dependency list for the first time:

``` bash
poetry add langgraph langchain-ollama python-dotenv
poetry add --group dev pytest ruff
```

### 3. Start Ollama and pull a model

Make sure the Ollama service is running, then pull the model you intend
to use. For example:

``` bash
ollama pull llama3.1:8b
```

Verify that the model is available:

``` bash
ollama list
```

Model memory and performance depend on the model size and your hardware.

### 4. Configure environment variables

Create `.env` from `.env.example`, or create `.env` directly:

``` dotenv
OLLAMA_MODEL=llama3.1:8b
OLLAMA_BASE_URL=http://localhost:11434
```

Do not commit `.env` if it contains secrets or private configuration.

### 5. Run V1

The exact command depends on how `run_agent.py` initializes the graph. A
common pattern is:

``` bash
poetry run python run_agent.py
```

If your entry point uses a different filename or requires arguments,
update this command to match the implementation.

------------------------------------------------------------------------

## 🧪 Run and test

Run the test suite:

``` bash
poetry run pytest
```

Run Ruff if it is configured:

``` bash
poetry run ruff check .
poetry run ruff format --check .
```

### Suggested V1 test checklist

-   [ ] Agent A generates a non-empty response.
-   [ ] Agent B generates a non-empty response.
-   [ ] Messages accumulate in `ChatState`.
-   [ ] Speaker names are preserved in the history.
-   [ ] The response counter increases once per agent turn.
-   [ ] The graph ends when `response_count >= max_responses`.
-   [ ] A model error is surfaced clearly.
-   [ ] The graph works for a short topic and a longer topic.

### Troubleshooting

```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}Ollama connection error`</strong>`{=html}
```{=html}
</summary>
```
-   Confirm Ollama is running.
-   Confirm `OLLAMA_BASE_URL` is correct (the default local URL is
    `http://localhost:11434`).
-   Check `ollama list` and ensure the configured model name is
    available.
-   Test the model directly before debugging the LangGraph workflow.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}An agent returns an empty response`</strong>`{=html}
```{=html}
</summary>
```
-   Keep the empty-response validation in `nodes.py`.
-   Inspect `response.response_metadata`, especially `done_reason` and
    `eval_count`.
-   Test the same prompt with `ChatOllama` outside the graph.
-   Print the exact prompt and transcript passed to the failing node.
-   Compare a simple prompt against the full agent prompt before
    changing dependencies.

```{=html}
</details>
```
```{=html}
<details>
```
```{=html}
<summary>
```
`<strong>`{=html}The agents refer to each other in the third
person`</strong>`{=html}
```{=html}
</summary>
```
Make the prompts explicitly request direct, first-person dialogue. Ask
agents to respond to the previous contribution as if speaking to the
other participant, not to describe the conversation. Prompting reduces
this behavior but cannot guarantee it will never occur.

```{=html}
</details>
```

------------------------------------------------------------------------

## 🧩 How the agent module works

### `ChatState` --- `agent/state.py`

The V1 state contains:

``` python
class ChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    topic: str
    response_count: int
    max_responses: int
```

-   `messages`: conversation history.
-   `topic`: current discussion topic.
-   `response_count`: number of agent responses so far.
-   `max_responses`: stop threshold.

### `get_llm()` --- `llm/provider.py`

Creates a configured `ChatOllama` client. It does not generate text
until the client is invoked.

### `_run_agent()` --- `agent/nodes.py`

A shared implementation used by both agent nodes. It creates a
transcript, sends the role prompt and context to the model, validates
the output, and returns a message plus an incremented response count.

### `build_graph()` --- `agent/graph.py`

Creates a `StateGraph`, registers Agent A and Agent B, connects the
nodes, adds conditional routing, and compiles the graph.

### Routing behavior

The graph starts with Agent A. After each response, the router checks
the counter:

-   If the limit has not been reached, control passes to the other
    agent.
-   If the limit has been reached, control passes to `END`.

------------------------------------------------------------------------

## 🔐 Safety and scope

EmoAgent Lite's future PHQ-9-related work involves sensitive
mental-health information. Treat it as a careful research and
software-engineering project, not as a diagnostic tool.

-   PHQ-9 is a screening questionnaire, not by itself a diagnosis.
-   Collect sensitive information only when necessary, with informed
    consent and a clearly explained purpose.
-   Minimize storage and retention; do not put private questionnaire
    responses in public logs, screenshots, or example datasets.
-   Define access controls and deletion behavior before adding
    persistence.
-   Do not present an LLM's output as a substitute for qualified
    professional assessment or care.
-   Design and review appropriate responses for urgent safety concerns
    before exposing the system to users.
-   Evaluate for failure modes and bias; do not infer clinical
    effectiveness from a handful of sample conversations.

The project should clearly distinguish **technical functionality**,
**conversation-quality evaluation**, and **clinical validation**. They
are not interchangeable.

## 🛣️ Current status and next steps

**Current foundation:** V1's two-agent LangGraph conversation flow,
prompt-defined personalities, shared message history, response counting,
conditional stopping, and Ollama integration.

Recommended next steps:

1.  [ ] Finish V1 tests and capture reproducible sample conversations.
2.  [ ] Document the state schema and graph routing.
3.  [ ] Design V2 agent responsibilities and the PHQ-9 data lifecycle
    before implementation.
4.  [ ] Build and test monitoring/evaluation behavior before connecting
    a UI.
5.  [ ] Add FastAPI and frontend integration in V4.
6.  [ ] Publish measured results and limitations in V5.

------------------------------------------------------------------------

## 🤝 Contributing

For changes or experiments:

1.  Create a branch for the feature.
2.  Keep prompts, model configuration, state, routing, and API concerns
    separated.
3.  Add tests for new behavior.
4.  Document new environment variables in `.env.example`.
5.  Never commit secrets or real user questionnaire data.
6.  Describe known limitations alongside results.

## 📄 License

No license has been specified yet. Add a `LICENSE` file before
presenting the repository as open source.

------------------------------------------------------------------------

```{=html}
<p align="center">
```
`<strong>`{=html}EmoAgent Lite`</strong>`{=html}`<br>`{=html}
`<em>`{=html}Build incrementally. Evaluate carefully. Keep the human at
the center.`</em>`{=html}
```{=html}
</p>
```
