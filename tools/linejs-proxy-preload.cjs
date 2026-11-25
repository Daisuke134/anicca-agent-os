// linejs creates its own undici Agent and passes it as an explicit fetch
// dispatcher, which bypasses Node's env-proxy global dispatcher. On this VM
// all egress must go through the hatch egress proxy (direct connections land
// on fake-IP DNS answers and fail), so strip any explicit dispatcher and let
// the NODE_USE_ENV_PROXY=1 global dispatcher handle the request.
const origFetch = globalThis.fetch;
globalThis.fetch = function (info, init) {
  if (init && typeof init === "object" && "dispatcher" in init) {
    const rest = { ...init };
    delete rest.dispatcher;
    return origFetch.call(this, info, rest);
  }
  return origFetch.call(this, info, init);
};
