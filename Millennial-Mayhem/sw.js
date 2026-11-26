/* Millennial Mayhem project-scoped offline release worker. */
const BASE = "/Millennial-Mayhem/";
const BUILD_ID = "fa5ffa8c7115d5028dd8";
const CACHE_NAME = `millennial-mayhem-release-${BUILD_ID}`;
const REGION_CACHE_PREFIX = `millennial-mayhem-region-${BUILD_ID}-`;
const MANIFEST_URL = `${BASE}precache-manifest.json`;
const REGIONS_URL = `${BASE}offline-regions.json`;
const LICENSED = `${BASE}audio/licensed/`;

function regionCacheName(regionId) {
  if (!/^[A-Z]{2}$/.test(regionId)) throw new Error("invalid regional pack id");
  return `${REGION_CACHE_PREFIX}${regionId}`;
}

function cacheUrl(relative) {
  if (typeof relative !== "string" || relative.startsWith("/") || relative.includes("..") || relative.startsWith("audio/licensed/")) throw new Error("unsafe offline asset path");
  return `${BASE}${relative}`;
}

async function loadRegionManifest(core) {
  const cached = await core.match(REGIONS_URL);
  const response = cached ?? await fetch(REGIONS_URL, { cache: "no-store" });
  if (!response.ok) throw new Error("regional offline manifest unavailable");
  const manifest = await response.json();
  if (manifest.base !== BASE || !Array.isArray(manifest.regions)) throw new Error("regional offline manifest mismatch");
  return manifest;
}

async function findRegion(regionId, core) {
  const manifest = await loadRegionManifest(core);
  const region = manifest.regions.find(item => item.id === regionId);
  if (!region || !Array.isArray(region.paths)) throw new Error("regional offline pack is unavailable");
  return region;
}

async function regionStatus(region, core, optional) {
  const present = await Promise.all(region.paths.map(async item => {
    const url = cacheUrl(item.path);
    const inCore = Boolean(await core.match(url, { ignoreVary: true }));
    const inOptional = Boolean(await optional?.match(url, { ignoreVary: true }));
    return { ready: inCore || inOptional, inCore, inOptional };
  }));
  const readyCount = present.filter(item => item.ready).length;
  return { id: region.id, label: region.label, bytes: region.bytes, ready: readyCount === region.paths.length, readyCount, totalCount: region.paths.length, coreCount: present.filter(item => item.inCore).length, optionalCount: present.filter(item => item.inOptional).length };
}

