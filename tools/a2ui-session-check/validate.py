#!/usr/bin/env python3
"""Offline structural validation of an A2UI v1.0 payload against the
official Basic Catalog allow-list (no API key, no network).

Checks:
 1. envelope: version == 1.0, createSurface before updateComponents,
    catalogId matches the official Basic Catalog v1.0 URL
 2. every component type is in the catalog allow-list
    (extracted from catalog.json $defs.anyComponent)
 3. component ids are unique; children/child references resolve
 4. a component with id 'root' exists
Exit 0 = PASS, 1 = FAIL.
"""
import json
import sys

CATALOG_ID = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"


def allowlist(catalog):
    names = []
    for ref in catalog["$defs"]["anyComponent"]["oneOf"]:
        names.append(ref["$ref"].split("/")[-1])
    return set(names)


def validate(payload, allowed):
    errors = []
    msgs = payload.get("messages")
    if not msgs:
        return ["no messages"]
    seen_surface = None
    components = {}
    for m in msgs:
        if m.get("version") != "1.0":
            errors.append(f"bad version: {m.get('version')}")
        if "createSurface" in m:
            cs = m["createSurface"]
            if cs.get("catalogId") != CATALOG_ID:
                errors.append(f"catalogId mismatch: {cs.get('catalogId')}")
            seen_surface = cs.get("surfaceId")
        if "updateComponents" in m:
            uc = m["updateComponents"]
            if seen_surface is None:
                errors.append("updateComponents before createSurface")
            if uc.get("surfaceId") != seen_surface:
                errors.append("surfaceId mismatch between create/update")
            for c in uc.get("components", []):
                cid, ctype = c.get("id"), c.get("component")
                if cid in components:
                    errors.append(f"duplicate component id: {cid}")
                if ctype not in allowed:
                    errors.append(f"component not in catalog allow-list: {ctype} (id={cid})")
                components[cid] = c
    if "root" not in components:
        errors.append("no component with id 'root'")
    for cid, c in components.items():
        for ref in c.get("children", []) + ([c["child"]] if "child" in c else []):
            if ref not in components:
                errors.append(f"dangling reference {ref} from {cid}")
    return errors


def main():
    catalog = json.load(open("catalog.json"))
    allowed = allowlist(catalog)
    print(f"allow-list ({len(allowed)}): {sorted(allowed)}")
    payload = json.load(open(sys.argv[1]))
    errors = validate(payload, allowed)
    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
