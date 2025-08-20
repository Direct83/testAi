import { Octokit } from "@octokit/rest";

type JsonSchema = Record<string, unknown>;
export type McpTool = {
    name: string;
    description: string;
    inputSchema: JsonSchema;
    handler: (args: any) => Promise<any>;
};

const requireEnv = (key: string) => {
    const v = process.env[key];
    if (!v) throw new Error(`Missing env: ${key}`);
    return v;
};

const octokit = new Octokit({ auth: requireEnv("GITHUB_TOKEN") });

async function getDefaultBranch(owner: string, repo: string) {
    const { data } = await octokit.repos.get({ owner, repo });
    return data.default_branch || "main";
}

export const tools: McpTool[] = [
    {
        name: "createBranch",
        description: "Создать ветку от base ветки",
        inputSchema: {
            type: "object",
            properties: { owner: { type: "string" }, repo: { type: "string" }, branch: { type: "string" }, from_branch: { type: "string" } },
            required: ["owner", "repo", "branch"]
        },
        handler: async ({ owner, repo, branch, from_branch }) => {
            const base = from_branch || (await getDefaultBranch(owner, repo));
            const ref = await octokit.git.getRef({ owner, repo, ref: `heads/${base}` });
            try {
                await octokit.git.createRef({ owner, repo, ref: `refs/heads/${branch}`, sha: ref.data.object.sha });
                return { ok: true, created: true };
            } catch (e: any) {
                if (e?.status === 422) return { ok: true, existing: true };
                throw e;
            }
        }
    },
    {
        name: "createOrUpdateFile",
        description: "Создать/обновить файл в ветке",
        inputSchema: {
            type: "object",
            properties: {
                owner: { type: "string" }, repo: { type: "string" }, path: { type: "string" }, content: { type: "string" }, message: { type: "string" }, branch: { type: "string" }
            },
            required: ["owner", "repo", "path", "content", "message", "branch"]
        },
        handler: async ({ owner, repo, path, content, message, branch }) => {
            let sha: string | undefined;
            try {
                const current = await octokit.repos.getContent({ owner, repo, path, ref: branch });
                if (!Array.isArray(current.data) && (current.data as any).sha) sha = (current.data as any).sha;
            } catch (_) { }
            const res = await octokit.repos.createOrUpdateFileContents({
                owner, repo, path, message, content: Buffer.from(content, "utf8").toString("base64"), branch, sha
            });
            return { path: res.data.content?.path, commit: res.data.commit.sha, url: res.data.content?.html_url };
        }
    },
    {
        name: "createPullRequest",
        description: "Создать Pull Request",
        inputSchema: {
            type: "object",
            properties: { owner: { type: "string" }, repo: { type: "string" }, title: { type: "string" }, body: { type: "string" }, head: { type: "string" }, base: { type: "string" }, draft: { type: "boolean" } },
            required: ["owner", "repo", "title", "head", "base"]
        },
        handler: async ({ owner, repo, title, body, head, base, draft = false }) => {
            const res = await octokit.pulls.create({ owner, repo, title, body, head, base, draft });
            return { number: res.data.number, url: res.data.html_url };
        }
    }
];

export function registerGithubTools(server: { addTool: (t: McpTool) => void }) {
    for (const t of tools) server.addTool(t);
}


