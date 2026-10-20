import test from 'node:test';
import assert from 'node:assert/strict';
import { selectCharacterReference } from './character-reference.ts';
const approved = { projectId: 'sekret-bip', characterId: 'suhana', assetId: 'asset-001', assetVersion: 'v1', consentScope: 'fictional-character' as const, approvedFor: ['image'] as const };
const request = { projectId:'sekret-bip', characterId:'suhana', output:'image' as const };
test('unique approved character reference selected',()=>assert.deepEqual(selectCharacterReference([approved],request), approved));
test('cross-project, wrong output and duplicates rejected',()=>{
 assert.equal(selectCharacterReference([approved], {...request, projectId:'other'}),null);
 assert.equal(selectCharacterReference([approved], {...request,output:'video'}),null);
 assert.equal(selectCharacterReference([approved,approved],request),null);
});
test('malformed or blank metadata fails closed',()=>{
 for(const ref of [{...approved,assetId:' '},{...approved,assetVersion:' '},{...approved,approvedFor:null},{...approved,consentScope:'unknown'}])
  assert.equal(selectCharacterReference([ref as any],request),null);
 assert.equal(selectCharacterReference([],{...request,characterId:' '}),null);
});
test('adult likeness requires consent evidence reference, not merely a scope flag',()=>{
 const likeness={...approved,consentScope:'authorized-adult-likeness' as const};
 assert.equal(selectCharacterReference([likeness],request),null);
 assert.equal(selectCharacterReference([{...likeness,consentEvidenceId:'  '}],request),null);
 const ref={...likeness,consentEvidenceId:'consent-receipt-123'};
 assert.deepEqual(selectCharacterReference([ref],request),ref);
});
