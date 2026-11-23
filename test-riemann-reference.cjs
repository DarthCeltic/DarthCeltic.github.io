const { test } = require('node:test');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');
const path = require('node:path');
const { pins, checkFile } = require(process.argv[2] && !process.argv[2].startsWith('-') ? path.resolve(process.argv[2]) : './riemann-reference.js');

test('exact length and content determine the result', async () => {
  const bytes = 'example-content';
  const pin = {path: 'test', size: bytes.length, hash: createHash('sha256').update(bytes).digest('hex')};
  const input = value => async () => new Response(value);
  assert.equal(await checkFile(pin,input(bytes)), 'matched');
  assert.equal(await checkFile(pin,input('example-contest')), 'different');
  assert.equal(await checkFile(pin,input(bytes.slice(1))), 'different');
  assert.equal(await checkFile(pin,input(bytes + 'x')), 'different');
  assert.equal(await checkFile(pin,async () => new Response(null,{status:503})), 'unavailable');
  assert.equal(await checkFile(pin,async () => { throw Error('offline'); }), 'unavailable');
});
test('all pinned references are immutable and small', () => {
  assert.equal(pins.length, 4);
  assert.equal(pins.reduce((sum,pin) => sum+pin.size, 0), 14421);
  for (const pin of pins) {
    assert.match(pin.path,/^(mathlib4|riemann-hypothesis)\/[\da-f]{40}\//);
    assert.match(pin.hash,/^[\da-f]{64}$/);
  }
});
