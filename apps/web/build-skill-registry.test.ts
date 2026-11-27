import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { buildSkillRegistry, readRegistryAsset } from "./build-skill-registry.ts";

test("publishes tracked skill files with a content version", (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "food4agent-registry-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const skillDir = path.join(root, "skills/alpha");
  fs.mkdirSync(path.join(skillDir, "scripts"), { recursive: true });
  fs.writeFileSync(path.join(skillDir, "SKILL.md"), "---\nname: alpha\ndescription: a\n---\n");
  fs.writeFileSync(path.join(skillDir, "scripts/run.py"), "print(1)\n");
  fs.writeFileSync(path.join(skillDir, ".gitignore"), "tmp\n");
  fs.writeFileSync(path.join(skillDir, "untracked.txt"), "x");
  const git = (...args: string[]) => execFileSync("git", args, { cwd: root, stdio: "ignore" });
  git("init", "-q");
  git("add", "skills/alpha/SKILL.md", "skills/alpha/scripts/run.py", "skills/alpha/.gitignore");
  git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init");

  const out = path.join(root, "dist");
  const catalog = { skills: [{ name: "alpha", summary: "a", categoryId: "dev" }], categories: [{ id: "dev", label: "开发" }] };
  buildSkillRegistry(root, out, catalog);

  const manifest = JSON.parse(fs.readFileSync(path.join(out, "registry/skills/alpha/manifest.json"), "utf8"));
  assert.deepEqual(manifest.files.map((file: { path: string }) => file.path), ["SKILL.md", "scripts/run.py"]);
  assert.equal(fs.readFileSync(path.join(out, "registry/skills/alpha/scripts/run.py"), "utf8"), "print(1)\n");
  const served = readRegistryAsset(root, "/registry/skills/alpha/manifest.json");
  assert.equal(JSON.parse(served?.body.toString() ?? "{}").version, manifest.version);
  assert.equal(readRegistryAsset(root, "/registry/skills/alpha/scripts/run.py")?.body.toString(), "print(1)\n");
  assert.equal(readRegistryAsset(root, "/registry/skills/alpha/.gitignore"), null);
  assert.equal(readRegistryAsset(root, "/registry/skills/alpha/../alpha/SKILL.md"), null);
  assert.equal(fs.existsSync(path.join(out, "registry/skills/alpha/.gitignore")), false);

  const index = JSON.parse(fs.readFileSync(path.join(out, "registry/skills.json"), "utf8"));
  assert.equal(index.skills[0].version, manifest.version);
  assert.equal(index.skills[0].file_count, 2);
  assert.match(index.skills[0].updated_at, /^\d{4}-/);
  assert.match(index.skills[0].digest, /^sha256:[a-f0-9]{64}$/);
  const discovery = JSON.parse(fs.readFileSync(path.join(out, "skills/alpha/.well-known/agent-skills/index.json"), "utf8"));
  assert.equal(discovery.skills[0].digest, index.skills[0].digest);
  assert.equal(discovery.skills[0].url, "/.well-known/agent-skills/alpha.zip");
  const site = JSON.parse(fs.readFileSync(path.join(out, ".well-known/agent-skills/index.json"), "utf8"));
  assert.equal(site.skills.length, 1);
  const archive = fs.readFileSync(path.join(out, ".well-known/agent-skills/alpha.zip"));
  assert.equal(archive.subarray(0, 2).toString("utf8"), "PK");
  assert.ok(archive.includes(Buffer.from("print(1)\n")));

  fs.writeFileSync(path.join(skillDir, "scripts/run.py"), "print(2)\n");
  git("add", "skills/alpha/scripts/run.py");
  buildSkillRegistry(root, out, catalog);
  const next = JSON.parse(fs.readFileSync(path.join(out, "registry/skills/alpha/manifest.json"), "utf8"));
  assert.notEqual(next.version, manifest.version);
});
