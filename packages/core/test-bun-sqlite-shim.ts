/**
 * Mock shim for bun:sqlite in Vitest environment
 * Pure in-memory mock - no real SQLite, just interface compatibility
 *
 * For unit tests: tests logic, not DB operations
 */

export interface DatabaseOptions {
  readonly?: boolean
  create?: boolean
  strict?: boolean
  safeIntegers?: boolean
}

// In-memory storage for mock data
type Row = Record<string, unknown>
type Table = Row[]
type MockStore = Map<string, Table>

/**
 * Statement mock - tracks SQL and returns mock data
 */
class Statement<T = unknown> {
  readonly source: string
  private store: MockStore
  private lastResult: { lastInsertRowid: number; changes: number } = {
    lastInsertRowid: 0,
    changes: 0,
  }

  constructor(sql: string, store: MockStore) {
    this.source = sql
    this.store = store
  }

  /**
   * Run query and return all results
   */
  all(..._params: unknown[]): T[] {
    // For SELECT COUNT(*), return mock count
    if (this.source.includes('COUNT(*)')) {
      const table = this.extractTableName()
      const rows = this.store.get(table) || []
      return [{ count: rows.length } as T]
    }

    // For other SELECTs, return stored rows
    if (this.source.trim().toUpperCase().startsWith('SELECT')) {
      const table = this.extractTableName()
      return (this.store.get(table) || []) as T[]
    }

    return []
  }

  /**
   * Run query and return first result
   */
  get(..._params: unknown[]): T | undefined {
    const results = this.all(..._params)
    return results[0]
  }

  /**
   * Run query and return execution metadata
   */
  run(...params: unknown[]): { lastInsertRowid: number | bigint; changes: number } {
    const sql = this.source.trim().toUpperCase()

    if (sql.startsWith('INSERT')) {
      const table = this.extractTableName()
      const rows = this.store.get(table) || []

      // Create a mock row from params
      const row: Row = {}
      if (params.length > 0) {
        // Simple: just store params as indexed values
        params.forEach((p, i) => {
          row[`col${i}`] = p
        })
      }
      rows.push(row)
      this.store.set(table, rows)

      this.lastResult = { lastInsertRowid: rows.length, changes: 1 }
    } else if (sql.startsWith('UPDATE')) {
      this.lastResult = { lastInsertRowid: 0, changes: 1 }
    } else if (sql.startsWith('DELETE')) {
      const table = this.extractTableName()
      const before = (this.store.get(table) || []).length
      this.store.set(table, [])
      this.lastResult = { lastInsertRowid: 0, changes: before }
    } else {
      this.lastResult = { lastInsertRowid: 0, changes: 0 }
    }

    return this.lastResult
  }

  /**
   * Run query and return all results as arrays
   */
  values(...params: unknown[]): unknown[][] {
    const rows = this.all(...params)
    return rows.map((row) => Object.values(row as object))
  }

  /**
   * Iterate over results
   */
  *iterate(...params: unknown[]): IterableIterator<T> {
    for (const row of this.all(...params)) {
      yield row
    }
  }

  /**
   * Finalize statement (no-op in mock)
   */
  finalize(): void {}

  /**
   * Get SQL source
   */
  toString(): string {
    return this.source
  }

  /**
   * Extract table name from SQL (simple pattern matching)
   */
  private extractTableName(): string {
    const sql = this.source.toUpperCase()

    // FROM table_name
    let match = sql.match(/FROM\s+(\w+)/i)
    if (match?.[1]) return match[1].toLowerCase()

    // INTO table_name
    match = sql.match(/INTO\s+(\w+)/i)
    if (match?.[1]) return match[1].toLowerCase()

    // UPDATE table_name
    match = sql.match(/UPDATE\s+(\w+)/i)
    if (match?.[1]) return match[1].toLowerCase()

    // DELETE FROM table_name
    match = sql.match(/DELETE\s+FROM\s+(\w+)/i)
    if (match?.[1]) return match[1].toLowerCase()

    return '_default'
  }

