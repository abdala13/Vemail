self.addEventListener('install', function(event){ self.skipWaiting(); });
self.addEventListener('activate', function(event){ event.waitUntil(self.clients.claim()); });
self.addEventListener('notificationclick', function(event){
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || '/inbox';
  event.waitUntil((async function(){
    const allClients = await clients.matchAll({type:'window', includeUncontrolled:true});
    for (const client of allClients) {
      if ('focus' in client) { client.navigate(url); return client.focus(); }
    }
    if (clients.openWindow) return clients.openWindow(url);
  })());
});
