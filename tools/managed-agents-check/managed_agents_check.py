#!/usr/bin/env python3
"""managed-agents-check: deterministic gate for the Claude Managed Agents
surface (hosted agent harness - how the agent / environment / session /
deployment objects are defined once and referenced, how scheduled
deployments fire and fail, how the sandbox network and vault credentials
are fenced, which tool calls run without a human, and how a run is
stopped and monitored - is decided, not left to habit).
Stdlib only, offline.
Canonical sources (read in full 2026-11-19):
- Anthropic Claude Platform Docs "Claude Managed Agents overview"
  https://platform.claude.com/docs/en/managed-agents/overview
  (116 lines read in full): two ways to build - Messages API for custom
  loops and fine-grained control, Managed Agents as a pre-built,
  configurable harness on managed infrastructure for long-running and
  asynchronous work, with built-in prompt caching and compaction. Four
  concepts: Agent (model, system prompt, tools, MCP servers, skills),
  Environment (Anthropic-managed cloud sandbox or self-hosted sandbox),
  Session (a running agent instance in an environment), Events (user
  turns, tool results, status updates). Flow: create the agent once and
  reference it by ID across sessions, create an environment, start a
  session, send events and stream responses over SSE (the service keeps
  the full event history), steer with additional user events or
  interrupt. Best for long-running execution, cloud or self-hosted
  sandboxes, minimal infrastructure, stateful sessions (persistent
  filesystem and history), and scheduled execution on a cron schedule.
  Built-in tools: bash, file operations, web search and fetch
  (optionally domain-restricted), MCP servers. Beta: an API key plus
  the managed-agents-2026-04-01 beta header on all requests; enabled by
  default for all API accounts; MCP tunnels and dreaming are a more
  limited research preview. Stateful by design: sessions are
  long-running, resume cleanly after pauses, and store conversation
  history, sandbox state and outputs server-side - therefore NOT
  eligible for Zero Data Retention or HIPAA BAA coverage, except
  self-hosted Managed Agents where you store the data yourself.
  Sessions and uploaded files can be deleted through the API at any
  time.
- Anthropic Claude Platform Docs "Scheduled deployments"
  https://platform.claude.com/docs/en/managed-agents/scheduled-deployments
  (125 lines read in full): a deployment starts sessions autonomously
  on a cadence; it requires agent and environment configuration,
  optionally files, GitHub, memory stores and vaults, and at least one
  initial event (user.message or user.define_outcome). Schedule is a
  POSIX cron expression (minute granularity) plus an IANA timezone;
  matching is literal wall-clock, so DST never shifts the local fire
  time. The response carries schedule.upcoming_runs_at to confirm the
  schedule; actual execution applies jitter of up to 15 percent of the
  interval between runs, minimum 5 seconds, maximum 9 minutes. Maximum
  1,000 deployments per organization. An optional budget is copied
  onto each session the deployment starts - it bounds every run
  separately, not cumulatively; the session pauses with budget_reached
  at its cap; changing the deployment budget affects later runs only,
  and a deployment budget can be removed with budget=None and set
  again. Every trigger attempt writes a deployment run record,
  independent of the session lifecycle; a failed run carries an error
  type (environment_archived_error, agent_archived_error,
  session_rate_limited_error). Session-creation rate limits are
  recorded immediately as a failed run without retry - the schedule
  tries again at the next occurrence. An archived environment or
  vault, or an agent referencing an archived subagent, records a
  failed run and pauses the deployment (paused_reason mirrors the
  error type); archiving the agent archives the deployment, deleting
  the agent archives it at the next trigger, and neither records a
  run. Pause suppresses triggers but running sessions continue and
  manual runs stay allowed; unpause resumes at the next occurrence and
  missed triggers are NOT backfilled. Archive is terminal. A
  deployment runs one pinned agent version even when the agent
  changes; moving versions is an explicit update. The run endpoint
  triggers a manual run (trigger_context.type manual) to test before
  committing to the schedule. Lifecycle changes and run outcomes are
  delivered as webhooks.
- Anthropic Claude Platform Docs "Secure your Managed Agents
  deployment" https://platform.claude.com/docs/en/managed-agents/secure-deployment
  (453 lines read in full): settings ordered most important first.
  Choose where the agent runs: cloud unless tools must run on your own
  infrastructure; with a self-hosted sandbox the firewall is yours,
  web tools still run on Anthropic's servers, and environment-variable
  credentials are not yet supported there. Limit the network:
  networking.type limited with only the hosts the agent needs in
  allowed_hosts - an environment create that omits networking might
  get unrestricted, so set it in every request; list only hosts you
  operate or trust, avoid wildcards and shared-hosting domains;
  allow_package_managers false unless the packages setting requires
  it (package-manager hosts include all of github.com, gitlab.com and
  bitbucket.org, where anyone can publish and sandbox code can
  upload); allow_mcp_servers false, with each trusted MCP host listed
  in allowed_hosts instead (a session-creation check rejects an MCP
  server whose host is not listed). Credentials live in vaults: for
  each environment-variable credential set injection_location to
  request headers only (name both fields - omitting the object enables
  both, and request bodies are often built from content the agent
  reads) and the credential's networking to limited with the exact
  hosts the key is for; sandbox code sees a placeholder and the real
  secret is swapped in only on outgoing HTTPS to allowed hosts;
  responses come back unredacted, so fetch third-party tokens yourself
  and store them in the vault. Keys stay out of system prompts, agent
  definitions and messages; never give the agent a Claude API key or
  access token - even from a vault, sandbox code can use it to call
  the API outside the agent's tool settings, approvals and budget.
  Keep workloads of different trust levels in separate workspaces
  (whoever can start sessions in a workspace can reference its
  vaults); authenticate the application with a Workload Identity
  Federation rule enabled in one workspace only, otherwise an API key
  scoped to that workspace; a mounted repository's GitHub token is
  fine-grained with minimum permissions, write only if the agent must
  push. Restrict web tools: allowed_domains on web_fetch (only the
  sites the agent needs - any fetched URL can carry data out) and on
  web_search (only trusted result sources; the list does not stop the
  query itself reaching the provider); blocked_domains blocks only the
  listed hosts and subdomains and must not be relied on for security.
  In a limited environment allowed_hosts also bounds the web tools,
  and the two lists match hosts differently (allowed_hosts example.com
  does not match www.example.com; allowed_domains example.com matches
  subdomains too). web_fetch opens only URLs that already appeared in
  the session (user message text, outcome descriptions, search result
  addresses, earlier fetched pages, direct custom-tool results) -
  never URLs from the system prompt, the agent configuration, Claude's
  own output, bash output, MCP results or attached files. A domain
  list on web_fetch does not limit bash; limit the network as well.
  Approve risky actions with permission_policy per tool: read, glob,
  grep always_allow (they change nothing); bash, write, edit and
  web_fetch auto - always_ask instead when a tool's changes cannot be
  undone outside the sandbox, or when relayed end-user text alone
  should not make it run; web_search always_ask if the agent handles
  data you would not want in a query; MCP tools that only read get
  auto set per tool in configs (the toolset default stays always_ask,
  so tools a server adds later still wait); MCP tools that change data
  keep always_ask; custom tools are governed by your own code, so
  validate each call's input and limit what it can touch. auto lets
  the server allow, deny or pause a call - it is NOT a human
  checkpoint; a paused session waits indefinitely, so an unattended
  session needs a client that answers paused calls or interrupts, and
  a client that approves every call unseen is the same as
  always_allow. A person approves each call to a tool that can move
  money (payments, withdrawals, transfers, payouts): always_ask, or
  for a custom tool no run before a person approves it. Smallest tool
  set: default_config.enabled false on the agent toolset (all eight
  built-ins are on by default), then enable only what the agent needs;
  the same for MCP toolsets, and remove unused servers; an agent
  update replaces the whole tools array and reaches only new sessions
  - deployments pin an agent version, agents that list this agent pin
  theirs, and an existing session is tightened by updating that
  session while idle (in multiagent sessions, web-tool domain lists
  apply across agents from their next turn). Keep untrusted input away
  from powerful tools: untrusted input is webpages, search results,
  tickets, emails, repository files, uploads, MCP results and relayed
  end-user messages; powerful tools are bash, write, edit, web_fetch,
  web_search, writing/sending MCP and custom tools, and any tool using
  a credential; no agent that reads untrusted input holds a powerful
  tool on always_allow. Designs: split reading from acting (a lead
  with no built-in tools, a fetcher with only domain-limited web
  tools, a writer holding the writing tools on auto or always_ask -
  they still share one sandbox, files and vault credentials, so a
  stronger split is two sessions with separate environments and
  vaults, passing only fixed fields), give the agent one narrow custom
  tool (the application runs it, checks input, holds the credential),
  or require always_ask. Reading a file can load CLAUDE.md and
  AGENTS.md from its directory and parents as instructions (with @
  references up to five deep, pointing anywhere in the sandbox; no
  setting turns this off except disabling read), so any repository,
  package or archive outsiders can write is untrusted input; a mounted
  GitHub repository's .claude/skills load as agent instructions with
  no review step; attach memory stores read_only unless the agent must
  write (default read_write, and later sessions read saved text as
  trusted memory). Limits and a way to stop: a session budget caps
  spend at public list prices - at the cap the session and each thread
  pause, though in-progress requests can complete and overshoot; you
  cannot add a budget to a session created without one, and after
  removing a cap you cannot set a new one; a budget does not limit
  what the agent does before the cap. Stop procedure: send
  user.interrupt alone (a running tool call can complete; the session
  goes idle; an interrupt ends no workflow run, so also message the
  agent to stop its runs), pause or archive the deployment so no new
  scheduled run starts, rotate any possibly exposed key at its issuer,
  wait for idle (a running session cannot be archived or deleted),
  then archive to keep history or delete when it is no longer needed;
  an interrupt does not undo what the agent already did or sent, and
  archiving an agent does not stop its running sessions; archiving or
  deleting a vault or credential removes the secret from running
  sessions without a restart (allow a delay, interrupt them too - a
  token already fetched with the secret stays in the sandbox).
  Monitoring: webhooks and alerts when a session goes idle, reaches
  its budget or terminates, with a check of why it went idle; an
  optional offline reviewer reads every session's events on a
  schedule; store the events you want to keep in your own logs and
  delete sessions you no longer need.
Exit 0=PASS, 1=FAIL.
"""
import json, sys
def check(d):
    f=[]
    dec=d.get("decision") or {}
    if not dec.get("decision_recorded"): f.append("MG-0 the Managed Agents surface is not recorded as a decided surface - which workloads run on a hosted harness (agent, environment, session, deployment as managed objects) and which stay on a self-built loop over the Messages API is left to each run and habit, not a decision")
    if not dec.get("owner_recorded"): f.append("MG-0 no owner is recorded for managed-agent correctness (object definitions, deployment failure handling, network and vault fences, permission policies) - a deployment that silently stops firing or a session holding an over-wide key has no accountable reader")
    if not dec.get("surfaces_inventoried"): f.append("MG-0 there is no inventory of agent workloads in use (which loops exist, what each one's agent definition, environment and schedule would be, and which of them is a managed deployment) - the surface cannot be required where its own workloads are uncounted")
    dfn=d.get("definition") or {}
    if not dfn.get("agent_defined_once"): f.append("MG-1 the agent is not defined once and referenced (the Agent object - model, system prompt, tools, MCP servers, skills - is created once, its ID and version are stored, and sessions take a pointer only; putting model, system or tools on the session body rebuilds the definition per run and drifts silently) - every run carries its own copy of what the agent is")
    if not dfn.get("environment_decided"): f.append("MG-1 the environment is not decided (cloud sandbox versus self-hosted sandbox is chosen per workload - cloud unless tools must run on infrastructure you control; a self-hosted sandbox makes the firewall, isolation and hardening yours, web tools still run on Anthropic's servers, and environment-variable credentials are not yet supported there; the beta runs under the managed-agents-2026-04-01 header) - the sandbox is wherever the first run happened to land")
    if not dfn.get("session_shape_known"): f.append("MG-1 the session shape is not fixed (a session references an agent and an environment, work arrives as events - user turns, tool results, status updates - responses stream over SSE, the service keeps the full event history for later fetch, and a running session is steered with additional user events or interrupted, not abandoned and restarted) - long work is babysat as chat instead of run as stateful sessions that resume after pauses")
    sch=d.get("scheduling") or {}
    if not sch.get("deployment_shape_known"): f.append("MG-2 the deployment shape is not fixed (a deployment requires agent and environment configuration plus at least one initial event - a user.message or user.define_outcome; the schedule is a POSIX cron expression at minute granularity with an IANA timezone and literal wall-clock matching across DST; schedule.upcoming_runs_at is checked to confirm the schedule took; actual firing jitters up to 15 percent of the interval, minimum 5 seconds and maximum 9 minutes; the organization cap is 1,000 deployments) - a recurring agent fires at a time nobody verified, or a fleet grows past the cap it never counted")
    if not sch.get("budget_per_run"): f.append("MG-2 no per-run budget is set on deployments (the deployment budget is copied onto each session it starts and bounds every run separately, not cumulatively - a 2000 cap lets every run spend about $20; the session pauses with budget_reached at its cap; changing the deployment budget reaches only runs started afterward, a running session keeps the cap it started with, and a deployment budget can be removed with budget=None and set again) - one stuck recurring run bills like every run before it, forever")
    if not sch.get("lifecycle_and_failures_handled"): f.append("MG-2 deployment lifecycle and failure behavior are not handled (every trigger attempt writes a deployment run record independent of the session lifecycle; a failed run carries an error type - environment_archived_error, agent_archived_error, session_rate_limited_error; a session-creation rate limit is recorded immediately without retry and the schedule tries again at the next occurrence; an archived environment or vault or an archived referenced subagent records a failed run and pauses the deployment with paused_reason mirroring the error; pause suppresses triggers while running sessions continue and manual runs stay allowed, unpause resumes at the next occurrence and missed triggers are not backfilled, archive is terminal; a deployment pins one agent version until explicitly updated; the run endpoint fires a manual run to test before committing) - a schedule that died on an archived dependency looks exactly like a schedule that is merely quiet")
    sec=d.get("security") or {}
    if not sec.get("networking_limited"): f.append("MG-3 the sandbox network is not limited (networking.type is limited with only the hosts the agent needs in allowed_hosts, set explicitly in every environment create because an omitted networking can come back unrestricted; only hosts you operate or trust, no wildcards or shared-hosting domains; allow_package_managers stays false unless the packages setting requires it - package-manager hosts open all of github.com, gitlab.com and bitbucket.org to reads and uploads; allow_mcp_servers stays false with each trusted MCP host listed in allowed_hosts, and session creation rejects an MCP server whose host is not listed) - sandbox code reaches, and can upload to, the whole internet by default")
    if not sec.get("credentials_in_vaults"): f.append("MG-3 credentials are not fenced in vaults (every secret lives in a vault attached via vault_ids; each environment-variable credential injects into request headers only - both injection fields named, because omitting the object enables body injection too and bodies are built from content the agent reads - and its networking is limited to the exact hosts the key is for, so sandbox code sees only a placeholder and the real secret is swapped in on outgoing HTTPS to those hosts; third-party tokens are fetched by the application and stored in the vault, because a token fetched with a stored secret returns unredacted; keys never appear in system prompts, agent definitions or messages; the agent is never given a Claude API key or access token, which sandbox code could use outside the agent's tool settings, approvals and budget; trust levels are separated by workspace and the application authenticates with a federation rule or API key scoped to one workspace) - the secret sits where the model, the logs or the next fetched page can read it")
    if not sec.get("web_tools_restricted"): f.append("MG-3 the web tools are not restricted (allowed_domains is set on web_fetch - only the sites the agent needs, because any fetched URL can carry data to the site it points to - and on web_search - only trusted result sources, knowing the list does not stop the query itself reaching the provider; blocked_domains is never the security control, since it blocks only the listed hosts and subdomains while archives, caches and mirrors stay open; in a limited environment allowed_hosts also bounds the web tools and the two lists match differently - allowed_hosts example.com misses www.example.com while allowed_domains example.com covers subdomains; web_fetch opens only URLs that already appeared in the session, never URLs from the system prompt, the agent configuration, Claude's own output, bash output, MCP results or attached files; and a domain list on web_fetch does not limit bash, so the network is limited as well) - the agent reads the open web and ships data to whatever URL injected text builds")
    per=d.get("permissions") or {}
    if not per.get("permission_policies_set"): f.append("MG-4 permission policies are not set per tool (read, glob and grep are always_allow because they change nothing; bash, write, edit and web_fetch are auto, upgraded to always_ask when a tool's changes cannot be undone outside the sandbox or when relayed end-user text alone should not make it run; web_search is always_ask when the agent handles data that must not ride in a query; read-only MCP tools get auto per tool in configs while the toolset default stays always_ask so a tool the server adds later still waits; data-changing MCP tools keep always_ask; auto is a server check, not a human checkpoint; a paused session waits indefinitely, so unattended sessions have a client that answers paused calls or interrupts, and every paused call is reviewed - a client that approves unseen is always_allow under another name; any tool that can move money is always_ask with a person approving each call, and a custom money tool does not run before a person approves it) - the default toolset runs every call without approval, including the irreversible ones")
    if not per.get("smallest_toolset"): f.append("MG-4 the tool set is not the smallest (default_config.enabled is false on the agent toolset - all eight built-ins are on by default - and only the tools the agent needs are enabled; MCP toolsets get the same default-off treatment with named tools enabled and unused servers removed; custom tools are validated call by call in the application because permission policies do not apply to them; an agent update replaces the whole tools array and reaches only new sessions, deployments and listing agents keep their pinned versions until updated, and an existing session is tightened by updating it while idle - in multiagent sessions new web-tool domain lists apply to every agent from its next turn) - the agent holds, and a later server update can silently extend, tools its task never needed")
    if not per.get("untrusted_input_separation"): f.append("MG-4 untrusted input is not separated from powerful tools (no agent that reads untrusted input - webpages, search results, tickets, emails, repository files, uploads, MCP results, relayed end-user messages - holds a powerful tool - bash, write, edit, web tools, writing or sending MCP or custom tools, any credentialed tool - on always_allow; the design is one of: split reading from acting across agents or, stronger, across two sessions with separate environments and vaults passing only fixed fields; one narrow custom tool the application runs and validates while holding the credential; or always_ask on the powerful tool; reading a file loads CLAUDE.md and AGENTS.md from its directory and parents, with @ references up to five deep pointing anywhere in the sandbox, and a mounted repository's .claude/skills load as instructions with no review - so any repository, package or archive outsiders can write is treated as untrusted input; memory stores attach read_only unless the agent must write, because the read_write default makes later sessions read saved text as trusted memory) - text anyone on the internet can write can drive the agent's most powerful tools")
    lim=d.get("limits") or {}
    if not lim.get("stop_procedure_known"): f.append("MG-5 the stop procedure is not fixed in advance (send user.interrupt alone - a running tool call can complete first and the session goes idle; an interrupt ends no workflow run, so the agent is also messaged to stop its runs; pause the deployment so no new scheduled run starts, or archive it to end the schedule; rotate any possibly exposed key at its issuer; wait for idle, because a running session cannot be archived or deleted; then archive to keep history or delete when it is no longer needed; an interrupt does not undo what the agent already did or sent, archiving an agent does not stop its running sessions, and archiving or deleting a vault or credential strips the secret from running sessions without a restart - with a delay, and a token already fetched with it stays in the sandbox; a session budget cannot be added to a session created without one, and once a cap is removed no new one can be set, and a budget never limits what the agent does before the cap) - when a run must stop, the team improvises against a moving agent")
    if not lim.get("monitoring_alerts"): f.append("MG-5 sessions are not monitored (webhooks or alerts fire when a session goes idle, reaches its budget or terminates, and why it went idle is checked rather than assumed; an offline reviewer reads every session's events on a schedule, so a long run's transcript is read by something other than the run itself; the events worth keeping are stored in your own logs, not only in the service's history) - a fleet of long-running sessions runs unobserved, and an idle or budget-stopped session looks exactly like a finished one")
    if not lim.get("retention_decided"): f.append("MG-5 retention is not decided (Managed Agents is stateful by design - conversation history, sandbox state and outputs are stored server-side - and is therefore not eligible for Zero Data Retention or HIPAA BAA coverage, except self-hosted deployments where you store the data yourself; sessions you no longer need are deleted, and uploaded files are deleted separately, both through the API at any time; which workloads may carry data that must never sit outside ZDR is decided before they are placed on the hosted harness, not after) - transcripts accumulate server-side under terms nobody chose, including workloads whose data was never cleared to be there")
    return f
if __name__=="__main__":
    data=json.load(open(sys.argv[1])); fails=check(data)
    if fails:
        print(f"FAIL ({len(fails)}):")
        [print(" -",x) for x in fails]; sys.exit(1)
    print("PASS"); sys.exit(0)
