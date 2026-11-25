#!/usr/bin/env python3
"""wif-check: deterministic gate for the WORKLOAD IDENTITY FEDERATION surface.
Stdlib only, offline, free. Canonical sources (read in full 2026-11-20):
Anthropic Claude Platform Docs "Workload Identity Federation"
https://platform.claude.com/docs/en/manage-claude/workload-identity-federation
and "WIF reference" https://platform.claude.com/docs/en/manage-claude/wif-reference
Key facts: WIF replaces long-lived sk-ant-... keys with short-lived OIDC JWTs
from an IdP you operate (AWS IAM, Google Cloud, GitHub Actions, Kubernetes,
SPIFFE, Entra ID, Okta). Three Console resources express the trust: a service
account (svac_..., named non-human principal, org-level, workspace member,
implicitly in the default workspace), a federation issuer (fdis_..., exact
iss string + JWKS source discovery/explicit_url/inline), and a federation
rule (fdrl_..., binds issuer to service account; match + scope + lifetime).
A rule must set at least one of subject_prefix, claims, or condition (CEL);
audience alone is rejected. All configured matchers must pass; Anthropic
evaluates the rule the client names - there is no implicit rule search.
Exchange: SDK posts the JWT to POST /v1/oauth/token with the RFC 7523
jwt-bearer grant; response is RFC 6749 5.1 (access_token <redacted>).
Env activation needs ANTHROPIC_FEDERATION_RULE_ID + ANTHROPIC_ORGANIZATION_ID
+ one of ANTHROPIC_IDENTITY_TOKEN_FILE / ANTHROPIC_IDENTITY_TOKEN (file is
reread on every exchange). Credential precedence: constructor > ANTHROPIC_API_KEY
/ ANTHROPIC_AUTH_TOKEN > explicit ANTHROPIC_PROFILE > federation env vars >
active profile; an exported-but-empty variable can win its slot, so unset,
never blank. Scopes: workspace:developer (all non-admin endpoints, = workspace
API key), workspace:inference (inference only), workspace:manage_tunnels,
org:admin (Admin API; rule must target an admin-role service account; effective
permissions are the intersection of rule scope and account role; out-of-scope
calls return 403; no finer-grained scopes exist). Minted lifetime is the
lesser of the rule token_lifetime_seconds (60-86400, default 3600; wizard
prefills 600) and twice the IdP JWT's remaining lifetime, floored at 60s.
Refresh is two-tier: advisory at expiry-120s (cached token keeps serving),
mandatory at expiry-30s (failure is an error). JWT verification: at most
16 KiB, asymmetric algs only (HMAC and none rejected), kid required and must
match JWKS, sub present, iat present and not future, exp present and future,
30s clock leeway, JWT lifetime capped by issuer max (default 1h). Assertions
carrying jti are single-use per issuer (check_jti on by default); reuse fails
as jti_reused - mint a fresh JWT per exchange; disabling check_jti removes
replay protection for every rule on the issuer and is a last resort only.
Issuer/JWKS URLs Anthropic fetches must be https, port 443, public DNS
resolving to public IPs, no IP literals (explicit_url/inline compare
issuer_url as a string only). JWKS rotation: publish the new key at least
15 minutes before first signing use and keep the old key until its tokens
expire; fetched JWKS is cached up to about 1 minute. workspace_id is required
when the rule spans all/multiple workspaces; use the wrkspc_... ID, the
literal default is deprecated; switching workspaces needs a new exchange.
Every assertion denial is the same opaque 401 authentication_error
"Authentication failed"; the deny reason lives in the Console authentication
history (400 invalid_request_error cases leave no history entry and name the
problem directly). WIF is not a complete security solution: the chain is only
as strong as the upstream IdP, so pair it with IdP controls (workload binding,
conditional access, audit logging). Migration: configure in parallel, check
ant auth status, unset ANTHROPIC_API_KEY everywhere, then delete the key.
Profile files: configs/<profile>.json is non-secret and committable;
credentials/<profile>.json is secret and written mode 0600.
Exit 0 = all pass, 1 = any fail. null/unverified = fail."""
import json, sys
def check(d):
    r = {}
    r["WF-0a_surface_decided"] = d.get("decided") is True
    r["WF-0b_owner_and_source"] = bool(d.get("owner")) and bool(d.get("source"))
    r["WF-0c_workload_credential_surfaces_inventoried"] = d.get("workload_credential_surfaces_inventoried") is True
    r["WF-1a_service_account_per_workload"] = d.get("service_account_per_workload_named_principal") is True
    r["WF-1b_issuer_exact_iss_and_jwks_mode"] = d.get("issuer_registered_exact_iss_and_jwks_mode_chosen") is True
    r["WF-1c_rule_has_real_matcher_not_audience_only"] = d.get("rule_binds_issuer_to_account_with_at_least_one_matcher") is True
    r["WF-2a_exchange_rfc7523_post_oauth_token"] = d.get("exchange_via_rfc7523_jwt_bearer_post_oauth_token") is True
    r["WF-2b_env_vars_complete_file_reread"] = d.get("env_vars_complete_rule_org_and_token_file_or_token") is True
    r["WF-2c_precedence_api_key_unset_not_blanked"] = d.get("credential_precedence_checked_api_key_unset_so_federation_wins") is True
    r["WF-3a_scope_least_privilege_intersection"] = d.get("oauth_scope_least_privilege_and_role_intersection") is True
    r["WF-3b_lifetime_min_rule_and_2x_jwt_floor60"] = d.get("token_lifetime_min_of_rule_and_2x_jwt_remainder_floor60") is True
    r["WF-3c_workspace_scoping_explicit_wrkspc_id"] = d.get("workspace_scoping_explicit_when_rule_multi_workspace") is True
    r["WF-4a_jwt_verification_constraints"] = d.get("jwt_constraints_16kib_asymmetric_kid_claims_skew_maxlife") is True
    r["WF-4b_jti_single_use_fresh_each_exchange"] = d.get("jti_single_use_fresh_jwt_each_exchange_check_jti_kept") is True
    r["WF-4c_jwks_url_rules_and_rotation_lead"] = d.get("jwks_url_https443_public_and_rotation_publish_15min_ahead") is True
    r["WF-5a_upstream_idp_controls_paired"] = d.get("upstream_idp_strength_paired_not_complete_alone") is True
    r["WF-5b_opaque_401_via_auth_history"] = d.get("opaque_401_debugged_via_auth_history_not_response") is True
    r["WF-5c_secret_separation_and_key_deletion"] = d.get("config_nonsecret_credentials_secret_0600_and_old_key_deleted_after_migration") is True
    r["pass_count"] = sum(1 for v in r.values() if v is True)
    r["fail_count"] = sum(1 for v in r.values() if v is False)
    r["pass"] = r["fail_count"] == 0
    return r
if __name__ == "__main__":
    v = check(json.load(open(sys.argv[1])))
    print(json.dumps(v, indent=2)); sys.exit(0 if v["pass"] else 1)
