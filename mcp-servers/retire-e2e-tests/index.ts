#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    ErrorCode,
    ListToolsRequestSchema,
    McpError,
} from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs/promises";
import * as path from "path";

// Simple config with defaults
const config = {
    e2eRepoPath: process.env.E2E_REPO_PATH || "/tmp/e2e-tests",
    monolithRepoPath: process.env.MONOLITH_REPO_PATH || "/tmp/monolith-tests",
    e2eSubPath: process.env.E2E_SUB_PATH || "spec/features",
    monolithSubPath: process.env.MONOLITH_SUB_PATH || "spec",
    smokeTagPattern: process.env.SMOKE_TAG_PATTERN || "smoke"
};

interface TestFile {
    path: string;
    content: string;
    tags: string[];
    testType: 'e2e' | 'unit' | 'integration';
    testName: string;
    smokeTagged: boolean;
}

interface TestOverlap {
    e2eTest: TestFile;
    overlappingTests: TestFile[];
    redundancyScore: number;
    recommendation: 'remove' | 'refactor' | 'keep';
    rationale: string;
}

interface AnalysisResult {
    totalE2eTests: number;
    totalUnitTests: number;
    overlaps: TestOverlap[];
    summary: string;
    potentialTimeSavings: string;
}

class TestOverlapAnalyzer {
    private e2eTests: TestFile[] = [];
    private unitTests: TestFile[] = [];

    async analyzeProjects(): Promise<AnalysisResult> {
        console.error("🔍 Starting test overlap analysis...");
        console.error(`📁 E2E Repo: ${config.e2eRepoPath}`);
        console.error(`📁 Monolith Repo: ${config.monolithRepoPath}`);

        const e2eFullPath = path.join(config.e2eRepoPath, config.e2eSubPath);
        const monolithFullPath = path.join(config.monolithRepoPath, config.monolithSubPath);

        await this.verifyPath(e2eFullPath, 'E2E project');
        await this.verifyPath(monolithFullPath, 'Monolith project');

        await this.loadAndAnalyzeTests(e2eFullPath, 'e2e');
        await this.loadAndAnalyzeTests(monolithFullPath, 'unit');

        const overlaps = await this.findOverlaps();
        return this.generateAnalysis(overlaps);
    }

    private async verifyPath(pathToCheck: string, description: string): Promise<void> {
        try {
            await fs.access(pathToCheck);
        } catch (error) {
            throw new Error(`${description} path does not exist or is not accessible: ${pathToCheck}`);
        }
    }

    private async loadAndAnalyzeTests(projectPath: string, testType: 'e2e' | 'unit'): Promise<void> {
        const testFiles = await this.findTestFiles(projectPath);

        for (const filePath of testFiles) {
            try {
                const content = await fs.readFile(filePath, 'utf-8');
                const testFile = await this.analyzeTestFile(filePath, content, testType);

                if (testType === 'e2e' && testFile.smokeTagged) {
                    this.e2eTests.push(testFile);
                } else if (testType === 'unit') {
                    this.unitTests.push(testFile);
                }
            } catch (error) {
                console.error(`Error analyzing ${filePath}: ${error}`);
            }
        }
    }

    private async analyzeTestFile(filePath: string, content: string, baseType: 'e2e' | 'unit'): Promise<TestFile> {
        const tags = this.extractTags(content);
        const smokeTagged = this.isSmokeTagged(content);
        const testName = this.extractTestName(content, filePath);

        return {
            path: filePath,
            content,
            tags,
            testType: baseType,
            testName,
            smokeTagged
        };
    }

    private isSmokeTagged(content: string): boolean {
        const smokePatterns = [
            /:smoke\b/,
            /'smoke'/,
            /"smoke"/,
            /tag.*smoke/i,
            /smoke.*tag/i,
            /describe.*smoke/i,
            /context.*smoke/i,
            /it.*smoke/i
        ];

        return smokePatterns.some(pattern => pattern.test(content));
    }

