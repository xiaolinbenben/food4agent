import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test, type TestContext } from "node:test";
import { readSkillCatalog } from "./read-skill-catalog.ts";

function fixture(t: TestContext, categories: unknown) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "food4agent-catalog-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  for (const name of ["beta", "alpha"]) {
    const directory = path.join(root, "skills", name);
    fs.mkdirSync(directory, { recursive: true });
    fs.writeFileSync(path.join(directory, "SKILL.md"), `---\nname: ${name}\ndescription: ${name} summary\n---\n`);
  }
  fs.writeFileSync(path.join(root, "skills/categories.json"), JSON.stringify(categories));
  return root;
}

test("exports sorted skills with one category each and only nonempty category metadata", (t) => {
  const root = fixture(t, [
    { id: "writing", label: "内容写作", skills: ["beta"] },
    { id: "empty", label: "空分类", skills: [] },
    { id: "development", label: "软件开发", skills: ["alpha"] },
  ]);
  assert.deepEqual(readSkillCatalog(root), {
    skills: [
      { name: "alpha", summary: "alpha summary", categoryId: "development" },
      { name: "beta", summary: "beta summary", categoryId: "writing" },
    ],
    categories: [{ id: "writing", label: "内容写作" }, { id: "development", label: "软件开发" }],
  });
});

test("rejects missing assignments and lists every missing skill", (t) => {
  assert.throws(() => readSkillCatalog(fixture(t, [])), /缺少归类: alpha\n缺少归类: beta/);
});

test("rejects a skill assigned to multiple categories", (t) => {
  const root = fixture(t, [
    { id: "writing", label: "内容写作", skills: ["alpha", "beta"] },
    { id: "development", label: "软件开发", skills: ["alpha"] },
  ]);
  assert.throws(() => readSkillCatalog(root), /重复归类: alpha \(writing, development\)/);
});

test("rejects duplicate skill names within the same category", (t) => {
  const root = fixture(t, [{ id: "writing", label: "内容写作", skills: ["alpha", "alpha", "beta"] }]);
  assert.throws(() => readSkillCatalog(root), /重复归类: alpha/);
});

test("rejects stale names after a skill is removed or renamed", (t) => {
  const root = fixture(t, [{ id: "writing", label: "内容写作", skills: ["alpha", "beta", "old-name"] }]);
  assert.throws(() => readSkillCatalog(root), /引用不存在的技能: old-name \(writing\)/);
});

test("rejects duplicate category ids even when their skills do not overlap", (t) => {
  const root = fixture(t, [
    { id: "writing", label: "内容写作", skills: ["alpha"] },
    { id: "writing", label: "重复分类", skills: ["beta"] },
  ]);
  assert.throws(() => readSkillCatalog(root), /分类标识重复: writing/);
});

test("reports independent classification errors together", (t) => {
  const root = fixture(t, [{ id: "writing", label: "内容写作", skills: ["alpha", "alpha", "removed"] }]);
  assert.throws(() => readSkillCatalog(root), (error: Error) => {
    assert.match(error.message, /重复归类: alpha/);
    assert.match(error.message, /引用不存在的技能: removed/);
    assert.match(error.message, /缺少归类: beta/);
    return true;
  });
});

test("rejects malformed category records", (t) => {
  for (const categories of [
    {},
    [null],
    [{ id: "Writing", label: "内容写作", skills: [] }],
    [{ id: "writing", label: " ", skills: [] }],
    [{ id: "writing", label: "内容写作", skills: "alpha" }],
    [{ id: "writing", label: "内容写作", skills: [42] }],
  ]) {
    assert.throws(() => readSkillCatalog(fixture(t, categories)), /skills\/categories.json/);
  }
});

test("the repository catalog covers every skill directory exactly once", () => {
  const root = path.resolve(import.meta.dirname, "../..");
  const { skills, categories } = readSkillCatalog(root);
  const directoryCount = fs.readdirSync(path.join(root, "skills"), { withFileTypes: true }).filter((entry) => entry.isDirectory()).length;
  assert.equal(skills.length, directoryCount);
  assert.equal(new Set(skills.map((skill) => skill.name)).size, directoryCount);
  const ids = new Set(categories.map((category) => category.id));
  assert.ok(skills.every((skill) => ids.has(skill.categoryId)));
  assert.equal(categories.reduce((total, category) => total + skills.filter((skill) => skill.categoryId === category.id).length, 0), directoryCount);
});