async function handleRegionMessage(event) {
  const message = event.data;
  const port = event.ports[0];
  const reply = value => port?.postMessage(value);
  const core = await caches.open(CACHE_NAME);
  if (message?.type === "MM_OFFLINE_REGIONS_STATUS") {
    const manifest = await loadRegionManifest(core);
    const existingCaches = new Set(await caches.keys());
    const regions = await Promise.all(manifest.regions.map(async region => {
      const name = regionCacheName(region.id);
      const optional = existingCaches.has(name) ? await caches.open(name) : null;
      return regionStatus(region, core, optional);
    }));
    reply({ ok: true, regions, base: manifest.base });
    return;
  }
  if (message?.type === "MM_REMOVE_OFFLINE_REGIONS") {
    const cacheNames = (await caches.keys()).filter(key => key.startsWith("millennial-mayhem-region-") || key.startsWith("millennial-mayhem-regions-"));
    let removed = 0;
    for (const name of cacheNames) {
      const cache = await caches.open(name);
      removed += (await cache.keys()).length;
      await caches.delete(name);
    }
    reply({ ok: true, removed, removedRegions: cacheNames.length });
    return;
  }
  if (message?.type === "MM_TEST_INTERRUPTED_REGION_DOWNLOAD") {
    const regionId = message.regionId;
    const region = await findRegion(regionId, core);
    const optional = await caches.open(regionCacheName(regionId));
    const before = (await optional.keys()).map(request => request.url).sort();
    const stageName = `millennial-mayhem-region-staging-${BUILD_ID}-${regionId}-${Date.now()}`;
    const staging = await caches.open(stageName);
    let staged = 0;
    try {
      for (const item of region.paths) {
        const url = cacheUrl(item.path);
        if (await core.match(url, { ignoreVary: true }) ?? await optional.match(url, { ignoreVary: true })) continue;
        const response = await fetch(url, { cache: "no-store" });
        if (!response.ok || response.type === "opaque") throw new Error(`Could not download ${item.path} (${response.status})`);
        const bytes = await response.arrayBuffer();
        const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), value => value.toString(16).padStart(2, "0")).join("");
        if (bytes.byteLength !== item.bytes || digest !== item.sha256) throw new Error(`Offline asset verification failed for ${item.path}`);
        await staging.put(url, new Response(bytes, { headers: response.headers }));
        staged += 1;
        break;
      }
      if (!staged) throw new Error("No uncached file was available to exercise interrupted regional download cleanup");
      throw new Error("simulated interruption after the first verified regional file");
    } catch (error) {
      await caches.delete(stageName);
      const after = (await optional.keys()).map(request => request.url).sort();
      reply({ ok: true, simulatedFailure: true, stagedFiles: staged, stagingRemoved: !(await caches.keys()).includes(stageName), optionalCacheUnchanged: JSON.stringify(before) === JSON.stringify(after), reason: error instanceof Error ? error.message : "interrupted" });
    }
    return;
  }
  if (message?.type !== "MM_DOWNLOAD_OFFLINE_REGION") return;
  const regionId = message.regionId;
  const regionCache = regionCacheName(regionId);
  const region = await findRegion(regionId, core);
  const optional = await caches.open(regionCache);
  const alreadyReady = await regionStatus(region, core, optional);
  if (alreadyReady.ready) { reply({ ok: true, regionId, alreadyReady: true, bytes: 0 }); return; }
  const stageName = `millennial-mayhem-region-staging-${BUILD_ID}-${regionId}-${Date.now()}`;
  const staging = await caches.open(stageName);
  try {
    let downloadedBytes = 0;
    for (const item of region.paths) {
      const url = cacheUrl(item.path);
      if (await core.match(url, { ignoreVary: true }) ?? await optional.match(url, { ignoreVary: true })) continue;
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok || response.type === "opaque") throw new Error(`Could not download ${item.path} (${response.status})`);
      const bytes = await response.arrayBuffer();
      const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), value => value.toString(16).padStart(2, "0")).join("");
      if (bytes.byteLength !== item.bytes || digest !== item.sha256) throw new Error(`Offline asset verification failed for ${item.path}`);
      await staging.put(url, new Response(bytes, { headers: response.headers }));
      downloadedBytes += bytes.byteLength;
    }
    for (const request of await staging.keys()) {
      const response = await staging.match(request);
      if (response) await optional.put(request, response);
    }
    await staging.put(`${BASE}__offline-region__/${regionId}`, new Response(JSON.stringify({ id: regionId, buildId: BUILD_ID, savedAt: new Date().toISOString() }), { headers: { "content-type": "application/json" } }));
    await caches.delete(stageName);
    reply({ ok: true, regionId, alreadyReady: false, bytes: downloadedBytes });
  } catch (error) {
    await caches.delete(stageName);
    reply({ ok: false, regionId, error: error instanceof Error ? error.message : "Regional download failed" });
  }
}

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
    await Promise.all(keys.filter(key => (key.startsWith("millennial-mayhem-release-") && key !== CACHE_NAME)
      || (key.startsWith("millennial-mayhem-region-") && !key.startsWith(REGION_CACHE_PREFIX))
      || key.startsWith("millennial-mayhem-regions-")
      || key.startsWith("millennial-mayhem-region-staging-")).map(key => caches.delete(key)));
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
    const optionalCaches = (await caches.keys()).filter(key => key.startsWith(REGION_CACHE_PREFIX));
    let cachedRegion;
    for (const key of optionalCaches) {
      const optional = await caches.open(key);
      cachedRegion = await optional.match(request, { ignoreVary: true });
      if (cachedRegion) break;
    }
    if (cachedRegion) {
      const range = request.headers.get("Range");
      if (range && /^(audio|video)\//i.test(cachedRegion.headers.get("Content-Type") || "")) return cachedMediaRange(cachedRegion, range);
      return cachedRegion;
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
  if (event.data?.type === "MM_OFFLINE_REGIONS_STATUS" || event.data?.type === "MM_DOWNLOAD_OFFLINE_REGION" || event.data?.type === "MM_REMOVE_OFFLINE_REGIONS" || event.data?.type === "MM_TEST_INTERRUPTED_REGION_DOWNLOAD") {
    event.waitUntil(handleRegionMessage(event).catch(error => event.ports[0]?.postMessage({ ok: false, error: error instanceof Error ? error.message : "Offline region operation failed" })));
    return;
  }
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