    private extractTags(content: string): string[] {
        const tagPatterns = [
            /:(\w+)\b/g,
            /['"`](\w+)['"`]/g
        ];

        const tags = new Set<string>();
        for (const pattern of tagPatterns) {
            let match;
            while ((match = pattern.exec(content)) !== null) {
                tags.add(match[1]);
            }
        }

        return Array.from(tags);
    }

    private extractTestName(content: string, filePath: string): string {
        const describeMatch = content.match(/describe\s+['"`]([^'"`]+)['"`]/);
        const itMatch = content.match(/it\s+['"`]([^'"`]+)['"`]/);
        const contextMatch = content.match(/context\s+['"`]([^'"`]+)['"`]/);

        return describeMatch?.[1] || itMatch?.[1] || contextMatch?.[1] || path.basename(filePath);
    }

    private async findTestFiles(projectPath: string): Promise<string[]> {
        const testFiles: string[] = [];

        const scanDirectory = async (dir: string): Promise<void> => {
            try {
                const entries = await fs.readdir(dir, { withFileTypes: true });

                for (const entry of entries) {
                    const fullPath = path.join(dir, entry.name);

                    if (entry.isDirectory()) {
                        if (!this.shouldSkipDirectory(entry.name)) {
                            await scanDirectory(fullPath);
                        }
                    } else if (this.isTestFile(entry.name)) {
                        testFiles.push(fullPath);
                    }
                }
            } catch (error) {
                console.error(`Error scanning directory ${dir}: ${error}`);
            }
        };

        await scanDirectory(projectPath);
        return testFiles;
    }

    private shouldSkipDirectory(dirName: string): boolean {
        return ['node_modules', '.git', 'tmp', 'log', 'coverage'].includes(dirName);
    }

    private isTestFile(filename: string): boolean {
        return filename.endsWith('.rb') && filename.includes('_spec.rb');
    }

    private async findOverlaps(): Promise<TestOverlap[]> {
        const overlaps: TestOverlap[] = [];

        for (const e2eTest of this.e2eTests) {
            const overlappingTests: TestFile[] = [];

            for (const unitTest of this.unitTests) {
                if (this.testsOverlap(e2eTest, unitTest)) {
                    overlappingTests.push(unitTest);
                }
            }

            if (overlappingTests.length > 0) {
                const redundancyScore = this.calculateRedundancyScore(e2eTest, overlappingTests);
                const recommendation = this.generateRecommendation(redundancyScore);

                overlaps.push({
                    e2eTest,
                    overlappingTests,
                    redundancyScore,
                    recommendation: recommendation.action,
                    rationale: recommendation.rationale
                });
            }
        }

        return overlaps;
    }

    private testsOverlap(e2eTest: TestFile, unitTest: TestFile): boolean {
        // Extract what the E2E test is actually testing
        const e2eTestTargets = this.extractE2ETestTargets(e2eTest.content);
        const unitTestTargets = this.extractUnitTestTargets(unitTest.content);

        // Check for overlaps in what they're testing
        return this.hasOverlappingTargets(e2eTestTargets, unitTestTargets);
    }

    private extractE2ETestTargets(content: string): {
        endpoints: string[];
        businessLogic: string[];
        models: string[];
        services: string[];
    } {
        const targets = {
            endpoints: [] as string[],
            businessLogic: [] as string[],
            models: [] as string[],
            services: [] as string[]
        };

        // Extract API endpoints being tested
        const endpointMatches = content.match(/create_candidate_order_report|wait_for_report_status|get_internal_provider_requests|get_internal_response_with_bearer_token/g);
        if (endpointMatches) {
            targets.endpoints.push(...endpointMatches);
        }

        // Extract business logic being tested
        const businessLogicPatterns = [
            /state.*criminal.*search/i,
            /county.*criminal.*search/i,
            /fallback.*search/i,
            /screening.*result/i,
            /provider.*request/i,
            /consider.*clear/i
        ];

        businessLogicPatterns.forEach(pattern => {
            if (pattern.test(content)) {
                targets.businessLogic.push(pattern.source);
            }
        });

        // Extract models/services from API calls and expectations
        const modelPatterns = [
            /candidate/i,
            /report/i,
            /search/i,
            /record/i,
            /provider/i
        ];

        modelPatterns.forEach(pattern => {
            if (pattern.test(content)) {
                targets.models.push(pattern.source);
            }
        });

        return targets;
    }

    private extractUnitTestTargets(content: string): {
        models: string[];
        services: string[];
        methods: string[];
        businessLogic: string[];
    } {
        const targets = {
            models: [] as string[],
            services: [] as string[],
            methods: [] as string[],
            businessLogic: [] as string[]
        };

        // Extract model names being tested
        const modelMatches = content.match(/describe\s+['"`]([^'"`]+)['"`]/g);
        if (modelMatches) {
            targets.models.push(...modelMatches.map(m => m.replace(/describe\s+['"`]|['"`]/g, '')));
        }

        // Extract service names
        const serviceMatches = content.match(/Service|Controller|Helper/g);
        if (serviceMatches) {
            targets.services.push(...serviceMatches);
        }

        // Extract method names
        const methodMatches = content.match(/it\s+['"`]([^'"`]+)['"`]/g);
        if (methodMatches) {
            targets.methods.push(...methodMatches.map(m => m.replace(/it\s+['"`]|['"`]/g, '')));
        }

        // Extract business logic being tested
        const businessLogicPatterns = [
            /criminal.*search/i,
            /screening/i,
            /fallback/i,
            /provider/i,
            /record/i,
            /consider/i,
            /clear/i
        ];

        businessLogicPatterns.forEach(pattern => {
            if (pattern.test(content)) {
                targets.businessLogic.push(pattern.source);
            }
        });

        return targets;
    }

    private hasOverlappingTargets(e2eTargets: any, unitTargets: any): boolean {
        // Check for overlapping business logic
        const e2eBusinessLogic = e2eTargets.businessLogic.map((bl: string) => bl.toLowerCase());
        const unitBusinessLogic = unitTargets.businessLogic.map((bl: string) => bl.toLowerCase());

        const businessLogicOverlap = e2eBusinessLogic.some(e2eBl =>
            unitBusinessLogic.some(unitBl =>
                e2eBl.includes(unitBl) || unitBl.includes(e2eBl)
            )
        );

        // Check for overlapping models
        const e2eModels = e2eTargets.models.map((m: string) => m.toLowerCase());
        const unitModels = unitTargets.models.map((m: string) => m.toLowerCase());

        const modelOverlap = e2eModels.some(e2eModel =>
            unitModels.some(unitModel =>
                e2eModel.includes(unitModel) || unitModel.includes(e2eModel)
            )
        );

        // Check for overlapping services
        const e2eServices = e2eTargets.services.map((s: string) => s.toLowerCase());
        const unitServices = unitTargets.services.map((s: string) => s.toLowerCase());

        const serviceOverlap = e2eServices.some(e2eService =>
            unitServices.some(unitService =>
                e2eService.includes(unitService) || unitService.includes(e2eService)
            )
        );

        return businessLogicOverlap || modelOverlap || serviceOverlap;
    }

    private calculateRedundancyScore(e2eTest: TestFile, overlappingTests: TestFile[]): number {
        // Simple scoring based on number of overlaps and test complexity
        let score = overlappingTests.length * 20;

        if (e2eTest.content.length > 1000) score += 10;
        if (overlappingTests.length > 3) score += 20;

        return Math.min(score, 100);
    }

    private generateRecommendation(score: number): { action: 'remove' | 'refactor' | 'keep', rationale: string } {
        if (score >= 70) {
            return { action: 'remove', rationale: 'High redundancy score indicates significant overlap' };
        } else if (score >= 40) {
            return { action: 'refactor', rationale: 'Medium redundancy score suggests potential for consolidation' };
        } else {
            return { action: 'keep', rationale: 'Low redundancy score, test appears to be unique' };
        }
    }

    private generateAnalysis(overlaps: TestOverlap[]): AnalysisResult {
        const highRedundancy = overlaps.filter(o => o.redundancyScore >= 70);
        const mediumRedundancy = overlaps.filter(o => o.redundancyScore >= 40 && o.redundancyScore < 70);

        const summary = `Found ${this.e2eTests.length} smoke-tagged E2E tests and ${this.unitTests.length} unit tests. 
    Identified ${overlaps.length} overlaps: ${highRedundancy.length} high redundancy, ${mediumRedundancy.length} medium redundancy.`;

        const timeSavings = this.calculateTimeSavings(overlaps);

        return {
            totalE2eTests: this.e2eTests.length,
            totalUnitTests: this.unitTests.length,
            overlaps,
            summary,
            potentialTimeSavings: timeSavings
        };
    }

    private calculateTimeSavings(overlaps: TestOverlap[]): string {
        const removableTests = overlaps.filter(o => o.recommendation === 'remove');
        const estimatedMinutes = removableTests.length * 5; // 5 minutes per test

        if (estimatedMinutes === 0) return "No significant time savings identified";
        return `Estimated ${estimatedMinutes} minutes saved by removing ${removableTests.length} redundant tests`;
    }
}

const server = new Server(
    {
        name: "test-overlap-analyzer",
        version: "1.0.0",
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: "analyze_test_overlap",
                description: "Analyze overlap between smoke-tagged E2E tests and unit tests using environment variables",
                inputSchema: {
                    type: "object",
                    properties: {}
                }
            },
            {
                name: "show_config",
                description: "Show current configuration",
                inputSchema: {
                    type: "object",
                    properties: {}
                }
            }
        ],
    };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    switch (name) {
        case "analyze_test_overlap": {
            try {
                const analyzer = new TestOverlapAnalyzer();
                const result = await analyzer.analyzeProjects();

                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify(result, null, 2)
                        }
                    ]
                };
            } catch (error) {
                throw new McpError(ErrorCode.InternalError, `Analysis failed: ${error}`);
            }
        }

        case "show_config": {
            try {
                return {
                    content: [
                        {
                            type: "text",
                            text: JSON.stringify({
                                message: "Current configuration:",
                                config: config,
                                environment_variables: {
                                    E2E_REPO_PATH: "Path to E2E test repository",
                                    MONOLITH_REPO_PATH: "Path to monolith repository",
                                    E2E_SUB_PATH: "Subdirectory in E2E repo (default: spec/features)",
                                    MONOLITH_SUB_PATH: "Subdirectory in monolith repo (default: spec)",
                                    SMOKE_TAG_PATTERN: "Pattern to identify smoke tests (default: smoke)"
                                }
                            }, null, 2)
                        }
                    ]
                };
            } catch (error) {
                throw new McpError(ErrorCode.InternalError, `Failed to show config: ${error}`);
            }
        }

        default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }
});

async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("🚀 Test Overlap Analyzer MCP Server started");
}

main().catch(console.error); 