'use strict';
(function(root) {
  const canonical = v => v === null || typeof v !== 'object' ? JSON.stringify(v) : Array.isArray(v) ? '['+v.map(canonical).join(',')+']' : '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
  // HTTP on a private LAN lacks Web Crypto's secure-context API.
  // SHA-256 keeps the same integrity checks without weakening validation.
  function shaPortable(raw) {
    const bytes=typeof raw==='string'?new TextEncoder().encode(raw):new Uint8Array(raw.buffer||raw,raw.byteOffset||0,raw.byteLength);
    const k=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
    const h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    const padded=new Uint8Array(Math.ceil((bytes.length+9)/64)*64);padded.set(bytes);padded[bytes.length]=128;
    const view=new DataView(padded.buffer);view.setUint32(padded.length-8,Math.floor(bytes.length/0x20000000));view.setUint32(padded.length-4,(bytes.length*8)>>>0);
    const rr=(x,n)=>(x>>>n)|(x<<(32-n)),w=new Uint32Array(64);
    for(let offset=0;offset<padded.length;offset+=64){
      for(let i=0;i<16;i++)w[i]=view.getUint32(offset+i*4);
      for(let i=16;i<64;i++){const x=w[i-15],y=w[i-2];w[i]=(w[i-16]+(rr(x,7)^rr(x,18)^(x>>>3))+w[i-7]+(rr(y,17)^rr(y,19)^(y>>>10)))>>>0;}
      let [a,b,c,d,e,f,g,z]=h;
      for(let i=0;i<64;i++){const t1=(z+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[i]+w[i])>>>0,t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))>>>0;z=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;}
      [a,b,c,d,e,f,g,z].forEach((v,i)=>h[i]=(h[i]+v)>>>0);
    }
    return h.map(x=>x.toString(16).padStart(8,'0')).join('');
  }
  async function sha(raw) {
    const bytes = typeof raw === 'string' ? new TextEncoder().encode(raw) : raw;
    if(typeof module !== 'undefined' && module.exports) return require('node:crypto').createHash('sha256').update(bytes).digest('hex');
    if(!root.crypto?.subtle)return shaPortable(bytes);
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)), b=>b.toString(16).padStart(2,'0')).join('');
  }
  const digest = v => sha(canonical(v));
  const requireValue = (ok, message) => {if(!ok) throw new Error(message);};
  function ledger(w) {
    const objects=Object.values(w.objects), atoms=[...w.ready,...Object.keys(w.nutrients),...Object.keys(w.waste),...objects.flatMap(o=>o.atoms)];
    const tokens=[...w.bank,...objects.flatMap(o=>o.tokens)];
    requireValue(atoms.length===96 && new Set(atoms).size===96 && atoms.every(a=>w.atoms[a]), 'Material ownership invalid');
    requireValue(tokens.length===new Set(tokens.map(t=>t.unit)).size, 'Work ownership invalid');
    requireValue(Number.isInteger(w.heat)&&w.heat>=0,'Heat invalid');
    objects.forEach(o=>requireValue(o.bits===o.atoms.map(a=>w.atoms[a].bit).join(''),'Composition invalid'));
    const bonds=objects.reduce((n,o)=>n+o.atoms.length-1,0);
    return {atoms:atoms.length, usable:tokens.length, heat:w.heat, bonds, nutrients:Object.keys(w.nutrients).length,
      ready:w.ready.length, waste:Object.keys(w.waste).length, bound:objects.reduce((n,o)=>n+o.atoms.length,0),
      total:tokens.length+w.heat+bonds+8*Object.keys(w.nutrients).length};
  }
  async function validate(raw, integrity) {
    requireValue(raw.byteLength===integrity.bytes && await sha(raw)===integrity.sha256,'Recording integrity mismatch');
    const d=JSON.parse(new TextDecoder().decode(raw));
    requireValue(d.schema==='ora-observer-v1' && d.mode==='recorded' && d.spatial===false && d.experiment_id==='HEARTBEAT-04','Unsupported observer contract');
    const m=d.manifest, id=m.identity;
    requireValue(canonical(m.config)===canonical({seed:1,work:2,max_ticks:32}) && id.world_id==='template-reference' && id.source_revision==='3bc1ca652c2dd31ec46a13061604ff56d2ecc6fb','Unsupported reference adapter');
    requireValue(m.schema==='heartbeat04-v1' && id.config_sha256===await digest(m.config),'Configuration identity mismatch');
    const {run_id,...identity}=id;
    requireValue(run_id===await digest(identity),'Run identity mismatch');
    requireValue(d.frames.length>1 && d.frames.length<=230,'Frame bounds');
    let chain='0'.repeat(64),tick=-1, eventChain=null, prior=null, lastTime=null, total=null;
    for(let i=0;i<d.frames.length;i++) {
      const f=d.frames[i],{frame_sha256,...body}=f,s=f.state;
      requireValue(f.schema==='heartbeat04-v1' && f.seq===i && s.run_id===run_id,'Frame identity/order invalid');
      requireValue(f.previous_sha256===chain && frame_sha256===await digest(body) && f.state_sha256===await digest(s),'Frame/state hash mismatch');
      const time=Date.parse(f.last_heartbeat); requireValue(Number.isFinite(time)&&(lastTime===null||time>=lastTime),'Timestamp order invalid');lastTime=time;
      requireValue(!prior || prior.status!=='stopped','Event after terminal');
      if(i===0) { requireValue(s.simulation_tick===0 && f.event===null && f.reason==='ready','Invalid genesis'); eventChain=await digest(s.world); }
      else if(f.event) {
        const {sha256,...e}=f.event;
        requireValue(f.reason==='advanced' && s.simulation_tick===tick+1 && e.tick===tick && e.previous===eventChain && e.before===await digest(prior.state.world) && e.after===await digest(s.world) && sha256===await digest(e),'Event chain/order invalid');
        eventChain=sha256;
      } else requireValue(s.simulation_tick===tick && f.state_sha256===prior.state_sha256,'Status frame mutated state');
      requireValue(s.event_chain===eventChain && s.noise_cursor===s.simulation_tick,'Cursor/event identity invalid');
      const l=ledger(s.world); if(total===null)total=l.total; requireValue(l.total===total,'Conservation failed');
      chain=frame_sha256;tick=s.simulation_tick;prior=f;
    }
    const a=d.audit, terminal=d.frames.at(-1);
    requireValue(a.run_id===run_id && a.world_id===id.world_id && a.verified_revision===id.source_revision && a.verified_state_sha256===terminal.state_sha256 && a.verified_frames===d.frames.length && a.verified_simulation_tick===tick && a.complete_reference_state_continuity===true,'Independent audit identity mismatch');
    requireValue(tick===m.config.max_ticks && terminal.status==='stopped','Incomplete reference');
    return deepFreeze(d);
  }
  function deepFreeze(v) { if(v&&typeof v==='object'){Object.values(v).forEach(deepFreeze);Object.freeze(v);}return v; }
  const snapshots=d=>d.frames.filter((f,i)=>i===0||f.event);
  function history(d,id) { return d.frames.filter(f=>f.event && (f.event.result.targets.includes(id)||f.event.result.product===id||['spent','carried','discarded','endowed','returned'].some(k=>(f.event.result[k]||[]).some(t=>t.actor===id)))); }
  function ancestors(w,id,seen=new Set()) { if(seen.has(id)||!w.history[id]) return [];seen.add(id);const o=w.history[id];return [id,...[...o.parents,o.producer,o.template_parent].filter(Boolean).flatMap(p=>ancestors(w,p,seen))]; }
  const api={canonical,sha,shaPortable,digest,ledger,validate,snapshots,history,ancestors};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Ora=api;
})(globalThis);
