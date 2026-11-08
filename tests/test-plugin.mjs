import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import plugin from '../.opencode/plugins/hybrid-sage.mjs';

function context() {
  const state = { mcp: new Map(), skills: [], commands: [], hooks: new Map(), prompts: [] };
  return {
    state,
    mcp: { transform: async (fn) => fn({ set: (name, config) => state.mcp.set(name, config) }) },
    skill: { transform: async (fn) => fn({ add: (skill) => state.skills.push(skill) }) },
    command: { transform: async (fn) => fn({ add: (command) => state.commands.push(command) }) },
    session: {
      hook: async (name, fn) => state.hooks.set(name, fn),
      prompt: async (prompt) => state.prompts.push(prompt),
    },
  };
}

test('v2 registers working MCP, routing skill, commands, and owned context parts', async () => {
  const ctx = context();
  await plugin.setup(ctx);
  assert.equal(plugin.id, 'hybrid-sage');
  assert.equal(ctx.state.mcp.get('hybrid-sage').type, 'local');
  assert.equal(ctx.state.mcp.get('hybrid-sage').disabled, false);
  assert.equal(ctx.state.skills[0].name, 'model-router');
  assert.ok(ctx.state.skills[0].content.includes('free-only'));
  const event = { system: [{ type: 'text', text: 'existing owner' }] };
  await ctx.state.hooks.get('context')(event);
  assert.equal(event.system[0].text, 'existing owner');
  assert.ok(event.system[1].text.includes('THREE-HARNESS'));
  const command = ctx.state.commands.find((item) => item.name === 'route');
  await command.execute({ sessionID: 'test-session', prompt: { text: 'Review parser', files: [{ path: 'parser.py', mention: 'x' }] }, delivery: 'queue' });
  assert.ok(ctx.state.prompts[0].text.includes('Review parser'));
  assert.equal(ctx.state.prompts[0].files[0].mention, undefined);
});

test('v2 delegated child disables routing MCP and skips delegation instructions', async () => {
  process.env.HYBRID_SAGE_CHILD = 'opencode';
  try {
    const ctx = context();
    await plugin.setup(ctx);
    assert.equal(ctx.state.mcp.get('hybrid-sage').disabled, true);
    assert.equal(ctx.state.hooks.size, 0);
    assert.equal(ctx.state.commands.length, 0);
  } finally {
    delete process.env.HYBRID_SAGE_CHILD;
  }
});

test('v1 adapter preserves native registration for older clients', async () => {
  const hooks = await plugin.server();
  const config = {};
  await hooks.config(config);
  assert.ok(config.mcp['hybrid-sage'].enabled);
  assert.ok(config.command.fleet);
});

test('persisted mode and model changes apply to existing plugin hooks without restart', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sage-plugin-preferences-'));
  const previous = process.env.HYBRID_SAGE_PREFERENCES;
  process.env.HYBRID_SAGE_PREFERENCES = path.join(dir, 'preferences.json');
  try {
    const ctx = context();
    await plugin.setup(ctx);
    fs.writeFileSync(process.env.HYBRID_SAGE_PREFERENCES, JSON.stringify({ enabled: false }));
    const off = { system: [] };
    await ctx.state.hooks.get('context')(off);
    assert.ok(off.system[0].text.includes('DISABLED'));
    fs.writeFileSync(process.env.HYBRID_SAGE_PREFERENCES, JSON.stringify({ enabled: true, model_id: 'provider/chosen' }));
    const on = { system: [] };
    await ctx.state.hooks.get('context')(on);
    assert.ok(on.system[0].text.includes('provider/chosen'));
  } finally {
    if (previous === undefined) delete process.env.HYBRID_SAGE_PREFERENCES;
    else process.env.HYBRID_SAGE_PREFERENCES = previous;
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
