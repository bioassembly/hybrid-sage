// hybrid-sage.mjs — OpenCode Plugin.
//
// Injects the Hybrid SAGE fleet orchestration protocol into system prompts,
// registers the hybrid-sage MCP server (exposing fleet_status, route_task,
// delegate_local, manage_handoff, airgap_scan, and escalate_task tools),
// and mounts the model-router skill.

import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../..');
const mcpServerScript = path.join(repoRoot, 'plugins', 'mcp_server.py');

export default async ({ client } = {}) => {
  const skillsDir = path.join(repoRoot, 'skills');

  return {
    config: async (config) => {
      // 1. Expose the model-router skill directory
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(skillsDir)) {
        config.skills.paths.push(skillsDir);
      }

      // 2. Register hybrid-sage MCP server natively
      config.mcp = config.mcp || {};
      config.mcp['hybrid-sage'] = {
        type: 'local',
        command: ['python3', mcpServerScript],
        enabled: true,
      };

      // 3. Register chat slash commands (/fleet, /route, /escalate)
      if (!config.command) config.command = {};
      config.command['fleet'] = {
        description: 'Show live Hybrid SAGE fleet, OpenCode runtime, and bridge telemetry',
        template: 'Check fleet status using the `fleet_status` tool and report active units, OpenCode runtime state, and ROI token savings.',
      };
      config.command['route'] = {
        description: 'Classify and route a task across your configured fleet',
        template: 'Classify the following task using `route_task`: $ARGUMENTS',
      };
      config.command['escalate'] = {
        description: 'Escalate a hard bug, race condition, or architecture bottleneck to Gemini 4 Argon via escalate_task',
        template: 'Call `escalate_task(prompt="$ARGUMENTS")` to obtain root-cause diagnosis and invariants from the frontier architect, then implement and verify the fix locally.',
      };
    },

    // Inject the Hybrid SAGE routing protocol & project-scoped lessons into system prompts
    'experimental.chat.system.transform': async (_input, output) => {
      const instructions = `
[HYBRID SAGE WORKHORSE PROTOCOL (v2.0)]
You are running inside OpenCode as the primary local/workhorse coding harness ($0 cloud frontier quota).

CORE OPERATIONAL RULES:
1. **Direct Execution (Never Delegate to Yourself)**:
   - Execute code editing, bash commands, file reading, and test verification DIRECTLY using OpenCode native tools (\`edit\`, \`bash\`, \`read\`).
   - NEVER call \`delegate_local\` on your own tasks — \`delegate_local\` is exclusively for upstream cloud sessions offloading work into OpenCode.
2. **Proactive Upfront Classification**:
   - For ambiguous greenfield architecture, multi-file structural design, or complex algorithmic trade-offs, call \`route_task(prompt="...")\` upfront.
   - If \`route_task\` classifies the task as \`frontier-architect\` or \`cloud-sprinter\` (and \`agy\` is installed), invoke \`escalate_task\` to obtain read-only architectural diagnosis and invariants before writing code.
   - Execute routine coding, bug fixes, TDD loops, and refactoring directly without upfront escalation.
3. **Autonomous 2-Strike Escalation**:
   - If you attempt to fix a bug or failing test twice and verification still fails, or when the user invokes \`/escalate\`, call:
     \`escalate_task(prompt="<symptom & context>", files=["..."], attempted=["attempt 1", "attempt 2"], failing_command="...", failing_output="...")\`
   - \`escalate_task\` runs pre-flight airgap sanitization, consults Gemini in read-only \`--mode plan\`, records reusable lessons to \`lessons.jsonl\`, and writes invariants to \`NOTES.md\`.
   - Once the diagnosis returns, immediately implement and verify the solution locally.
4. **Native MCP Tools**:
   - \`route_task\`: Multi-axis capability classifier + airgap scan + matching project lessons.
   - \`escalate_task\`: Read-only frontier escalation via \`agy --mode plan\` with automatic lesson distillation.
   - \`airgap_scan\`: Pre-flight PII/PHI/Secret firewall and redactor (\`redact=true\`).
   - \`fleet_status\`: OpenCode runtime health, \`agy\` CLI status, shared memory graph, and ROI ledger.
   - \`manage_handoff\`: Structured \`NOTES.md\` plan/review state and episodic \`lessons.jsonl\` management.
`;

      // Read project-scoped lessons from flock-protected ~/.config/opencode/lessons.jsonl
      let lessonsSection = '';
      try {
        const lessonsFile = path.join(os.homedir(), '.config', 'opencode', 'lessons.jsonl');
        if (fs.existsSync(lessonsFile)) {
          const raw = fs.readFileSync(lessonsFile, 'utf8');
          const lines = raw.trim().split('\n').filter(Boolean);
          const cwd = process.cwd();
          const matched = [];
          for (let i = lines.length - 1; i >= 0; i--) {
            try {
              const rec = JSON.parse(lines[i]);
              if (rec.repo_path && (cwd === rec.repo_path || cwd.startsWith(rec.repo_path + path.sep) || rec.repo_path.startsWith(cwd + path.sep))) {
                matched.push(rec);
                if (matched.length >= 8) break;
              }
            } catch (e) {}
          }
          if (matched.length > 0) {
            const lessonLines = matched.map((m) => {
              const sig = m.error_signature || m.symptom || 'Invariant';
              const root = m.root_cause_summary || '';
              return `- [${sig.slice(0, 80)}]: ${root.slice(0, 180)}`;
            });
            const joined = lessonLines.join('\n');
            const capped = joined.length > 1600 ? joined.slice(0, 1600) + '...' : joined;
            lessonsSection = `\n\n[PROJECT-SCOPED FRONTIER LESSONS]\nPrior architectural lessons and pitfalls for this repository:\n${capped}`;
          }
        }
      } catch (e) {}

      const fullPrompt = (instructions.trim() + lessonsSection).trim();
      output.system = Array.isArray(output.system) ? output.system : [];
      if (output.system.length > 0) {
        output.system[output.system.length - 1] += '\n\n' + fullPrompt;
      } else {
        output.system.push(fullPrompt);
      }
    },
  };
};
