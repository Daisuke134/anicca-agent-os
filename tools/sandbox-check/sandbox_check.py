#!/usr/bin/env python3
"""sandbox-check: deterministic gate for the SANDBOXED BASH TOOL surface
(how the OS-enforced boundary around shell commands an agent runs -
scope, enablement, filesystem/network defaults, credential protection,
modes and the unsandboxed-retry escape hatch, excludedCommands, credential
masking, org enforcement and locks, local-address and IPv6 rules, and the
stated limitations - is decided, not improvised per machine).
Stdlib only, offline, free.
Canonical source (read in full 2026-11-20):
Claude Code Docs "Configure the sandboxed Bash tool"
https://code.claude.com/docs/en/sandboxing (1,153 lines fetched; page
updated 2026-11-19). Key facts:
The sandbox is an OS-enforced boundary around the shell commands Claude
runs (Bash, PowerShell, Monitor and their child processes). It covers
shell commands ONLY: built-in file/web tools (Read, Edit, Write,
WebFetch, WebSearch), command hooks, local MCP servers, plugin monitors,
LSP servers, helper commands and mods run OUTSIDE it with full access.
To put those behind one boundary, run the Claude Code process itself in
a container, VM, or the sandbox runtime (@anthropic-ai/sandbox-runtime,
open source; macOS Seatbelt, Linux/WSL2 bubblewrap).
The sandbox is OFF by default. Enable with /sandbox or
sandbox.enabled=true in settings (~/.claude/settings.json for all
projects; managed settings to enforce org-wide; --settings for one
session). Platforms: macOS, Linux, WSL2. Native Windows runs commands
unsandboxed (use WSL2). Linux/WSL2 need bubblewrap + socat (seccomp
filter optional, via npm @anthropic-ai/sandbox-runtime); the dependency
check runs at startup, so restart after installing. Verify with probes
run BY Claude (a command typed at the ! prompt usually runs outside):
touch ~/sandbox-probe must fail (Operation not permitted / Read-only
file system); curl --noproxy '*' https://example.com must fail (no route
around the proxy). Decline unsandboxed retries of a failed probe.
Defaults while on: WRITES = working directory + per-user temp dir
($TMPDIR is redirected there) + added directories; protected paths stay
write-denied even inside writable dirs. READS = most of the machine,
INCLUDING credential files such as ~/.ssh and ~/.aws/credentials.
NETWORK = no direct route out; traffic goes through a local proxy that
checks each host against allowed domains, which START EMPTY.
ENVIRONMENT = inherited, including secrets. Change with
filesystem.allowWrite / denyWrite / denyRead / allowRead (when read
rules overlap the NARROWER path wins: a deny holds inside a wider allow,
a narrower allow re-opens part of a denied region; wildcard denies hold
the same way), network.allowedDomains / deniedDomains (denied refused in
every permission mode), credentials, CLAUDE_CODE_SUBPROCESS_ENV_SCRUB.
Prefer allowWrite for a tool needing one more directory over
excludedCommands. On Linux/WSL2 an allowWrite entry for a path that does
not exist yet has no effect - create it first. Filesystem arrays merge
across settings scopes. Git worktrees also allow writes to the main
repo's shared .git dir (hooks/ and config inside it stay denied).
Protected paths (write-denied even when covered by allowWrite or an Edit
allow rule): .claude settings/skills/agents/commands/hooks, .mcp.json,
.claude/workflows and scheduled_tasks.json in the working dir and its
parents; shell startup files, .gitconfig, .vscode/.idea, .git hooks and
config in the working dir; bare-repo files (HEAD/objects/refs/config);
most of ~/.claude plus ~/.claude.json and .credentials.json. Turning
protection off requires filesystem.disabled, which turns off the whole
filesystem layer. Newer top-level HEAD/objects/refs created during a
session may be deleted after a sandboxed command.
Network details: the proxy is reached via HTTP_PROXY/HTTPS_PROXY/
ALL_PROXY env vars. Tools that ignore proxy vars (plain ssh, most
database drivers) cannot connect even to allowed hosts; non-TCP traffic
(UDP, QUIC, ICMP/ping) cannot leave. A WebFetch(domain:...) allow rule
also pre-allows the host for sandboxed commands (wildcards: leading *.
or bare * only). strictAllowlist (user/managed/--settings only, repo
settings have no effect) denies non-allowlist hosts instead of
prompting. allowManagedDomainsOnly (managed) honors only managed
domains/rules. After a hostname passes the allowlist, the proxy refuses
it when it resolves ONLY to local addresses (loopback, link-local incl
169.254.169.254 cloud metadata, the machine's own addresses); localhost
and *.localhost may resolve to loopback, an allowed intranet name
resolving to a private range (10.0.0.0/8) connects, and adding the IP
(with port) to allowedDomains lets a name resolve to a refused address.
IPv6 in domain lists must be bracketed ("[::1]", "[::1]:443"); an
unbracketed ambiguous entry is denied under every parse on deny lists
and never widens an allow list; claude doctor warns "Sandbox network
domain entries have unreliable spellings". In auto mode a command can
carry its own per-command host list for classifier review (v2.1.271+);
it widens only default denies, deniedDomains still block, and locked
allowlists refuse per-command lists.
Credentials: there is NO built-in credential deny list - only listed
files/vars are restricted. sandbox.credentials entries take mode deny
(file reads denied like denyRead; env vars unset before each sandboxed
command; deny entries merge from every loaded scope and can only
narrow) or mask. Disabling filesystem isolation (filesystem.disabled)
stops enforcing file deny / credentials file deny, but env-var scrubbing
and masks stay enforced. filesystem.disabled itself is honored only
from user, managed, and --settings sources - never from project
settings - and is ignored entirely when CLAUDE_CODE_SUBPROCESS_ENV_SCRUB
is set. To strip credentials from ALL subprocesses regardless of
sandboxing, set CLAUDE_CODE_SUBPROCESS_ENV_SCRUB.
Modes: sandbox modes differ only in approval. Auto-allow approves a
command automatically when it runs inside the sandbox; commands outside
(excludedCommands match, unsandboxed retry) go through the regular
permission flow. Even in auto-allow: Bash deny rules still block, rm/
rmdir on critical paths still prompt, content-scoped ask rules still
prompt, a bare Bash ask rule is skipped for sandboxed commands (but not
in plan mode), Monitor commands are NOT auto-approved (still
sandboxed), and commands with a leading variable assignment or eval may
still prompt. Regular permissions mode sends every Bash command through
the regular flow. An allow rule that matches a command ALSO approves
its unsandboxed retry with no prompt.
Unsandboxed retry: when a command fails in the sandbox, Claude may retry
with dangerouslyDisableSandbox. Who approves depends on permission mode:
bypassPermissions = no prompt; manual/acceptEdits = prompt; auto =
classifier; dontAsk = denied; plan mode = its own gating. An ask rule
for Bash(dangerouslyDisableSandbox:true) forces a prompt in auto and
bypassPermissions too and takes precedence over a matching allow rule.
Strict sandbox mode = allowUnsandboxedCommands:false - the parameter is
ignored and retries are refused; add failIfUnavailable so Claude Code
refuses to START (or refuses commands with "Sandbox is required") rather
than fall back unsandboxed. Under an admin-required sandbox (the above
set in managed settings or --settings), repository settings that loosen
the sandbox (excludedCommands, allowedDomains, allowWrite, weaker keys,
enabled:false, etc.) are ignored.
excludedCommands: patterns use Bash permission-rule syntax (end with
" *" to match with arguments; no wildcard = exact match). EVERY command
in a chained call must match; matching is on the call TEXT (a script or
make target calling docker internally does not match, nor does a full
path); redirects, cd, and command substitution keep the whole call
sandboxed; a git clone entry does not cover clones naming absolute, ~,
or .. paths (use a relative path). Excluded commands have NO filesystem
restrictions and NO network proxy, and run under the regular permission
flow. Use the narrowest pattern (e.g. "docker compose *", "gh *").
Masking: mode mask shows sandboxed commands a per-session SENTINEL; the
proxy substitutes the real value on outbound requests to allowed hosts.
Masking REQUIRES network.tlsTerminate (proxy terminates TLS; without it
the sentinel reaches the server and auth fails - claude doctor warns
"TLS termination is unavailable"). Each mask entry may list injectHosts;
the proxy injects only on allowlist-admitted connections, so each
injectHost must also be in allowedDomains; with no injectHosts the value
is substituted on requests to EVERY allowed host. injectHosts are
matched against the bare destination address ignoring ports (IPv6:
bare compressed form there, bracketed in allowedDomains; doctor warns
when an entry can never match). Mask entries, tlsTerminate,
allowPlaintextInject, awsPairs and sigv4 are honored ONLY from user,
managed, and --settings scopes - repository entries are ignored. deny
beats mask for the same variable in any scope. Structured values use
extract/decode/maskClaims/onExtractNoMatch. AWS: mask
AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY TOGETHER (proxy detects
SigV4 by the key sentinel and re-signs; masking only the secret fails);
the conventional AWS trio is linked automatically; other names need
credentials.awsPairs; streaming uploads, presigned URLs and SigV4A
cannot be re-signed (proxy fails them; credentials.sigv4 forwards them
to AWS's own rejection). Credential FILES: mask needs v2.1.221+; on
Linux/WSL2 commands read a sentinel copy (extract marks the secret part);
on macOS the file is BLOCKED instead (same as deny, and the block holds
even with filesystem isolation off). A mask entry falls back to deny for
a directory, a glob, a file over 8 MiB, or a non-UTF-8 file. List each
credential file individually.
Org enforcement: deliver sandbox keys via managed settings to require
the sandbox for every developer. Boolean keys set in managed settings
override local values; array keys MERGE, so lock widening keys in
managed settings: enableWeakerNestedSandbox,
enableWeakerNetworkIsolation, network.allowAllUnixSockets,
network.allowLocalBinding, allowAppleEvents, allowNestedUserNamespaces
(set each to false if unwanted). allowManagedReadPathsOnly honors only
managed allowRead entries. While managed settings configure
sandbox.filesystem at all, or list any credentials.files deny entry,
only managed settings can set filesystem.disabled. With
failIfUnavailable, Claude Code exits at startup on native Windows -
deliver by OS or move Windows users to WSL2/containers. Custom proxy:
httpProxyPort/socksProxyPort replace the built-in proxy; which scopes
may set a port depends on locks (managed-only under
allowManagedDomainsOnly). If a custom port and HTTPS_PROXY are both set,
traffic is NOT forwarded onward to the env proxy.
Failure playbook: Ubuntu AppArmor restriction on user namespaces stops
bubblewrap (add an AppArmor profile when Claude Code runs /usr/bin/
bwrap, or sysctl kernel.apparmor_restrict_unprivileged_userns=0 until
reboot; restart Claude Code). bwrap inside an unprivileged container
cannot mount /proc - enableWeakerNestedSandbox bind-mounts the existing
/proc and considerably weakens security; use only when the outer
container is the real boundary. On Linux/WSL2 the sandbox leaves 0-byte
read-only placeholder files at write-deny paths when a session is killed
(SIGKILL / exiting with a background command running); later settings
writes fail there - claude doctor lists them ("Sandbox mask files left
behind"); delete them with no session running. jest: use --no-watchman.
docker is incompatible - exclude narrowly. Chromium/rootless Podman need
user namespaces: --no-sandbox for the browser, excludedCommands for the
test command, or allowNestedUserNamespaces (user settings only) which
turns OFF a security boundary. git over SSH fails on macOS inside the
sandbox (switch remote to HTTPS or exclude git's network commands);
on Linux it works once the host is allowed on port 22 and the key file
is readable (a denyRead/credentials entry for ~/.ssh hides keys).
Localhost servers: macOS needs network.allowLocalBinding (exposes every
localhost port and lets commands listen on non-loopback too); on Linux a
sandboxed command's localhost is private to that command - exclude the
command that needs the host server. Clipboard tools (pbcopy/xclip/
wl-copy) cannot reach the system clipboard from inside; use /copy.
Limitations (doc's own list): sandboxing reduces risk but is NOT a
complete isolation boundary. The built-in proxy does not terminate or
inspect TLS by default, so encrypted contents are not examined (you are
responsible for allowing only trusted domains). allowUnixSockets can
grant host access (e.g. /var/run/docker.sock = host control). Broad
write access to $PATH executables, system config dirs, or shell startup
files enables privilege escalation. enableWeakerNestedSandbox
considerably weakens the Linux sandbox. allowAppleEvents removes
code-execution isolation on macOS. allowMachLookup services act outside
the sandbox. allowNestedUserNamespaces turns off a boundary.
Layers: permission rules are evaluated BEFORE a tool runs and apply to
every tool; the sandbox is OS enforcement DURING the run and holds
regardless of what the model chose. /sandbox is NOT a permission mode.
--dangerously-skip-permissions also skips protected-path checks.
Subagents run in the parent process and inherit its sandbox config;
background sessions are sandboxed when their own settings enable it;
computer use runs on the real desktop, outside the sandbox, gated by
per-app prompts.
Distinct from: bash-tool-check (the Bash tool's own contract; here the
OS boundary around it), code-execution-check (Anthropic-hosted code
execution sandbox; here the LOCAL Claude Code sandbox),
computer-use-check (desktop control; here only that it runs outside),
credential-check / credential-storage gates (where credentials live;
here only shielding them from sandboxed commands).
"""
import json, sys
CHECKS = [
 ("SB-0a","decided"), ("SB-0b","owner_recorded"), ("SB-0c","canonical_record"),
 ("SB-1a","scope_shell_only_outside_listed"), ("SB-1b","enabled_explicitly_platforms_known"), ("SB-1c","os_prerequisites_and_probes_verified"),
 ("SB-2a","filesystem_defaults_and_narrower_wins"), ("SB-2b","network_proxy_allowlist_from_empty"), ("SB-2c","credentials_explicit_no_builtin_list"),
 ("SB-3a","modes_autoallow_limits_kept"), ("SB-3b","unsandboxed_retry_controlled_strict"), ("SB-3c","excluded_commands_minimal_text_matched"),
 ("SB-4a","masking_tls_trusted_scopes"), ("SB-4b","org_enforcement_and_weaker_key_locks"), ("SB-4c","local_address_refusal_and_ipv6_spelling"),
 ("SB-5a","limitations_not_complete_boundary"), ("SB-5b","permissions_separate_layer_subagents_computeruse"), ("SB-5c","doctor_warnings_and_config_tab_reviewed"),
]
def main(path):
    d = json.load(open(path))
    fails = [cid for cid, key in CHECKS if d.get(key) is not True]
    for cid, key in CHECKS:
        print(f"{'PASS' if d.get(key) is True else 'FAIL'} {cid} {key}")
    print(f"TOTAL {len(CHECKS)-len(fails)}/{len(CHECKS)} pass, {len(fails)} fail")
    return 1 if fails else 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
