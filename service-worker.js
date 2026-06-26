/* ====================================================================
   StaFlow — Service Worker (PWA básico)
   --------------------------------------------------------------------
   Estratégia:
   - Pre-cache de assets críticos no install (logo, CSS, JS shell)
   - Network-first para HTML (sempre busca atualizações do Vercel)
   - Cache-first para assets estáticos (logo, CSS, fontes)
   - Bypass total para chamadas Supabase/Stripe (sempre online)
   - Auto-update: nova versão do SW dispara controllerchange e
     o app pode mostrar prompt "Recarregar para atualizar"
   ==================================================================== */

const VERSION   = 'staflow-v2'; // v2: app.css no precache (BUG-009)
const CACHE_NAME = 'staflow-' + VERSION;

// Assets críticos pré-cacheados
const PRECACHE = [
  '/colaborador',
  '/app.css',
  '/assets/logo-mark.svg',
  '/auth/auth.css',
  '/js/supabase-client.js',
  '/js/auth.js',
  '/js/route-guard.js',
  '/js/validadores.js',
  '/manifest.json'
];

// Hosts que NUNCA devem ser cacheados (sempre online)
const NEVER_CACHE_HOSTS = [
  'wsxpskrrzqtdoodpoofx.supabase.co',
  'api.stripe.com',
  'checkout.stripe.com',
  'viacep.com.br'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE).catch(() => null))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Bypass total para hosts críticos (Supabase/Stripe/etc)
  if (NEVER_CACHE_HOSTS.some((h) => url.hostname.includes(h))) return;

  // HTML: network-first (busca atualizações; cai no cache se offline)
  const isHTML = req.mode === 'navigate'
    || (req.headers.get('accept') || '').includes('text/html');

  if (isHTML) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // Cacheia uma cópia da resposta HTML
          const copy = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(req, copy)).catch(() => {});
          return res;
        })
        .catch(() => caches.match(req).then((cached) => cached || caches.match('/colaborador')))
    );
    return;
  }

  // Assets estáticos: cache-first
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        // Só cacheia respostas válidas e do nosso origin
        if (res && res.status === 200 && url.origin === self.location.origin) {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => cached);
    })
  );
});

// Mensagem do app para forçar atualização
self.addEventListener('message', (event) => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
