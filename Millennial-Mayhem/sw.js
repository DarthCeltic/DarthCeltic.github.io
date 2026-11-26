/* Millennial Mayhem project-scoped offline release worker. */
const BASE = "/Millennial-Mayhem/";
const BUILD_ID = "b2d6d31d7b80af8b0190";
const CACHE_NAME = `millennial-mayhem-release-${BUILD_ID}`;
const MANIFEST_URL = `${BASE}precache-manifest.json`;
const LICENSED = `${BASE}audio/licensed/`;

async function installCompleteRelease() {
  const response = await fetch(MANIFEST_URL, { cache: "no-store" });
  if (!response.ok) throw new Error("release manifest unavailable");
  const manifest = await response.json();
  if (manifest.base !== BASE || manifest.buildId !== BUILD_ID || !Array.isArray(manifest.paths)) throw new Error("release manifest mismatch");
  const urls = manifest.paths.map(path => {
    if (typeof path !== "string" || path.startsWith("/") || path.includes("..") || path.startsWith("audio/licensed/")) throw new Error("unsafe release path");
    return `${BASE}${path}`;
  });
  const staging = await caches.open(CACHE_NAME);
  try {
    await staging.addAll(urls);
    await staging.put(MANIFEST_URL, new Response(JSON.stringify(manifest), { headers: { "content-type": "application/json" } }));
  } catch (error) {
    await caches.delete(CACHE_NAME);
    throw error;
  }
  return manifest;
}

self.addEventListener("install", event => {
  event.waitUntil(installCompleteRelease().then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith("millennial-mayhem-release-") && key !== CACHE_NAME).map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

// Browsers seek inside local audio and film clips with single byte ranges.
async function cachedMediaRange(response, range) {
  const match = /^bytes=(\d*)-(\d*)$/i.exec(range);
  if (!match || (!match[1] && !match[2])) return response;
  const file = await response.blob();
  const size = file.size;
  const start = match[1] ? Number(match[1]) : Math.max(0, size - Number(match[2]));
  const end = match[1] && match[2] ? Math.min(size - 1, Number(match[2])) : size - 1;
  if (start > end || start >= size) {
    return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
  }
  const headers = new Headers(response.headers);
  headers.delete("Content-Encoding");
  headers.set("Accept-Ranges", "bytes");
  headers.set("Content-Range", `bytes ${start}-${end}/${size}`);
  headers.set("Content-Length", String(end - start + 1));
  return new Response(file.slice(start, end + 1, file.type), { status: 206, headers });
}

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || !url.pathname.startsWith(BASE) || url.pathname.startsWith(LICENSED)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    // Precache installation uses Cache.addAll requests whose default headers
    // can differ from module/stylesheet requests in Chromium and Firefox.
    // These are immutable, same-origin hashed release assets, so matching the
    // exact URL while ignoring only Vary keeps the complete offline release
    // usable for lazy chunks as well as the document shell.
    const cached = await cache.match(request, { ignoreVary: true });
    if (cached) {
      const range = request.headers.get("Range");
      if (range && /^(audio|video)\//i.test(cached.headers.get("Content-Type") || "")) {
        return cachedMediaRange(cached, range);
      }
      return cached;
    }
    try {
      const response = await fetch(request);
      if (response.status === 200 && response.type !== "opaque") await cache.put(request, response.clone());
      return response;
    } catch {
      if (request.mode === "navigate") return (await cache.match(`${BASE}index.html`)) ?? Response.error();
      return Response.error();
    }
  })());
});

self.addEventListener("message", event => {
  if (event.data?.type !== "MM_TEST_INTERRUPTED_UPGRADE") return;
  event.waitUntil((async () => {
    const prior = await caches.keys();
    const priorRelease = prior.find(key => key.startsWith("millennial-mayhem-release-"));
    const stagingName = `millennial-mayhem-test-staging-${Date.now()}`;
    try {
      const staging = await caches.open(stagingName);
      await staging.addAll([`${BASE}index.html`]);
      if (!await staging.match(`${BASE}index.html`)) throw new Error("partial release asset was not staged");
      throw new Error("simulated interruption after the first release asset");
    } catch {
      await caches.delete(stagingName);
      const after = await caches.keys();
      event.ports[0]?.postMessage({ ok: true, priorReleasePreserved: Boolean(priorRelease && after.includes(priorRelease)), stagingRemoved: !after.includes(stagingName) });
    }
  })());
});