  [Symbol.iterator](...params: unknown[]): IterableIterator<T> {
    return this.iterate(...params)
  }
}

/**
 * Database mock - in-memory store with bun:sqlite interface
 */
export class Database {
  private store: MockStore = new Map()
  private statementCache: Map<string, Statement> = new Map()
  private _open: boolean = true
  private _inTransaction: boolean = false
  readonly filename: string

  constructor(filename?: string, _options: DatabaseOptions = {}) {
    this.filename = filename === '' || filename === undefined ? ':memory:' : filename
  }

  /**
   * Prepare and cache a statement
   */
  query<T = unknown>(sql: string): Statement<T> {
    let cached = this.statementCache.get(sql)
    if (!cached) {
      cached = new Statement<T>(sql, this.store)
      this.statementCache.set(sql, cached)
    }
    return cached as Statement<T>
  }

  /**
   * Prepare a statement without caching
   */
  prepare<T = unknown>(sql: string): Statement<T> {
    return new Statement<T>(sql, this.store)
  }

  /**
   * Execute SQL directly (CREATE TABLE, etc.)
   */
  exec(sql: string): void {
    // Parse CREATE TABLE statements to initialize storage
    const createMatch = sql.match(/CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)/gi)
    if (createMatch) {
      for (const match of createMatch) {
        const tableMatch = match.match(/(\w+)$/i)
        if (tableMatch?.[1]) {
          const tableName = tableMatch[1].toLowerCase()
          if (!this.store.has(tableName)) {
            this.store.set(tableName, [])
          }
        }
      }
    }
  }

  /**
   * Execute a single statement
   */
  run(sql: string, ...params: unknown[]): { lastInsertRowid: number | bigint; changes: number } {
    return this.prepare(sql).run(...params)
  }

  /**
   * Run a pragma command (mock - just return empty/default)
   */
  pragma(sql: string, options?: { simple?: boolean }): unknown {
    // Common pragmas - return sensible defaults
    if (sql.includes('journal_mode')) {
      return options?.simple ? 'wal' : [{ journal_mode: 'wal' }]
    }
    if (sql.includes('foreign_keys')) {
      return options?.simple ? 1 : [{ foreign_keys: 1 }]
    }
    if (sql.includes('busy_timeout')) {
      return options?.simple ? 5000 : [{ busy_timeout: 5000 }]
    }
    // Default: return empty array for non-simple, null for simple
    return options?.simple ? null : []
  }

  /**
   * Close database
   */
  close(_throwOnError: boolean = false): void {
    this._open = false
    this.store.clear()
    this.statementCache.clear()
  }

  /**
   * Serialize database (mock - return empty buffer)
   */
  serialize(): Uint8Array {
    return new Uint8Array(0)
  }

  /**
   * Deserialize database
   */
  static deserialize(_buffer: Uint8Array): Database {
    return new Database(':memory:')
  }

  /**
   * Create transaction wrapper
   */
  transaction<T extends (...args: unknown[]) => unknown>(
    fn: T
  ): T & {
    deferred: T
    immediate: T
    exclusive: T
  } {
    const self = this
    const wrapped = ((...args: unknown[]) => {
      self._inTransaction = true
      try {
        return fn(...args)
      } finally {
        self._inTransaction = false
      }
    }) as T & { deferred: T; immediate: T; exclusive: T }

    wrapped.deferred = wrapped
    wrapped.immediate = wrapped
    wrapped.exclusive = wrapped

    return wrapped
  }

  /**
   * Load extension (no-op in mock)
   */
  loadExtension(_path: string): void {}

  get inTransaction(): boolean {
    return this._inTransaction
  }

  get open(): boolean {
    return this._open
  }

  // Test helpers - allow tests to seed/inspect mock data
  __mockSetRows(table: string, rows: Row[]): void {
    this.store.set(table.toLowerCase(), rows)
  }

  __mockGetRows(table: string): Row[] {
    return this.store.get(table.toLowerCase()) || []
  }

  __mockClear(): void {
    this.store.clear()
  }
}

export default { Database }
