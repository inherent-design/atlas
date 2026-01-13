#!/usr/bin/env tsx
/**
 * atlas-project skill implementation
 *
 * Creates Atlas bootstrap file via LLM-based project detection
 *
 * Input (stdin): { conversation_history: Message[], args?: string, cwd: string }
 * Output (stdout): { success: boolean, bootstrap_path: string, project_name: string, project_path: string }
 */

import { AtlasConnection, isDaemonRunning } from '@inherent.design/atlas-core'
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs'
import { join } from 'path'
import { execSync } from 'child_process'

interface Message {
  role: string
  content: string
}

interface SkillInput {
  conversation_history: Message[]
  args?: string // Optional: "<project-name> <path>"
  cwd: string
}

/** Read stdin using Node.js streams */
async function readStdin(): Promise<string> {
  const chunks: Buffer[] = []
  for await (const chunk of process.stdin) {
    chunks.push(chunk)
  }
  return Buffer.concat(chunks).toString('utf-8')
}

async function main() {
  // Parse skill input
  let input: SkillInput
  try {
    const data = await readStdin()
    input = JSON.parse(data)
  } catch (error) {
    console.error('Error: Invalid skill input')
    process.exit(1)
  }

  // Parse args if provided
  let projectName: string | undefined
  let projectPath: string | undefined

  if (input.args) {
    const parts = input.args.trim().split(/\s+/)
    if (parts.length >= 2) {
      projectName = parts[0]
      const part1 = parts[1]
      if (!part1) throw new Error('Invalid project specification')
      projectPath = part1
    } else if (parts.length === 1) {
      // Single arg could be path or name, try to disambiguate
      const part0 = parts[0]
      if (!part0) throw new Error('Invalid project specification')
      if (part0.includes('/') || part0 === '.') {
        projectPath = part0
      } else {
        projectName = part0
      }
    }
  }

  // Default to cwd if no path specified
  if (!projectPath) {
    projectPath = input.cwd
  }

  // Resolve relative paths
  if (!projectPath.startsWith('/')) {
    projectPath = join(input.cwd, projectPath)
  }

  // Verify path exists
  if (!existsSync(projectPath)) {
    console.error(`Error: Path does not exist: ${projectPath}`)
    process.exit(1)
  }

  // Gather context
  const context: string[] = []

  // 1. Conversation history (last 10 messages for context)
  const recentMessages = input.conversation_history.slice(-10)
  context.push('## Conversation Context\n')
  context.push(recentMessages.map((m) => `**${m.role}**: ${m.content}`).join('\n\n'))

  // 2. Directory structure
  try {
    const tree = execSync(`tree -L 3 -I 'node_modules|dist|build|target|.git' "${projectPath}"`, {
      encoding: 'utf-8',
      maxBuffer: 10 * 1024 * 1024, // 10MB
    })
    context.push('\n## Directory Structure\n')
    context.push('```\n' + tree.trim() + '\n```')
  } catch {
    // Tree command not available or failed, try ls fallback
    try {
      const ls = execSync(`ls -la "${projectPath}"`, {
        encoding: 'utf-8',
      })
      context.push('\n## Directory Listing\n')
      context.push('```\n' + ls.trim() + '\n```')
    } catch {
      // Even ls failed, skip directory listing
    }
  }

  // 3. Git info
  if (existsSync(join(projectPath, '.git'))) {
    try {
      const log = execSync('git log --oneline -5', {
        cwd: projectPath,
        encoding: 'utf-8',
      })
      context.push('\n## Recent Commits\n')
      context.push('```\n' + log.trim() + '\n```')
    } catch {
      // Git failed, skip
    }
  }

  // 4. Package manifests (Node, Rust, Go, Python)
  const manifests = [
    'package.json',
    'Cargo.toml',
    'go.mod',
    'pyproject.toml',
    'requirements.txt',
    'composer.json',
    'Gemfile',
  ]

  for (const manifest of manifests) {
    const path = join(projectPath, manifest)
    if (existsSync(path)) {
      try {
        const content = readFileSync(path, 'utf-8')
        // Truncate if too large
        const truncated =
          content.length > 5000 ? content.slice(0, 5000) + '\n...(truncated)' : content
        context.push(`\n## ${manifest}\n`)
        context.push('```\n' + truncated + '\n```')
      } catch {
        // Read failed, skip
      }
    }
  }

  // 5. README if present
  const readmeFiles = ['README.md', 'README.txt', 'README']
  for (const readme of readmeFiles) {
    const path = join(projectPath, readme)
    if (existsSync(path)) {
      try {
        const content = readFileSync(path, 'utf-8')
        // Truncate README to first 2000 chars
        const truncated =
          content.length > 2000 ? content.slice(0, 2000) + '\n...(truncated)' : content
        context.push(`\n## ${readme}\n`)
        context.push('```markdown\n' + truncated + '\n```')
        break // Only include first README found
      } catch {
        // Read failed, skip
      }
    }
  }

  // Detect project type and generate bootstrap content
  let projectType = 'Unknown'
  let version = '0.0.0'
  let setupCommands: string[] = []
  let buildCommands: string[] = []
  let testCommands: string[] = []
  let runCommands: string[] = []
  let techStack: string[] = []

  // Detect from package manifests
  if (existsSync(join(projectPath, 'package.json'))) {
    try {
      const pkg = JSON.parse(readFileSync(join(projectPath, 'package.json'), 'utf-8'))
      version = pkg.version || version
      projectType = pkg.workspaces ? 'Monorepo (Node)' : 'Node.js'

      // Detect package manager
      const hasYarnLock = existsSync(join(projectPath, 'yarn.lock'))
      const hasPnpmLock = existsSync(join(projectPath, 'pnpm-lock.yaml'))
      const hasBunLock = existsSync(join(projectPath, 'bun.lockb'))

      const pkgMgr = hasBunLock ? 'bun' : hasPnpmLock ? 'pnpm' : hasYarnLock ? 'yarn' : 'npm'

      setupCommands.push(`${pkgMgr} install`)
      if (pkg.scripts?.build) buildCommands.push(`${pkgMgr} run build`)
      if (pkg.scripts?.test) testCommands.push(`${pkgMgr} test`)
      if (pkg.scripts?.dev) runCommands.push(`${pkgMgr} run dev`)
      if (pkg.scripts?.start) runCommands.push(`${pkgMgr} start`)

      if (pkg.dependencies?.react || pkg.devDependencies?.react) techStack.push('React')
      if (pkg.dependencies?.next || pkg.devDependencies?.next) techStack.push('Next.js')
      if (pkg.dependencies?.vue || pkg.devDependencies?.vue) techStack.push('Vue')
      if (pkg.dependencies?.typescript || pkg.devDependencies?.typescript)
        techStack.push('TypeScript')
    } catch {}
  }

  if (existsSync(join(projectPath, 'Cargo.toml'))) {
    projectType = 'Rust'
    setupCommands.push('cargo fetch')
    buildCommands.push('cargo build')
    testCommands.push('cargo test')
    runCommands.push('cargo run')
    techStack.push('Rust')
  }

  if (existsSync(join(projectPath, 'go.mod'))) {
    projectType = 'Go'
    setupCommands.push('go mod download')
    buildCommands.push('go build')
    testCommands.push('go test ./...')
    runCommands.push('go run .')
    techStack.push('Go')
  }

  if (
    existsSync(join(projectPath, 'pyproject.toml')) ||
    existsSync(join(projectPath, 'requirements.txt'))
  ) {
    projectType = 'Python'
    setupCommands.push('pip install -r requirements.txt')
    if (existsSync(join(projectPath, 'pyproject.toml'))) setupCommands.push('pip install -e .')
    testCommands.push('pytest')
    runCommands.push('python main.py')
    techStack.push('Python')
  }

  // Generate bootstrap content
  let bootstrapContent = `# ${projectName || projectPath.split('/').filter(Boolean).pop() || 'Project'} Bootstrap

**Version:** ${version} | **Type:** ${projectType} | **Root:** \`${projectPath}\`

## Overview

Project tracked in Atlas persistent memory for context recovery across sessions.

${context[0] ? '## Context\n\n' + context.slice(0, 2).join('\n\n') : ''}

## Entry Points

${existsSync(join(projectPath, 'src/main.ts')) ? '- `src/main.ts` - Main entrypoint' : ''}
${existsSync(join(projectPath, 'src/index.ts')) ? '- `src/index.ts` - Module entrypoint' : ''}
${existsSync(join(projectPath, 'main.py')) ? '- `main.py` - Python entrypoint' : ''}
${existsSync(join(projectPath, 'src/main.rs')) ? '- `src/main.rs` - Rust entrypoint' : ''}
${existsSync(join(projectPath, 'cmd')) ? '- `cmd/` - Go commands' : ''}

## Commands

${setupCommands.length > 0 ? '\`\`\`bash\n# Setup\n' + setupCommands.join('\n') + '\n```\n' : ''}
${buildCommands.length > 0 ? '\`\`\`bash\n# Build\n' + buildCommands.join('\n') + '\n```\n' : ''}
${testCommands.length > 0 ? '\`\`\`bash\n# Test\n' + testCommands.join('\n') + '\n```\n' : ''}
${runCommands.length > 0 ? '\`\`\`bash\n# Run\n' + runCommands.join('\n') + '\n```\n' : ''}

## Tech Stack

${techStack.length > 0 ? techStack.map((t) => `- ${t}`).join('\n') : '- See package manifest for details'}

${context.slice(2).join('\n\n')}

---

*Generated by atlas-project skill on ${new Date().toISOString().split('T')[0]}*
`

  // Infer project name from content if not provided
  if (!projectName) {
    const match = bootstrapContent.match(/^#\s+(.+?)\s+Bootstrap/m)
    if (match) {
      const matchedName = match[1]
      if (!matchedName) throw new Error('Failed to extract project name from bootstrap')
      projectName = matchedName
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^a-z0-9-]/g, '')
    } else {
      // Fallback: use directory name
      projectName = projectPath.split('/').filter(Boolean).pop() || 'untitled-project'
      projectName = projectName.toLowerCase().replace(/\s+/g, '-')
    }
  }

  // Write bootstrap file
  const bootstrapDir = join(process.env.HOME!, '.atlas', 'bootstrap')
  mkdirSync(bootstrapDir, { recursive: true })

  const bootstrapPath = join(bootstrapDir, `${projectName}.md`)
  writeFileSync(bootstrapPath, bootstrapContent, 'utf-8')

  console.log(`✓ Bootstrap created: ${bootstrapPath}`)

  // Start auto-ingestion (only if daemon is running)
  let taskId: string | undefined
  if (isDaemonRunning()) {
    try {
      const connection = new AtlasConnection()
      await connection.connect()

      const ingestResult = (await connection.request('atlas.ingest.start' as any, {
        paths: [projectPath],
        recursive: true,
        watch: true,
      })) as any

      taskId = ingestResult.taskId
      console.log(`✓ Auto-ingestion started: ${taskId}`)
      connection.disconnect()
    } catch (error) {
      console.error(`Warning: Failed to start auto-ingestion: ${error}`)
      console.error('You can manually start ingestion later with:')
      console.error(
        `  bun run --filter @inherent.design/atlas-cli atlas ingest.start "${projectPath}" -r --watch`
      )
    }
  } else {
    console.log('Note: Daemon not running. Auto-ingestion not started.')
    console.log('To enable auto-ingestion:')
    console.log('  1. Start daemon: cd ~/production/atlas/packages/core && bun run daemon')
    console.log(
      `  2. Start ingestion: bun run --filter @inherent.design/atlas-cli atlas ingest.start "${projectPath}" -r --watch`
    )
  }

  // Output for Claude Code
  const output = {
    success: true,
    bootstrap_path: bootstrapPath,
    project_name: projectName,
    project_path: projectPath,
    ingestion_task_id: taskId,
  }

  console.log('\n' + JSON.stringify(output, null, 2))
}

main()
