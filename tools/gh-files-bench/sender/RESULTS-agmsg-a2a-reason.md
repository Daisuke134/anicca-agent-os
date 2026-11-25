# Raw results: agmsg / A2A minimal / Reason (2026-11-22)

## agmsg (v1.8.1, shared SQLite, no daemon)
- Setup: team bench1122 + join bench-a/bench-b = 0.99 s total (one-time
  install was done 2026-11-18; the installer needed one recovery step then).
- Sequential handoffs (send -> recipient inbox read): 20/20.
  Latency s (agmsg-lat.txt): min 0.900, median 1.042, max 1.725.
- Concurrent sends x5: 5/5 arrived, no loss, no duplicates.
- Wake: watch.sh stream surfaced a new message 4.33 s after send.
  poke.sh to a hand-joined member failed cleanly:
  "no placement record for 'bench1122/bench-b'" (poke needs a session
  spawned with a recorded pane placement).
- Bench agents left the team afterwards; identity history preserved.

## A2A (minimal hand-written implementation, Python stdlib only)
- No installable product exists; we wrote worker.py (Agent Card +
  JSON-RPC message/send, tasks/get) and client.py. See results.json.
- Sequential: 20/20, latency min 0.065 s / median 0.066 s / max 0.100 s
  (loopback, includes a 50 ms simulated work tick in the worker).
- Concurrent: 5/5.
- Wake test: send while the worker was down FAILED (URLError).
  After an external supervisor restarted the worker, the endpoint was
  ready in 0.104 s and the handoff succeeded. The protocol itself has
  no wake primitive; the endpoint must be kept alive externally.

## Reason (Reason Machines network, CLI on this VM)
- `reason network who` answered in ~0.2 s: 2 machines online
  (this VM + the Mac mini relay), 18 known sessions, 17 offline.
- `reason status` produced no output for >60 s and was killed.
- 3 sends to daisuke/terminal: all accepted in 0.51-0.87 s, all landed
  in state "queued" - the address resolved to a session on the Mac mini
  "last seen 28d ago". Confirmed deliveries: 0/3.
- Our production wake path for Reason is a 60 s polling hook
  (reason-inbox-wake), i.e. the knock is ours, not the network's.
- Full 20-round workload not run: with the only reachable named
  session 28 days stale and every send queueing silently, further
  rounds would measure the same queue.
