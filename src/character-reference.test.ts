import test from "node:test";
import assert from "node:assert/strict";
import { selectCharacterReference } from "./character-reference.ts";

const approved = {
  projectId: "sekret-bip",
  characterId: "suhana",
  assetId: "asset-001",
  assetVersion: "v1",
  consentScope: "fictional-character" as const,
  approvedFor: ["image"] as const,
};

test("selects the single approved character reference", () => {
  assert.deepEqual(selectCharacterReference([approved], {
    projectId: "sekret-bip", characterId: "suhana", output: "image",
  }), approved);
});

test("rejects cross-project requests", () => {
  assert.equal(selectCharacterReference([approved], {
    projectId: "other", characterId: "suhana", output: "image",
  }), null);
});

test("rejects unapproved output", () => {
  assert.equal(selectCharacterReference([approved], {
    projectId: "sekret-bip", characterId: "suhana", output: "video",
  }), null);
});

test("rejects ambiguous matches", () => {
  assert.equal(selectCharacterReference([approved, approved], {
    projectId: "sekret-bip", characterId: "suhana", output: "image",
  }), null);
});

test("rejects missing asset metadata", () => {
  assert.equal(selectCharacterReference([{ ...approved, assetId: " " }], {
    projectId: "sekret-bip", characterId: "suhana", output: "image",
  }), null);
});
