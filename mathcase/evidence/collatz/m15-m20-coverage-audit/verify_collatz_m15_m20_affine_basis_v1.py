#!/usr/bin/env python3
"""Independently verify the saved M15–M20 affine basis and coverage audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


BASE = "research/collatz"
PACKAGE = "research/collatz/m15-m20-affine-basis-v1/run-5"
PROTOCOL = "research/collatz/m15-m20-affine-basis-v1/protocol.md"
M13_LEAN = "research/collatz/m15/lean/BoundedDescentPlusM13.lean"
M13_SUMMARY = "research/collatz/m15/m13/m13-prefix-summary-r2.json"
M20_README = "research/collatz/m20/README.md"
LEVELS = (
    {"name":"m15","m":15,"q":9,"steps":24,"new":173,"shards":23,"scan":"research/collatz/m15/scan/m15-prefix-scan.json","package":"research/collatz/m15/package-manifest.json","source_manifest":None,"covered":31473,"coverage_key":"combined_covered_mod_32768"},
    {"name":"m16","m":16,"q":10,"steps":26,"new":476,"shards":24,"scan":"research/collatz/m16/scan/m16-residual-affine-screen.json","package":"research/collatz/m16/package-manifest.json","source_manifest":"research/collatz/m16/lean/source-manifest.json","covered":63422,"coverage_key":"combined_covered_mod65536"},
    {"name":"m18","m":18,"q":11,"steps":29,"new":961,"shards":49,"scan":"research/collatz/m18/scan/m18-residual-affine-screen.json","package":"research/collatz/m18/package-manifest.json","source_manifest":"research/collatz/m18/lean/source-manifest.json","covered":254649,"coverage_key":"combined_covered_mod262144"},
    {"name":"m20","m":20,"q":12,"steps":32,"new":2652,"shards":133,"scan":"research/collatz/m20/scan/m20-residual-affine-screen.json","package":"research/collatz/m20/package-manifest.json","source_manifest":"research/collatz/m20/lean/source-manifest.json","covered":1021248,"coverage_key":"combined_covered_mod1048576"},
)
TRACE_SPECS = (
    {"name":"M29Residue167","source":"research/collatz/affine-trace/M29Residue167.lean","receipt":"research/collatz/affine-trace/evidence/m29-residue167-attempt-3/attempt-receipt.json"},
    {"name":"M31Residue111","source":"research/collatz/affine-trace/M31Residue111.lean","receipt":"research/collatz/affine-trace/lean-check-receipt.json"},
    {"name":"M31Residue223","source":"research/collatz/affine-trace/M31Residue223.lean","receipt":"research/collatz/affine-trace/evidence/m31-residue223-attempt-1/attempt-receipt.json"},
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw=path.read_bytes()
    return raw,json.loads(raw.decode("utf-8",errors="strict"))


def bind(repo: Path, path: Path, inputs: dict[str,str]) -> str:
    resolved=path.resolve(strict=True)
    rel=resolved.relative_to(repo.resolve(strict=True)).as_posix()
    digest=file_sha(resolved)
    inputs[rel]=digest
    return digest


def parse_m13(lean: str) -> set[int]:
    conditions=[]
    for name in ("eligibleResidue","eligibleResidue256","eligibleResidue4096","eligibleResidue8192"):
        marker=f"def {name} (r : Nat) : Bool :="
        start=lean.find(marker)
        if start<0: raise ValueError(f"missing M13 predicate {name}")
        end=lean.find("\n\n",start)
        body=lean[start:end if end>=0 else len(lean)]
        conditions.extend((int(m),int(v)) for m,v in re.findall(r"r % (\d+) = (\d+)",body))
        if name=="eligibleResidue8192":
            match=re.search(r"\[([0-9, ]+)\]\.contains",body)
            if not match: raise ValueError("M13 terminal residue list missing")
            conditions.extend((8192,int(v.strip())) for v in match.group(1).split(","))
    return {r for r in range(8192) if any(r%m==v for m,v in conditions)}


def module_records(repo: Path, level: dict[str,Any], package: dict[str,Any], source_manifest: dict[str,Any] | None, input_map: dict[str,str]) -> dict[int,dict[str,Any]]:
    name=level["name"]
    files={x["path"]:x["sha256"] for x in package.get("files",[])}
    modules=package.get("modules",[]) if name=="m15" else (source_manifest or {}).get("modules",[])
    result={}
    for module in modules:
        module_name=module["module"]
        source_rel=module["source"]
        source_repo_rel=f"research/collatz/{name}/{source_rel}"
        source=repo/source_repo_rel
        source_hash=bind(repo,source,input_map)
        if source_hash!=module.get("source_sha256") or files.get(source_rel)!=source_hash:
            raise ValueError(f"{name} source binding mismatch for {module_name}")
        if name=="m15":
            receipt_rel=module["receipt"]
        else:
            names={f"{module_name}.json",f"{module_name}.receipt.json"}
            candidates=[rel for rel in files if Path(rel).name in names]
            if len(candidates)!=1: raise ValueError(f"{name} receipt mapping ambiguous for {module_name}")
            receipt_rel=candidates[0]
        receipt_repo_rel=f"research/collatz/{name}/{receipt_rel}"
        receipt_path=repo/receipt_repo_rel
        receipt_hash=bind(repo,receipt_path,input_map)
        if files.get(receipt_rel)!=receipt_hash:
            raise ValueError(f"{name} package manifest does not bind receipt {module_name}")
        _,receipt=read_json(receipt_path)
        if receipt.get("exit_code")!=0 or receipt.get("source_sha256") not in (None,source_hash):
            raise ValueError(f"{name} receipt does not qualify source {module_name}")
        theorem_names=module.get("theorem_names",[])
        residue_map={int(r):t for r,t in zip(module.get("residues",[]),theorem_names,strict=True)} if theorem_names else {}
        text=source.read_text(encoding="utf-8",errors="strict")
        for residue0 in module.get("residues",[]):
            residue=int(residue0)
            theorem=residue_map.get(residue,f"descent_mod{1<<level['m']}_{residue}")
            if not re.search(rf"\btheorem\s+{re.escape(theorem)}\b",text):
                raise ValueError(f"{name} theorem source missing: {theorem}")
            if residue in result: raise ValueError(f"duplicate {name} residue {residue}")
            result[residue]={"module":module_name,"theorem":theorem,"source_path":source_repo_rel,"source_sha256":source_hash,"receipt_path":receipt_repo_rel,"receipt_sha256":receipt_hash,"receipt_exit_code":0}
    return result


def expected_family(level: dict[str,Any], scan_row: dict[str,Any], src: dict[str,Any], scan_hash: str) -> dict[str,Any]:
    m,q=level["m"],level["q"]
    mod,r=1<<m,int(scan_row["r"])
    a,b=int(scan_row["endpoint_a"]),int(scan_row["endpoint_b"])
    ga,gb=mod-a,r-b
    if (scan_row.get("m"),scan_row.get("modulus"),scan_row.get("steps"))!=(m,mod,level["steps"]): raise ValueError("family row metadata mismatch")
    if a!=3**q or level["steps"]!=m+q: raise ValueError("family is not in exact common affine form")
    if (scan_row.get("strict_gap_coeff"),scan_row.get("strict_gap_const"))!=(ga,gb) or min(ga,gb)<=0: raise ValueError("family descent gap mismatch")
    word=scan_row.get("parity_word")
    if word is not None and (len(word)!=level["steps"] or word.count("O")!=q or word.count("E")!=m): raise ValueError("parity word count mismatch")
    return {"family_id":f"{level['name']}-r{r}","level":level["name"],"modulus_exponent":m,"modulus":mod,"residue":r,"odd_steps":q,"standard_steps":level["steps"],"endpoint_coefficient":a,"endpoint_intercept":b,"descent_gap_coefficient":ga,"descent_gap_intercept":gb,"input_formula":f"2^{m}*k + {r}","iterate_formula":f"C^{level['steps']}(2^{m}*k + {r}) = 3^{q}*k + {b}","descent_formula":f"(2^{m} - 3^{q})*k + ({r} - {b}) = {ga}*k + {gb} > 0","parity_word":word,"scan_path":level["scan"],"scan_sha256":scan_hash,**src}


def exact_exp(value:int,base:int)->int:
    exp=0
    while value>1 and value%base==0: value//=base; exp+=1
    if value!=1: raise ValueError("coefficient is not an exact power")
    return exp


def receipt_refs(repo:Path,receipt_path:Path,receipt:dict[str,Any],input_map:dict[str,str])->None:
    records=receipt.get("bindings")
    if not isinstance(records,dict): records={k:v for k,v in receipt.items() if isinstance(v,dict)}
    for item in records.values():
        if not isinstance(item,dict) or "path" not in item or "sha256" not in item: continue
        base=item.get("base","repository")
        if base in ("repository","repo"): path=repo/item["path"]
        elif base=="receipt_directory": path=receipt_path.parent/item["path"]
        else: raise ValueError(f"unsupported receipt reference base {base}")
        if bind(repo,path,input_map)!=item["sha256"]: raise ValueError(f"receipt child hash mismatch: {item['path']}")


def trace_rows(repo:Path,coverage:bytearray,input_map:dict[str,str])->list[dict[str,Any]]:
    rows=[]
    pattern=(r"theorem\s+universalDescent\s*:\s*∀ k : Nat,\s*iterate\s*\((\d+)\s*\* k \+ (\d+)\)\s+(\d+)\s*=\s*(\d+)\s*\* k \+ (\d+)\s*∧\s*(\d+)\s*\* k \+ (\d+)\s*<\s*(\d+)\s*\* k \+ (\d+)")
    for spec in TRACE_SPECS:
        source=repo/spec["source"]
        source_hash=bind(repo,source,input_map)
        match=re.search(pattern,source.read_text(encoding="utf-8",errors="strict"),re.S)
        if not match: raise ValueError(f"cannot parse {spec['name']} theorem")
        mod,r,steps,a,b,left_a,left_b,right_a,right_b=map(int,match.groups())
        m=exact_exp(mod,2);q=exact_exp(a,3);ga=mod-a;gb=r-b
        if steps!=m+q or (left_a,left_b)!=(a,b) or (right_a,right_b)!=(mod,r) or min(ga,gb)<=0:
            raise ValueError(f"{spec['name']} exact affine statement mismatch")
        receipt_path=repo/spec["receipt"]
        receipt_hash=bind(repo,receipt_path,input_map)
        _,receipt=read_json(receipt_path)
        if receipt.get("status")!="PASS_FINITE_FAMILY_ONLY": raise ValueError(f"{spec['name']} receipt status mismatch")
        if spec["name"]=="M31Residue111":
            binding=receipt.get("certificate_source",{})
            if binding.get("path")!=spec["source"] or binding.get("sha256")!=source_hash or receipt.get("execution",{}).get("network")!="none":
                raise ValueError("M31 residue-111 receipt binding mismatch")
        else:
            binding=receipt.get("bindings",{}).get("certificate_source",{})
            family=receipt.get("family",{})
            expected={"modulus":mod,"residue":r,"steps":steps,"endpoint_slope":a,"endpoint_intercept":b,"strict_gap_slope":ga,"strict_gap_intercept":gb}
            if any(family.get(k)!=v for k,v in expected.items()) or binding.get("path")!=spec["source"] or binding.get("sha256")!=source_hash:
                raise ValueError(f"{spec['name']} receipt/source mismatch")
            execution=receipt.get("execution",{})
            if execution.get("exit_code")!=0 or execution.get("network")!="none" or execution.get("timed_out") is True:
                raise ValueError(f"{spec['name']} execution receipt is nonqualifying")
        receipt_refs(repo,receipt_path,receipt,input_map)
        proj=r%(1<<20)
        if coverage[proj]: raise ValueError(f"{spec['name']} projects into covered M20 class")
        lifts=[r+i*mod for i in range(1<<(31-m))]
        if any(x%(1<<20)!=proj for x in lifts): raise ValueError("sparse lift does not preserve M20 projection")
        rows.append({"family_id":spec["name"],"modulus_exponent":m,"modulus":mod,"residue":r,"odd_steps":q,"standard_steps":steps,"endpoint_coefficient":a,"endpoint_intercept":b,"descent_gap_coefficient":ga,"descent_gap_intercept":gb,"m20_projection_residue":proj,"m20_projection_covered_by_saved_union":False,"classes_at_modulus_2^31":len(lifts),"source_path":spec["source"],"source_sha256":source_hash,"receipt_path":spec["receipt"],"receipt_sha256":receipt_hash,"receipt_status":receipt["status"],"source_use_note":receipt.get("source_use",""),"modulus_2^31_residue_classes":lifts,"all_lifts_outside_m20_union":True})
    classes=[x for row in rows for x in row["modulus_2^31_residue_classes"]]
    if len(classes)!=len(set(classes)): raise ValueError("sparse family lifts overlap")
    return rows


def verify(repo:Path)->dict[str,Any]:
    run=repo/PACKAGE
    summary_raw,summary=read_json(run/"summary.json")
    manifest_raw,manifest=read_json(run/"run-manifest.json")
    if manifest.get("status")!="PASS_HASH_BOUND_AFFINE_BASIS_AUDIT" or summary.get("status")!=manifest.get("status"):
        raise ValueError("derived run status mismatch")
    if manifest.get("input_sha256")!=summary.get("input_sha256"): raise ValueError("manifest and summary input maps differ")
    if file_sha(repo/PROTOCOL)!=manifest.get("protocol_sha256"): raise ValueError("protocol hash mismatch")
    for key in ("derivation_script_path","verification_script_path"):
        if file_sha(repo/manifest[key])!=manifest.get(key.replace("_path","_sha256")): raise ValueError(f"{key} hash mismatch")
    for rel,digest in manifest["input_sha256"].items():
        path=repo/Path(rel)
        if not path.is_file() or file_sha(path)!=digest: raise ValueError(f"input hash mismatch: {rel}")
    expected_inputs={}
    bind(repo,repo/M13_LEAN,expected_inputs)
    bind(repo,repo/M13_SUMMARY,expected_inputs)
    bind(repo,repo/M20_README,expected_inputs)
    outputs=manifest.get("outputs",{})
    for filename,digest in outputs.items():
        if file_sha(run/filename)!=digest: raise ValueError(f"output hash mismatch: {filename}")
    if outputs.get("summary.json")!=sha(summary_raw): raise ValueError("summary output digest mismatch")
    if summary.get("outputs_sha256")!={"family_basis_jsonl":outputs.get("family-basis.jsonl"),"sparse_trace_comparison_json":outputs.get("sparse-trace-comparison.json")}:
        raise ValueError("summary output bindings mismatch")

    m13_lean=(repo/M13_LEAN).read_text(encoding="utf-8",errors="strict")
    seed=parse_m13(m13_lean)
    _,m13_summary=read_json(repo/M13_SUMMARY)
    if len(seed)!=7825 or m13_summary.get("covered")!=7825 or m13_summary.get("source_sha256")!=file_sha(repo/M13_LEAN):
        raise ValueError("M13 seed residue set mismatch")
    if "97.395%" not in (repo/M20_README).read_text(encoding="utf-8",errors="strict"):
        raise ValueError("M20 README rounding text has changed")

    basis_lines=(run/"family-basis.jsonl").read_text(encoding="utf-8",errors="strict").splitlines()
    basis=[json.loads(line) for line in basis_lines]
    expected_basis=[]
    coverage=bytearray(1<<13)
    for r in seed: coverage[r]=1
    old_mod=1<<13
    level_summary=[]
    total_modules=0
    scan_hashes={}
    for i,level in enumerate(LEVELS):
        package_path=repo/level["package"]
        package_raw,package=read_json(package_path)
        bind(repo,package_path,expected_inputs)
        scan_path=repo/level["scan"]
        _,scan=read_json(scan_path)
        scan_hash=bind(repo,scan_path,expected_inputs)
        scan_hashes[level["name"]]=scan_hash
        package_files={row["path"]:row["sha256"] for row in package.get("files",[])}
        scan_rel_package=Path(level["scan"]).relative_to(Path(level["package"]).parent).as_posix()
        if package_files.get(scan_rel_package)!=scan_hash:
            raise ValueError(f"{level['name']} package manifest does not bind its scan")
        source_manifest=None
        if level["source_manifest"]:
            source_manifest_path=repo/level["source_manifest"]
            _,source_manifest=read_json(source_manifest_path)
            bind(repo,source_manifest_path,expected_inputs)
            if source_manifest.get("screen_sha256")!=scan_hash:
                raise ValueError(f"{level['name']} source manifest binds a different scan")
        if i==0:
            if scan.get("accepted_m13_summary_sha256")!=file_sha(repo/M13_SUMMARY):
                raise ValueError("M15 scan does not bind M13 summary")
        else:
            baseline=scan.get("baseline_inputs",{})
            previous=LEVELS[i-1]["name"]
            if baseline.get("m13_summary_sha256")!=file_sha(repo/M13_SUMMARY) or baseline.get(f"{previous}_scan_sha256")!=scan_hashes[previous]:
                raise ValueError(f"{level['name']} does not bind its saved predecessor")
        modules=module_records(repo,level,package,source_manifest,expected_inputs)
        module_count=len(package.get("modules",[])) if level["name"]=="m15" else len((source_manifest or {}).get("modules",[]))
        if module_count!=level["shards"]: raise ValueError(f"{level['name']} shard-module count mismatch")
        rows=scan.get("families",[])
        if len(rows)!=level["new"] or set(modules)!={int(row["r"]) for row in rows}:
            raise ValueError(f"{level['name']} scan and shard family sets differ")
        expected_basis.extend(expected_family(level,row,modules[int(row["r"])],scan_hash) for row in sorted(rows,key=lambda x:int(x["r"])))
        mod=1<<level["m"]
        lifted=bytearray(mod)
        factor=mod//old_mod
        for residue,value in enumerate(coverage):
            if value:
                for copy in range(factor): lifted[residue+copy*old_mod]=1
        overlap=0
        for row in rows:
            residue=int(row["r"])
            overlap += int(bool(lifted[residue]))
            lifted[residue]=1
        if overlap: raise ValueError(f"{level['name']} added set overlaps previous coverage")
        count=sum(lifted)
        if count!=level["covered"] or package.get("expected",{}).get(level["coverage_key"])!=count:
            raise ValueError(f"{level['name']} combined count mismatch")
        total_modules+=module_count
        level_summary.append({"level":level["name"],"modulus":mod,"new_families":level["new"],"previous_coverage_lifted":count-level["new"],"new_families_disjoint":True,"combined_coverage":count,"outside_classes":mod-count,"coverage_percent_exact_decimal":format(Decimal(100*count)/Decimal(mod),".12f"),"odd_steps":level["q"],"standard_steps":level["steps"],"endpoint_coefficient":3**level["q"],"descent_gap_coefficient":mod-3**level["q"],"shard_modules":module_count})
        coverage=lifted;old_mod=mod
    if basis!=expected_basis or len(basis)!=4262 or total_modules!=229: raise ValueError("normalized family basis differs from independently rebuilt rows")
    trace_expected=trace_rows(repo,coverage,expected_inputs)
    bind(repo,repo/PROTOCOL,expected_inputs)
    if expected_inputs!=manifest["input_sha256"]:
        raise ValueError("run manifest input set is incomplete or contains unbound extras")
    trace_output=json.loads((run/"sparse-trace-comparison.json").read_text(encoding="utf-8",errors="strict"))
    if trace_output!=trace_expected: raise ValueError("sparse trace comparison differs from independent reconstruction")
    m20_count=sum(coverage)
    new31=sum(len(row["modulus_2^31_residue_classes"]) for row in trace_expected)
    combined=m20_count*(1<<11)+new31
    percent=Decimal(100*m20_count)/Decimal(1<<20)
    if summary.get("levels")!=level_summary or summary.get("m13_seed")!={"modulus":8192,"covered":7825,"affine_family_rows_in_summary":len(m13_summary.get("m13_families",[]))}:
        raise ValueError("summary tier table differs from reconstructed coverage")
    audit=summary.get("m20_percent_rounding_audit",{})
    if audit.get("m20_readme_text")!="97.395%" or audit.get("m20_readme_sha256")!=file_sha(repo/M20_README) or audit.get("exact_percent")!=format(percent,".12f") or audit.get("rounded_to_three_decimal_places")!=percent.quantize(Decimal("0.001"),rounding=ROUND_HALF_UP).__str__()+"%":
        raise ValueError("M20 exact percentage correction does not recompute")
    sparse=summary.get("sparse_trace_comparison",{})
    expected_percent=format(Decimal(100*combined)/Decimal(1<<31),".12f")
    if sparse.get("families")!=3 or sparse.get("new_modulus_2^31_residue_classes")!=new31 or sparse.get("m20_coverage_lifted_to_modulus_2^31")!=m20_count*(1<<11) or sparse.get("combined_coverage_after_three_sparse_families")!=combined or sparse.get("remaining_classes_at_modulus_2^31")!=(1<<31)-combined or sparse.get("coverage_percent")!=expected_percent:
        raise ValueError("sparse family coverage summary mismatch")
    if manifest.get("family_rows")!=4262 or manifest.get("shard_modules")!=229 or summary.get("m15_m20_shard_modules")!=229 or manifest.get("sparse_trace_families")!=3 or manifest.get("external_calls")!=0 or manifest.get("cost_usd")!=0 or summary.get("m4_promoted") is not False:
        raise ValueError("manifest scope or count boundary mismatch")
    return {"schema":"mathcase-collatz-m15-m20-affine-basis-verification-v1","status":"PASS_INDEPENDENT_AFFINE_BASIS_AND_COVERAGE_CHECK","created_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),"summary_sha256":sha(summary_raw),"run_manifest_sha256":sha(manifest_raw),"family_basis_sha256":outputs["family-basis.jsonl"],"sparse_trace_comparison_sha256":outputs["sparse-trace-comparison.json"],"inputs_rehashed":len(manifest["input_sha256"]),"family_rows_checked":len(basis),"shard_modules_checked":total_modules,"m13_seed_classes_checked":len(seed),"m20_coverage_classes":m20_count,"sparse_new_classes_at_2_31":new31,"external_calls":0,"cost_usd":0,"lean_compiled":False,"trajectory_rescan_performed":False,"m4_promoted":False}


def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();repo=args.repo.resolve(strict=True)
    try:
        receipt=verify(repo)
        out=args.output.resolve(strict=False)
        if out.exists():raise FileExistsError("refusing to overwrite verification receipt")
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes((json.dumps(receipt,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        failure_path=args.output.resolve(strict=False).with_name("verification-failure-receipt.json")
        if not failure_path.exists():
            run_manifest=args.output.resolve(strict=False).parent/"run-manifest.json"
            failure={"schema":"mathcase-collatz-m15-m20-affine-basis-verification-failure-v1","status":"FAIL_PRESERVED","created_utc":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),"failure_type":type(exc).__name__,"failure":str(exc),"verifier_script_path":Path(__file__).resolve().relative_to(repo).as_posix(),"verifier_script_sha256":file_sha(Path(__file__).resolve()),"run_manifest_sha256":file_sha(run_manifest) if run_manifest.exists() else None,"external_calls":0,"cost_usd":0}
            failure_path.parent.mkdir(parents=True,exist_ok=True)
            failure_path.write_bytes((json.dumps(failure,ensure_ascii=False,indent=2)+"\n").encode("utf-8"))
        parser.exit(2,f"verification blocked; failure receipt preserved: {exc}\n")
    print(json.dumps(receipt,indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
