import { afterEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { forwardPolicy } from "../lib/public-api";

const request = (body = '{}', origin = 'http://localhost:3000') => new Request('http://localhost:3000/api/plan', {
  method: 'POST', body, headers: { 'content-type': 'application/json', origin },
});

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe('public API boundary', () => {
  it('rejects arbitrary paths before upstream access', async () => {
    const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
    expect((await forwardPolicy(request(), 'http://attacker/')).status).toBe(404);
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('rejects cross-origin POST requests', async () => {
    const response = await forwardPolicy(request('{}', 'https://attacker.invalid'), 'plan');
    expect(response.status).toBe(403);
  });
  it('rejects malformed and oversized payloads', async () => {
    expect((await forwardPolicy(request('{'), 'plan')).status).toBe(422);
    expect((await forwardPolicy(request('x'.repeat(65537)), 'plan')).status).toBe(413);
  });
  it('does not forward cookies and returns uncacheable JSON', async () => {
    const fetcher = vi.fn().mockResolvedValue(Response.json({ version: 1 }));
    vi.stubGlobal('fetch', fetcher);
    const req = request(); req.headers.set('cookie', 'private=never-forward');
    const response = await forwardPolicy(req, 'plan');
    expect(response.status).toBe(200);
    expect(response.headers.get('cache-control')).toBe('no-store');
    expect(fetcher.mock.calls[0][1].headers.Cookie).toBeUndefined();
    expect(JSON.stringify(fetcher.mock.calls)).not.toContain('never-forward');
  });
  it('sanitizes provider failures', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('SECRET response')));
    const response = await forwardPolicy(request(), 'plan');
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain('SECRET');
  });
  it('does not accept upstream redirects as success', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('redirect', {status: 302})));
    const response = await forwardPolicy(request(), 'plan');
    expect(response.status).toBe(503);
  });
});
