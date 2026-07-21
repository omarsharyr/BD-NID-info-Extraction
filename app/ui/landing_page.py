"""Focused landing page for the Bangladesh NID extraction service."""

from __future__ import annotations

from textwrap import dedent


def build_landing_page_html(app_name: str, version: str) -> str:
    html = dedent(
        """<!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width,initial-scale=1">
          <meta name="description" content="Extract and translate Bangladesh NID data from front and back images into structured JSON.">
          <meta name="theme-color" content="#f7f4ea">
          <title>__APP_NAME__ — Bangladesh NID extraction</title>
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,440;9..144,560;9..144,650&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
          <style>
            :root{--ink:#17231d;--muted:#6c7364;--line:#ded5bd;--paper:#f7f4ea;--panel:#fff;--green:#00693e;--green-deep:#0a3a24;--red:#c8102e;--danger:#a4291d;--radius:16px;--radius-lg:24px;--shadow:0 30px 80px rgba(23,35,29,.14)}
            *{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--paper);font-family:"IBM Plex Sans",system-ui,-apple-system,sans-serif;-webkit-font-smoothing:antialiased}button,input{font:inherit}a{color:inherit}h1,h2,h3{font-family:Fraunces,ui-serif,Georgia,serif}.container{width:min(1120px,calc(100% - 40px));margin:auto}.skip{position:fixed;top:10px;left:10px;z-index:20;padding:10px 14px;color:#fff;background:var(--ink);border-radius:10px;transform:translateY(-150%)}.skip:focus{transform:none}:focus-visible{outline:3px solid rgba(0,105,62,.55);outline-offset:3px}
            .nav{position:sticky;top:0;z-index:10;padding:16px 0;background:rgba(247,244,234,.86);backdrop-filter:blur(18px);border-bottom:1px solid var(--line)}.nav-in{display:flex;align-items:center;justify-content:space-between;gap:24px}.brand{display:flex;align-items:center;gap:11px;text-decoration:none;font-weight:700}.brand span:last-child{font-family:Fraunces,serif;font-size:1.05rem;letter-spacing:-.01em}.mark{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;color:#f7f4ea;background:linear-gradient(155deg,var(--green),var(--green-deep));box-shadow:0 10px 22px rgba(10,58,36,.25)}.mark svg{width:19px}.links{display:flex;align-items:center;gap:24px}.links a{text-decoration:none;color:var(--muted);font-size:.92rem;font-weight:600}.links a:hover{color:var(--ink)}
            .button{display:inline-flex;align-items:center;justify-content:center;gap:9px;min-height:46px;padding:0 19px;border:1px solid var(--line);border-radius:12px;text-decoration:none;font-weight:650;cursor:pointer;transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease}.button:hover{transform:translateY(-1px)}.button.primary{color:#f7f4ea;border:0;background:linear-gradient(155deg,var(--green),var(--green-deep));box-shadow:0 14px 30px rgba(10,58,36,.24)}.button.ghost{background:var(--panel)}
            .hero{position:relative;overflow:hidden;padding:84px 0 60px;background-image:repeating-linear-gradient(115deg,rgba(10,58,36,.035) 0 2px,transparent 2px 34px)}.hero-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:52px;align-items:center}.eyebrow{display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid var(--line);border-radius:999px;color:var(--green-deep);background:rgba(255,255,255,.7);font-size:.76rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.dot{width:7px;height:7px;border-radius:50%;background:var(--red);box-shadow:0 0 0 5px rgba(200,16,46,.14)}h1{max-width:620px;margin:22px 0 18px;font-weight:650;font-size:clamp(2.5rem,5.6vw,4.1rem);line-height:1.04;letter-spacing:-.02em}h1 em{font-style:normal;color:var(--green-deep)}.lead{max-width:520px;margin:0;color:var(--muted);font-size:clamp(1.02rem,1.6vw,1.15rem);line-height:1.7}.hero-actions{display:flex;gap:12px;margin-top:30px;flex-wrap:wrap}.facts{display:flex;gap:24px;margin-top:32px;flex-wrap:wrap;color:var(--muted);font-size:.88rem}.facts span{display:flex;align-items:center;gap:8px}.check{color:var(--green);font-weight:900}
            .id-visual{position:relative;height:360px}.id-card{position:absolute;width:302px;max-width:88%;aspect-ratio:1.586/1;border-radius:18px;padding:20px;border:1px solid rgba(23,35,29,.08);box-shadow:var(--shadow);overflow:hidden}.id-card.back{top:6px;left:0;background:linear-gradient(160deg,#fff,#f0ecdd);transform:rotate(-8deg)}.id-card.front{bottom:6px;right:0;background:linear-gradient(160deg,var(--green),var(--green-deep));color:#eef7f1;transform:rotate(5deg)}.id-card:before{content:"";position:absolute;inset:0;background-image:repeating-linear-gradient(72deg,rgba(255,255,255,.05) 0 1px,transparent 1px 7px);pointer-events:none}.id-card.back .id-row{height:7px;border-radius:4px;background:rgba(23,35,29,.09);margin-bottom:10px}.id-card.back .id-row:nth-child(1){width:64%}.id-card.back .id-row:nth-child(2){width:88%}.id-card.back .id-row:nth-child(3){width:74%}.id-card.back .id-barcode{display:flex;gap:2px;margin-top:16px}.id-card.back .id-barcode i{width:2px;background:rgba(23,35,29,.18);border-radius:1px}.id-top{display:flex;justify-content:space-between;align-items:flex-start;position:relative;z-index:1}.id-chip{width:34px;height:25px;border-radius:5px;background:linear-gradient(155deg,#f1d78c,#c9a35a)}.id-word{font-family:"IBM Plex Mono",monospace;font-size:.62rem;letter-spacing:.14em;opacity:.85}.id-mid{display:flex;gap:12px;margin-top:18px;position:relative;z-index:1}.id-photo{width:52px;height:64px;border-radius:6px;background:rgba(255,255,255,.16);flex:none}.id-lines{flex:1;display:flex;flex-direction:column;justify-content:center;gap:8px}.id-lines i{display:block;height:6px;border-radius:3px;background:rgba(255,255,255,.32)}.id-lines i:nth-child(1){width:80%}.id-lines i:nth-child(2){width:55%}.id-lines i:nth-child(3){width:66%}.id-badge{position:absolute;left:38%;top:44%;width:52px;height:52px;border-radius:50%;background:var(--red);color:#fdece9;display:grid;place-items:center;font-size:1.3rem;font-weight:800;box-shadow:0 12px 24px rgba(200,16,46,.3);transform:rotate(-10deg);z-index:2}
            .workspace{display:grid;grid-template-columns:.88fr 1.12fr;gap:20px;margin:16px auto 96px}.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius-lg);box-shadow:var(--shadow)}.upload-card{padding:28px}.card-head{display:flex;justify-content:space-between;gap:16px;align-items:start;margin-bottom:22px}.card-head h2,.section-head h2{margin:0;font-weight:600;font-size:clamp(1.5rem,2.6vw,2rem);letter-spacing:-.01em}.card-head p,.section-head p{margin:8px 0 0;color:var(--muted);line-height:1.6}.secure{padding:7px 11px;border-radius:999px;color:var(--green-deep);background:rgba(0,105,62,.09);font-size:.74rem;font-weight:700;white-space:nowrap}.drop-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.drop{position:relative;display:grid;place-items:center;min-height:190px;padding:20px;text-align:center;border:1.5px dashed var(--line);border-radius:16px;background:#fbf9f2;cursor:pointer;transition:.2s ease}.drop:hover,.drop.drag{border-color:var(--green);background:rgba(0,105,62,.05)}.drop.has-file{border-style:solid;border-color:#9fcdb2;background:#f2f8f4}.drop input{position:absolute;inset:0;width:100%;height:100%;opacity:0;cursor:pointer}.upload-icon{display:grid;place-items:center;width:46px;height:46px;margin:auto auto 12px;border-radius:13px;color:var(--green-deep);background:rgba(0,105,62,.1)}.drop strong{display:block}.drop small{display:block;margin-top:6px;color:var(--muted)}.submit{width:100%;margin-top:14px}.status{min-height:22px;margin:12px 2px 0;color:var(--muted);font-size:.88rem}.status.error{color:var(--danger)}
            .result-card{overflow:hidden;background:var(--green-deep);color:#dce9e0;border:1px solid rgba(255,255,255,.08);border-radius:var(--radius-lg);box-shadow:0 28px 80px rgba(10,30,20,.28)}.result-top{display:flex;justify-content:space-between;align-items:center;padding:18px 20px;border-bottom:1px solid rgba(255,255,255,.08)}.result-top span{font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.result-actions{display:flex;gap:8px}.icon-btn{padding:7px 10px;color:#c9d8ce;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.09);border-radius:9px;cursor:pointer;text-decoration:none;font-size:.85rem}.code{min-height:440px;margin:0;padding:24px;overflow:auto;color:#d3e2d8;font:14px/1.72 "IBM Plex Mono","SFMono-Regular",Consolas,monospace;white-space:pre-wrap}.key{color:#f1cd8a}.string{color:#a9e0bf}.bool{color:#f0a99a}
            .section{padding:80px 0}.section.white{background:var(--panel);border-block:1px solid var(--line)}.section-head{max-width:640px;margin-bottom:34px}.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.step{padding:25px;border:1px solid var(--line);border-radius:18px;background:var(--paper)}.section.white .step{background:var(--panel)}.step-no{display:grid;place-items:center;width:34px;height:34px;margin-bottom:22px;border-radius:10px;color:#f7f4ea;background:linear-gradient(155deg,var(--green),var(--green-deep));font-weight:700;font-family:Fraunces,serif}.step h3{margin:0 0 9px;font-weight:600;font-size:1.1rem}.step p{margin:0;color:var(--muted);line-height:1.65}.footer{padding:30px 0;color:var(--muted);border-top:1px solid var(--line);font-size:.9rem}.footer-in{display:flex;justify-content:space-between;gap:20px;align-items:center}
            .reveal{opacity:0;transform:translateY(16px);transition:opacity .55s ease,transform .55s ease}.reveal.visible{opacity:1;transform:none}
            @media(max-width:850px){.hero-grid{grid-template-columns:1fr}.id-visual{height:300px;margin-top:20px}.workspace{grid-template-columns:1fr}.links a:not(.button){display:none}.workspace{margin-bottom:60px}.steps{grid-template-columns:1fr}.result-card{min-height:400px}.code{min-height:360px}}
            @media(max-width:560px){.container{width:min(100% - 24px,1120px)}.nav{padding:10px 0}.brand span:last-child{display:none}.hero{padding:60px 0 40px}h1{font-size:clamp(2.3rem,12vw,3.2rem)}.drop-grid{grid-template-columns:1fr}.upload-card{padding:18px}.drop{min-height:150px}.section{padding:60px 0}.footer-in{align-items:start;flex-direction:column}.id-card{width:260px}}
            @media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{animation-duration:.01ms!important;transition-duration:.01ms!important}.reveal{opacity:1;transform:none}}
          </style>
        </head>
        <body>
          <a class="skip" href="#main">Skip to content</a>
          <header class="nav"><div class="container nav-in">
            <a class="brand" href="#main"><span class="mark"><svg viewBox="0 0 24 24" fill="none"><path d="M7 5.5h10a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z" stroke="currentColor" stroke-width="1.8"/><path d="M8.5 9h7M8.5 12h7M8.5 15h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></span><span>__APP_NAME__</span></a>
            <nav class="links" aria-label="Primary"><a href="#workflow">How it works</a><a class="button primary" href="#extract">Try extraction</a></nav>
          </div></header>

          <main id="main">
            <section class="hero"><div class="container hero-grid">
              <div class="reveal">
                <div class="eyebrow"><span class="dot"></span>Bangladesh NID extraction</div>
                <h1>Two images in.<br><em>Clean JSON out.</em></h1>
                <p class="lead">Upload the front and back of a Bangladesh National ID. Gemini reads Bengali and English text in one pass, translates key fields by meaning, and returns a predictable API response.</p>
                <div class="hero-actions"><a class="button primary" href="#extract">Try extraction</a><a class="button ghost" href="#workflow">See how it works</a></div>
                <div class="facts"><span><b class="check">✓</b> JPG, JPEG &amp; PNG</span><span><b class="check">✓</b> Gemini vision + translation</span><span><b class="check">✓</b> Docker ready</span><span><b class="check">✓</b> Graceful partial results</span></div>
              </div>
              <div class="id-visual reveal" aria-hidden="true">
                <div class="id-card back"><div class="id-row"></div><div class="id-row"></div><div class="id-row"></div><div class="id-barcode"><i style="height:16px"></i><i style="height:22px"></i><i style="height:14px"></i><i style="height:24px"></i><i style="height:18px"></i><i style="height:12px"></i><i style="height:20px"></i></div></div>
                <div class="id-card front">
                  <div class="id-top"><div class="id-chip"></div><span class="id-word">BGD · NID</span></div>
                  <div class="id-mid"><div class="id-photo"></div><div class="id-lines"><i></i><i></i><i></i></div></div>
                </div>
                <div class="id-badge">✓</div>
              </div>
            </div></section>

            <section class="container workspace reveal" id="extract" aria-label="NID extraction demo">
              <form class="card upload-card" id="extract-form">
                <div class="card-head"><div><h2>Upload NID images</h2><p>Both sides are required.</p></div><span class="secure">Local processing</span></div>
                <div class="drop-grid">
                  <label class="drop" data-drop><input name="front_image" type="file" accept="image/jpeg,image/png" required><span><span class="upload-icon">↑</span><strong>NID front</strong><small>Choose or drop image<br>JPG, JPEG, PNG</small></span></label>
                  <label class="drop" data-drop><input name="back_image" type="file" accept="image/jpeg,image/png" required><span><span class="upload-icon">↑</span><strong>NID back</strong><small>Choose or drop image<br>JPG, JPEG, PNG</small></span></label>
                </div>
                <div style="display:flex;gap:10px;margin-top:14px">
                  <button class="button primary submit" type="submit" style="margin-top:0;flex:2">Extract NID data <span aria-hidden="true">→</span></button>
                  <button class="button ghost" id="clear-form" type="button" style="flex:1">Clear</button>
                </div>
                <div class="status" id="form-status" role="status" aria-live="polite">Images are processed by this API instance.</div>
              </form>
              <div class="result-card" aria-label="JSON response preview">
                <div class="result-top"><span>Structured response</span><div class="result-actions"><a class="icon-btn" href="/docs">Schema</a><button class="icon-btn" id="copy-json" type="button">Copy</button></div></div>
                <pre class="code" id="json-output">{
  <span class="key">"name"</span>: <span class="string">"Md. Rahim"</span>,
  <span class="key">"fatherName"</span>: <span class="string">"Abdul Karim"</span>,
  <span class="key">"motherName"</span>: <span class="string">"Amena Begum"</span>,
  <span class="key">"dateOfBirth"</span>: <span class="string">"1998-01-15"</span>,
  <span class="key">"nidNumber"</span>: <span class="string">"1234567890123"</span>,
  <span class="key">"presentAddress"</span>: <span class="string">"Dhaka, Bangladesh"</span>,
  <span class="key">"permanentAddress"</span>: <span class="string">"Cumilla, Bangladesh"</span>
}</pre>
              </div>
            </section>

            <section class="section white" id="workflow"><div class="container">
              <div class="section-head reveal"><div class="eyebrow">Core workflow</div><h2>Focused on one job.</h2><p>No unnecessary product layers—just a clear path from NID images to usable data.</p></div>
              <div class="steps">
                <article class="step reveal"><div class="step-no">1</div><h3>Validate both images</h3><p>Accept front and back files in JPG, JPEG, or PNG. Missing, unsupported, corrupted, and unreadable images return meaningful errors.</p></article>
                <article class="step reveal"><div class="step-no">2</div><h3>Read and translate</h3><p>Extract all readable Bengali and English text in a single pass. Bengali identity fields are translated naturally while preserving their meaning.</p></article>
                <article class="step reveal"><div class="step-no">3</div><h3>Return structured JSON</h3><p>Receive the seven required camelCase fields. Any unreadable field is returned as null so partial extraction remains predictable.</p></article>
              </div>
            </div></section>

          </main>

          <footer class="footer"><div class="container footer-in"><span>__APP_NAME__ · v__VERSION__</span><span>Private, focused NID extraction.</span></div></footer>
          <script>
            (()=>{
              const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,items=document.querySelectorAll('.reveal');
              if(reduced||!('IntersectionObserver'in window))items.forEach(x=>x.classList.add('visible'));else{const observer=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('visible');observer.unobserve(e.target)}}),{threshold:.12});items.forEach(x=>observer.observe(x))}
              document.querySelectorAll('[data-drop]').forEach(drop=>{const input=drop.querySelector('input'),small=drop.querySelector('small');small.dataset.default=small.innerHTML;input.addEventListener('change',()=>{if(input.files[0]){drop.classList.add('has-file');small.textContent=input.files[0].name}});['dragenter','dragover'].forEach(name=>drop.addEventListener(name,()=>drop.classList.add('drag')));['dragleave','drop'].forEach(name=>drop.addEventListener(name,()=>drop.classList.remove('drag'))) });
              const form=document.querySelector('#extract-form'),status=document.querySelector('#form-status'),output=document.querySelector('#json-output'),defaultStatus=status.textContent;
              form.addEventListener('submit',async event=>{event.preventDefault();status.className='status';status.textContent='Reading both NID images…';const button=form.querySelector('[type=submit]');button.disabled=true;try{const response=await fetch('/api/v1/nid/extract',{method:'POST',body:new FormData(form)}),payload=await response.json();output.textContent=JSON.stringify(payload,null,2);if(!response.ok)throw new Error(payload.error?.message||'Extraction failed.');status.textContent=Object.values(payload).some(value=>value===null)?'Partial extraction complete — unreadable fields are null.':'Extraction complete.'}catch(error){status.className='status error';status.textContent=error.message}finally{button.disabled=false}});
              document.querySelector('#copy-json').addEventListener('click',event=>{navigator.clipboard.writeText(output.textContent);event.currentTarget.textContent='Copied'});
              document.querySelector('#clear-form').addEventListener('click',()=>{form.reset();document.querySelectorAll('[data-drop]').forEach(drop=>{drop.classList.remove('has-file');const small=drop.querySelector('small');small.innerHTML=small.dataset.default});status.className='status';status.textContent=defaultStatus;output.textContent='{\\n  \\"name\\": null,\\n  \\"fatherName\\": null,\\n  \\"motherName\\": null,\\n  \\"dateOfBirth\\": null,\\n  \\"nidNumber\\": null,\\n  \\"presentAddress\\": null,\\n  \\"permanentAddress\\": null\\n}'});
            })();
          </script>
        </body></html>"""
    )
    return html.replace("__APP_NAME__", app_name).replace("__VERSION__", version)
