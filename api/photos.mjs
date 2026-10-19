// Album photo du mariage — kd2026.fr/photos
// Une seule fonction pour l'album :
//   GET    /api/photos  → liste des photos (mise en cache 90 s par le CDN de Vercel)
//   POST   /api/photos  → ajoute une photo (formulaire : full, thumb, name)
//   DELETE /api/photos  → supprime une photo (JSON : key + token du propriétaire, ou clé admin)
//
// Les photos sont réduites dans le téléphone avant l'envoi (≈ 1600 px + vignette carrée),
// puis rangées dans le Blob store public du projet :
//   p/<id>.<empreinte>.<prénom en base64url>/f.jpg   (photo)
//   p/<id>.<empreinte>.<prénom en base64url>/t.jpg   (vignette)
// <empreinte> = début du SHA-256 d'un jeton aléatoire remis à la personne qui a envoyé la photo :
// elle seule (et les mariés, avec la clé admin) peut la supprimer. Aucun secret n'est stocké ici.

import { put, list, del } from "@vercel/blob";
import { createHash, randomBytes } from "node:crypto";

const ADMIN_SHA256 = "4356fe21215661b2cb442977d90a91fa156dd836879da38481649fd68a936d69";
const PREFIX = "p/";
const MAX_FULL = 3 * 1024 * 1024;   // une photo réduite fait d'habitude 300 à 600 Ko
const MAX_THUMB = 400 * 1024;
const KEY_RE = /^[0-9a-z]{8,12}\.[0-9a-f]{16}\.[A-Za-z0-9_-]{0,220}$/;

const sha256 = (s) => createHash("sha256").update(s).digest("hex");
const json = (body, status = 200, headers = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...headers },
  });

function cleanName(raw) {
  return String(raw || "")
    .normalize("NFC")
    .replace(/[\u0000-\u001f\u007f<>]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 40);
}
const b64url = (s) => Buffer.from(s, "utf8").toString("base64url");
const unb64url = (s) => { try { return Buffer.from(s, "base64url").toString("utf8"); } catch { return ""; } };
const isJpeg = (buf) => buf.length > 3 && buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff;

async function fileBuffer(form, field, max) {
  const f = form.get(field);
  if (!f || typeof f === "string") return { error: "missing " + field };
  if (f.size > max) return { error: field + " too large" };
  const buf = Buffer.from(await f.arrayBuffer());
  if (!isJpeg(buf)) return { error: field + " is not a jpeg" };
  return { buf };
}

async function listPhotos() {
  const groups = new Map();
  let cursor;
  do {
    const page = await list({ prefix: PREFIX, limit: 1000, cursor });
    for (const b of page.blobs) {
      const m = b.pathname.match(/^p\/([^/]+)\/([ft])\.jpg$/);
      if (!m) continue;
      const g = groups.get(m[1]) || { k: m[1] };
      if (m[2] === "f") { g.f = b.url; g.d = b.downloadUrl; g.at = new Date(b.uploadedAt).getTime(); }
      else g.th = b.url;
      groups.set(m[1], g);
    }
    cursor = page.hasMore ? page.cursor : undefined;
  } while (cursor);

  const photos = [];
  for (const g of groups.values()) {
    if (!g.f) continue;                       // vignette orpheline : ignorée
    const [id, , n] = g.k.split(".");
    photos.push({ k: g.k, n: unb64url(n || ""), t: g.at || parseInt(id.slice(0, 8), 36), f: g.f, th: g.th || g.f, d: g.d });
  }
  photos.sort((a, b) => b.t - a.t || (a.k < b.k ? 1 : -1));
  return photos;
}

async function handleGet() {
  try {
    const photos = await listPhotos();
    return json({ photos }, 200, {
      // le navigateur redemande à chaque fois, le CDN de Vercel garde la liste 90 s :
      // cela limite le nombre d'appels à list(), qui sont comptés dans le forfait gratuit
      "cache-control": "public, max-age=0, must-revalidate",
      "vercel-cdn-cache-control": "max-age=90, stale-while-revalidate=600",
    });
  } catch (e) {
    console.error("list failed", e);
    return json({ error: "unavailable" }, 503);
  }
}

async function handlePost(request) {
  let form;
  try { form = await request.formData(); } catch { return json({ error: "bad form" }, 400); }
  const full = await fileBuffer(form, "full", MAX_FULL);
  if (full.error) return json({ error: full.error }, 400);
  const thumb = await fileBuffer(form, "thumb", MAX_THUMB);
  if (thumb.error) return json({ error: thumb.error }, 400);

  const name = cleanName(form.get("name"));
  const token = randomBytes(18).toString("base64url");
  const id = Date.now().toString(36).padStart(8, "0") + randomBytes(3).toString("hex").slice(0, 4);
  const key = `${id}.${sha256(token).slice(0, 16)}.${b64url(name)}`;
  const opts = { access: "public", contentType: "image/jpeg", addRandomSuffix: false, cacheControlMaxAge: 31536000 };

  try {
    const t = await put(`${PREFIX}${key}/t.jpg`, thumb.buf, opts);
    let f;
    try {
      f = await put(`${PREFIX}${key}/f.jpg`, full.buf, opts);
    } catch (e) {
      await del(t.url).catch(() => {});
      throw e;
    }
    return json({ photo: { k: key, n: name, t: Date.now(), f: f.url, th: t.url, d: f.downloadUrl }, token });
  } catch (e) {
    console.error("put failed", e);
    return json({ error: "upload failed" }, 502);
  }
}

async function handleDelete(request) {
  let body;
  try { body = await request.json(); } catch { return json({ error: "bad json" }, 400); }
  const key = String(body && body.k || "");
  if (!KEY_RE.test(key)) return json({ error: "bad key" }, 400);
  const isAdmin = typeof body.admin === "string" && body.admin.length >= 12 && sha256(body.admin) === ADMIN_SHA256;
  const isOwner = typeof body.token === "string" && body.token.length >= 16 && sha256(body.token).slice(0, 16) === key.split(".")[1];
  if (!isAdmin && !isOwner) return json({ error: "forbidden" }, 403);
  try {
    await del([`${PREFIX}${key}/f.jpg`, `${PREFIX}${key}/t.jpg`]);
    return json({ ok: true });
  } catch (e) {
    console.error("delete failed", e);
    return json({ error: "delete failed" }, 502);
  }
}

export default {
  async fetch(request) {
    const url = new URL(request.url);
    // vérifie seulement la clé admin (pour afficher les boutons de suppression)
    if (request.method === "POST" && url.searchParams.has("check-admin")) {
      let body = {};
      try { body = await request.json(); } catch {}
      return json({ ok: typeof body.admin === "string" && sha256(body.admin) === ADMIN_SHA256 });
    }
    if (request.method === "GET" || request.method === "HEAD") return handleGet();
    if (request.method === "POST") return handlePost(request);
    if (request.method === "DELETE") return handleDelete(request);
    return json({ error: "method not allowed" }, 405, { allow: "GET, POST, DELETE" });
  },
};
