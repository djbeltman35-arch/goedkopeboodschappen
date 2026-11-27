// GET /api/nettorama: de uitgelezen Nettorama-folders (voor de dagelijkse prijzenronde op GitHub).
import { getStore } from '@netlify/blobs';
export default async () => {
  const d = await getStore('nettorama').get('folders', { type: 'json' }).catch(() => null);
  return Response.json(d || { folders: {} }, { headers: { 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' } });
};
export const config = { path: '/api/nettorama', method: ['GET'] };
