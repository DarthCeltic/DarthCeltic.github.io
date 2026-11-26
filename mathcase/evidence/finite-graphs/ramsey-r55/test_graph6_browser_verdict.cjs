const {readFileSync}=require("node:fs");
const {createHash,webcrypto}=require("node:crypto");
const vm=require("node:vm");
const {performance}=require("node:perf_hooks");
const assert=require("node:assert/strict");
const code=readFileSync(require("node:path").join(__dirname,"../../../ramsey-certificate.js"),"utf8");
const canonical=readFileSync(require("node:path").join(__dirname,"exoo42.g6"));
const legacy=readFileSync(require("node:path").join(__dirname,"exoo42-derived.graph6"));
const sha=b=>createHash("sha256").update(b).digest("hex");
async function check(data,expected,script) {
    let click;
    const button={addEventListener:(name,handler)=>click=handler};
    const status={dataset:{}};
    const result={replaceChildren(){}};
    const doc={getElementById:id=>({"ramsey-verify":button,"ramsey-status":status,"ramsey-result":result})[id],
        createElement(){return{append(){}}}};
    const buffer=data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength);
    vm.runInNewContext(script,{document:doc,fetch:async()=>({ok:true,arrayBuffer:async()=>buffer}),crypto:webcrypto,performance});
    await click();
    console.log(status.dataset.state,status.textContent);
    assert.equal(status.dataset.state,expected);
    return status.textContent;
}
(async()=>{
    await check(canonical,"success",code);
    assert.match(await check(legacy,"error",code),/SHA-256 mismatch/);
    // Test the mathematical verdict with a known bad certificate after its test-only hash is pinned.
    assert.match(await check(legacy,"error",code.replace(sha(canonical),sha(legacy))),/Monochromatic five-sets/);
})().catch(e=>{console.error(e);process.exit(1)});
