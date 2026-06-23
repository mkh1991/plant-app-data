const ALLOWED_ORIGIN = 'https://mkh1991.github.io';
const PLANTNET_BASE = 'https://my-api.plantnet.org/v2/identify/all';

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    const incomingUrl = new URL(request.url);
    const params = new URLSearchParams(incomingUrl.search);
    params.set('api-key', env.PLANTNET_API_KEY);

    const plantnetUrl = `${PLANTNET_BASE}?${params.toString()}`;

    const upstream = await fetch(plantnetUrl, {
      method: 'POST',
      body: request.body,
      headers: { 'Content-Type': request.headers.get('Content-Type') },
    });

    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
    });
  },
};
