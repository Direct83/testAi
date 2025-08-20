import "dotenv/config";
import express, { Request, Response } from "express";
import bodyParser from "body-parser";
import { tools as githubTools, McpTool } from "./tools/github.js";

const app = express();
app.use(bodyParser.json({ limit: "2mb" }));

const registry: Record<string, McpTool> = {};
for (const t of githubTools) registry[t.name] = t;

app.get("/capabilities", (_req: Request, res: Response) => {
    res.json({ name: "mcp-github", tools: Object.keys(registry) });
});

app.get("/tools/list", (_req: Request, res: Response) => {
    const tools = Object.values(registry).map(t => ({ name: t.name, description: t.description, inputSchema: t.inputSchema }));
    res.json({ name: "mcp-github", tools });
});

app.post("/tools/call", async (req: Request, res: Response) => {
    try {
        const name = req.body?.name;
        const args = req.body?.arguments || {};
        if (!name || !registry[name]) return res.status(400).json({ error: `Unknown tool: ${name}` });
        const result = await registry[name].handler(args);
        res.json(result);
    } catch (e: any) {
        res.status(e?.status || 500).send(e?.message || "Internal error");
    }
});

const PORT = Number(process.env.PORT || 8080);
app.listen(PORT, () => {
    console.log(`MCP GitHub server listening on http://0.0.0.0:${PORT}`);
});


