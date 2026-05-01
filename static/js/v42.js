(function(){
  const LANG=document.body.dataset.lang||'ar'; const TR={ar:{'Copied':'تم النسخ','Mailbox created':'تم إنشاء البريد','Create failed':'فشل الإنشاء','Creating...':'جارٍ الإنشاء...','Create temporary mailbox':'إنشاء بريد مؤقت','Inbox updated. New messages: ':'تم تحديث البريد. رسائل جديدة: ','New email received':'وصلت رسالة جديدة','No messages yet. Waiting for new mail...':'لا توجد رسائل بعد. بانتظار بريد جديد...','Refresh failed':'فشل التحديث','Inbox marked read':'تم تحديد رسائل البريد كمقروءة','Unread':'غير مقروء','Primary':'أساسي','Sub':'فرعي','Copy code':'نسخ الكود','Copy link':'نسخ الرابط','Open':'فتح','From: ':'من: ','unknown':'غير معروف','(No subject)':'(بدون عنوان)'}}; function t(x){return LANG==='en'?x:(TR.ar[x]||x);} function copyText(text){navigator.clipboard&&navigator.clipboard.writeText(text).then(()=>toast(t('Copied')));}
  function toast(msg){let t=document.createElement('div');t.textContent=msg;t.style.cssText='position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:#101b2e;color:#eaf2ff;border:1px solid #243653;border-radius:12px;padding:10px 14px;z-index:99';document.body.appendChild(t);setTimeout(()=>t.remove(),1600)}
  let swRegistration=null;
  async function ensureServiceWorker(){
    if(!('serviceWorker' in navigator)) return null;
    if(swRegistration) return swRegistration;
    try{ swRegistration=await navigator.serviceWorker.register('/sw.js'); return swRegistration; }catch(e){ console.warn('Vemail SW failed',e); return null; }
  }
  async function showNativeNotification(payload){
    if(!payload || !('Notification' in window)) return false;
    if(Notification.permission!=='granted') return false;
    const reg=await ensureServiceWorker();
    const opts={body:payload.body||'', tag:payload.tag||'vemail', data:{url:payload.url||'/inbox'}, renotify:true, icon:'/static/icon-192.png', badge:'/static/icon-192.png'};
    try{ if(reg && reg.showNotification){ await reg.showNotification(payload.title||'Vemail',opts); return true; } new Notification(payload.title||'Vemail', opts); return true; }catch(e){ console.warn('Vemail notification failed',e); return false; }
  }
  async function enableBrowserNotifications(){
    if(!('Notification' in window)){ toast(LANG==='en'?'Browser notifications are not supported.':'إشعارات المتصفح غير مدعومة على هذا الجهاز.'); return; }
    await ensureServiceWorker();
    let permission=Notification.permission;
    if(permission==='default') permission=await Notification.requestPermission();
    if(permission==='granted'){
      toast(LANG==='en'?'Browser notifications enabled':'تم تفعيل إشعارات المتصفح');
      try{ const r=await fetch('/api/browser-notification-test',{method:'POST',headers:{'Accept':'application/json','X-CSRFToken':document.body.dataset.csrf||''}}); const j=await r.json(); if(j.ok) showNativeNotification(j.notification); }catch(e){}
    }else{ toast(LANG==='en'?'Notification permission is blocked.':'إذن الإشعارات مرفوض من المتصفح.'); }
  }
  function esc(v){return String(v==null?'':v).replace(/[&<>'"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]});}
  function drawAdminChart(){
    const canvas=document.getElementById('adminChart');
    if(!canvas) return;
    const data=JSON.parse(canvas.dataset.chart||'[]');
    const parent=canvas.parentElement;
    const cssWidth=Math.max(260, Math.floor(parent.clientWidth));
    const cssHeight=Math.max(120, Math.floor(canvas.clientHeight||150));
    const dpr=window.devicePixelRatio||1;
    canvas.width=Math.floor(cssWidth*dpr);
    canvas.height=Math.floor(cssHeight*dpr);
    canvas.style.width='100%';
    canvas.style.height=cssHeight+'px';
    const ctx=canvas.getContext('2d');
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.clearRect(0,0,cssWidth,cssHeight);
    ctx.strokeStyle='#243653';ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(0,cssHeight-24);ctx.lineTo(cssWidth,cssHeight-24);ctx.stroke();
    function line(key,color,offset){
      if(!data.length) return;
      let max=Math.max(1,...data.map(d=>Number(d[key]||0)));
      ctx.beginPath();
      data.forEach((d,i)=>{let x=18+i*((cssWidth-36)/(data.length-1||1));let y=cssHeight-30-(Number(d[key]||0)/max)*(cssHeight-58)-offset;if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y)});
      ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();
    }
    line('new_users','#5eead4',0);line('messages','#60a5fa',5);line('payments','#facc15',10);
  }
  function setInboxBadges(count){
    count=Number(count||0);
    document.querySelectorAll('.nav-inbox').forEach(function(link){
      let badge=link.querySelector('.mail-badge');
      if(count>0){
        if(!badge){badge=document.createElement('span');badge.className='mail-badge';badge.title=t('Unread');link.appendChild(badge)}
        badge.textContent=String(count);
        link.classList.add('has-unread-mail');
      }else{
        if(badge) badge.remove();
        link.classList.remove('has-unread-mail');
      }
    });
  }
  function setNotificationBadges(count){
    count=Number(count||0);
    document.querySelectorAll('.bell').forEach(function(link){
      let badge=link.querySelector('.notif-badge');
      if(count>0){
        if(!badge){badge=document.createElement('b');badge.className='notif-badge';link.appendChild(badge)}
        badge.textContent=String(count);
      }else if(badge){badge.remove();}
    });
    document.querySelectorAll('[data-notification-count]').forEach(function(el){el.textContent=String(count);});
  }
  async function refreshUiState(){
    const res=await fetch('/api/ui/state',{headers:{'Accept':'application/json'}});
    if(!res.ok) return;
    const j=await res.json();
    if(!j.ok) return;
    setInboxBadges(j.unread_messages||0);
    setNotificationBadges(j.unread_notifications||0);
    if(Array.isArray(j.browser_notifications)){ j.browser_notifications.forEach(showNativeNotification); }
  }
  function renderMessageCard(m, index){
    const hidden=index>=10?' hidden-more':'';
    const unread=m.read?'':' unread';
    const dot=m.read?'':'<span class="unread-dot" title="Unread"></span>';
    const type=m.is_primary?t('Primary'):t('Sub');
    const codeBtn=m.first_code?`<button class="btn small" data-copy-text="${esc(m.first_code)}">${t('Copy code')}</button>`:'';
    const linkBtn=m.first_link?`<button class="btn small" data-copy-text="${esc(m.first_link)}">${t('Copy link')}</button>`:'';
    return `<article class="mail-card reveal-item${unread}${hidden}">
      <div class="mail-main">
        <h3>${dot}${esc(m.subject||t('(No subject)'))}</h3>
        <p class="muted">${t('From: ')}${esc(m.sender||t('unknown'))}</p>
        <p class="mailbox-line"><span class="pill">${type}</span> <code>${esc(m.mailbox_address||'')}</code></p>
      </div>
      <div class="mail-actions">
        <small>${esc(m.received_at||'')}</small>
        <a class="btn small" href="${esc(m.url)}">${t('Open')}</a>
        ${codeBtn}
        ${linkBtn}
      </div>
    </article>`;
  }
  async function refreshInboxLive(options){
    const list=document.querySelector('.inbox-list');
    if(!list) return;
    const params=new URLSearchParams(window.location.search);
    const res=await fetch('/api/inbox/live?'+params.toString(), {headers:{'Accept':'application/json'}});
    const j=await res.json();
    if(!j.ok) throw new Error(j.error||'Inbox refresh failed');
    setInboxBadges(Number(j.unread||0));
    const oldFirst=list.querySelector('.mail-card a.btn.small')?.getAttribute('href')||'';
    if(!j.messages.length){
      list.innerHTML='<div class="empty card">'+t('No messages yet. Waiting for new mail...')+'</div>';
    }else{
      list.innerHTML=j.messages.map(renderMessageCard).join('');
    }
    let show=document.getElementById('showMore');
    if(j.messages.length>10){
      if(!show){show=document.createElement('button');show.className='btn full';show.id='showMore';show.textContent=LANG==='en'?'Show more':'عرض المزيد';list.insertAdjacentElement('afterend',show);}
    }else if(show){show.remove();}
    const newFirst=list.querySelector('.mail-card a.btn.small')?.getAttribute('href')||'';
    if(options&&options.manual) toast(t('Inbox updated. New messages: ')+(j.new||0));
    else if(j.new>0 || (oldFirst && newFirst && oldFirst!==newFirst)) toast(t('New email received'));
  }
  document.addEventListener('click',async function(e){
    const nav=e.target.closest('.nav-toggle'); if(nav){const menu=document.getElementById('topnav'); menu&&menu.classList.toggle('open'); nav.setAttribute('aria-expanded', menu&&menu.classList.contains('open')?'true':'false'); return;}
    const browserNotify=e.target.closest('.enable-browser-notifications'); if(browserNotify){ enableBrowserNotifications(); return; }
    const copyTarget=e.target.closest('[data-copy-target]'); if(copyTarget){const el=document.getElementById(copyTarget.dataset.copyTarget); if(el) copyText(el.innerText.trim());}
    const copy=e.target.closest('[data-copy-text]'); if(copy) copyText(copy.dataset.copyText);
    const eye=e.target.closest('.eye'); if(eye){const input=eye.parentElement.querySelector('input'); input.type=input.type==='password'?'text':'password';}
    if(e.target.id==='showMore'){document.querySelectorAll('.hidden-more').forEach(x=>x.classList.remove('hidden-more'));e.target.remove();}
    if(e.target.id==='refreshInbox'){
      e.target.disabled=true;
      refreshInboxLive({manual:true}).catch(()=>toast(t('Refresh failed'))).finally(()=>e.target.disabled=false);
    }
  });
  document.addEventListener('submit', async function(e){
    const form=e.target.closest('.mark-read-form');
    if(!form) return;
    e.preventDefault();
    const btn=form.querySelector('button');
    if(btn) btn.disabled=true;
    try{
      const res=await fetch(form.action,{method:'POST',headers:{'Accept':'application/json','X-CSRFToken':document.body.dataset.csrf||''},body:new FormData(form)});
      const j=await res.json();
      if(!j.ok) throw new Error(j.error||'failed');
      setInboxBadges(j.unread||0);
      document.querySelectorAll('.mail-card.unread').forEach(card=>{card.classList.remove('unread'); const dot=card.querySelector('.unread-dot'); if(dot) dot.remove();});
      toast(t('Inbox marked read'));
    }catch(err){
      form.submit();
    }finally{
      if(btn) btn.disabled=false;
    }
  });
  const createBtn=document.getElementById('createTempBtn');
  if(createBtn){createBtn.addEventListener('click',()=>{createBtn.disabled=true;createBtn.textContent=t('Creating...');fetch('/api/temp-mailbox',{method:'POST'}).then(r=>r.json().catch(()=>({ok:false,error:'Invalid server response'}))).then(j=>{if(j.ok){document.getElementById('tempMailboxText').innerText=j.mailbox;document.getElementById('tempMailboxCard').style.display='block';toast(t('Mailbox created'))}else{toast(j.error||t('Create failed'))}}).catch(e=>toast(t('Create failed')+': '+e.message)).finally(()=>{createBtn.disabled=false;createBtn.textContent=t('Create temporary mailbox')})})}
  if(document.body.dataset.authenticated==='1') {
    ensureServiceWorker();
    setTimeout(()=>refreshUiState().catch(()=>{}), 1500);
    setInterval(()=>refreshUiState().catch(()=>{}), 15000);
  }
  if(document.querySelector('.inbox-list')){
    setTimeout(()=>refreshInboxLive({silent:true}).catch(()=>{}), 2500);
    setInterval(()=>refreshInboxLive({silent:true}).catch(()=>{}), 15000);
  }
  drawAdminChart();
  window.addEventListener('resize',()=>{clearTimeout(window.__vemailChartTimer);window.__vemailChartTimer=setTimeout(drawAdminChart,120)});
})();
