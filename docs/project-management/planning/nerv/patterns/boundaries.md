# System Boundaries

This document defines the concept of system boundaries in the NERV architecture - interfaces where data crosses between controlled and uncontrolled domains.

## Boundary Concept

System boundaries are critical points where data flows between different trust or control domains. They include:

- External API integrations
- File system interactions
- Database operations
- User input handling
- LLM model provider interactions

Each boundary requires explicit handling to ensure system integrity:

1. **Input Validation**: Ensuring incoming data meets requirements
2. **Type Conversion**: Converting between external and internal representations
3. **Error Handling**: Proper management of boundary-crossing failures
4. **Telemetry**: Tracking boundary interactions for observability

## Boundary Types

| Boundary Type      | Description                                     | Entry Point            | Exit Point               | Validation                             |
| ------------------ | ----------------------------------------------- | ---------------------- | ------------------------ | -------------------------------------- |
| **Network API**    | HTTP/HTTPS communication with external services | `NetworkRequest[T_in]` | `NetworkResponse[T_out]` | Schema validation, response parsing    |
| **File System**    | Reading/writing files                           | `FileReadRequest`      | `FileContent[T]`         | Format validation, content parsing     |
| **Database**       | Data storage and retrieval                      | `QueryRequest[T]`      | `QueryResult[T]`         | Schema validation, constraint checking |
| **User Input**     | Commands or data from user                      | `UserInputData`        | `ValidatedCommand`       | Type conversion, constraint checking   |
| **Model Provider** | LLM API integration                             | `ModelRequest`         | `ModelResponse`          | Schema validation, content filtering   |

## Boundary Interface

::: info Boundary Protocol
All system boundaries implement the `Boundary` protocol with the following interface:

- **`validate(data: T_in) -> ValidationResult[T_out]`**:  
  Validates incoming data and returns a validation result containing either validated data or errors.

- **`process(data: T_in) -> T_out`**:  
  Processes data across the boundary. May raise a `BoundaryError` if processing fails.

- **`handle_error(error: Exception) -> BoundaryError`**:  
  Handles errors at the boundary and returns an appropriate boundary error.
:::

## Boundary Pattern

The general pattern for all boundary interactions is:

```
External                  │                  Internal
                          │
                          │
Raw JSON ────────────────►│───► Validated DTO ───► Domain Model
                          │
HTTP Response ◄───────────│◄─── Typed Request ◄─── Business Logic
                          │
                          │
```

## Validation Results

::: details Validation Result Structure
All boundary validation operations return a `ValidationResult` that contains:

- **`is_valid`**: Boolean indicating whether validation succeeded
- **`data`**: Optional validated data of type T_out (present if validation succeeded)
- **`errors`**: List of error details as dictionaries (present if validation failed)
:::

## Error Handling

::: warning Boundary Error Hierarchy
Boundary errors are handled through a specialized error hierarchy:

**Base Error Class**:
- `BoundaryError`: Base class for all boundary errors
  - Properties: message, boundary name, details dictionary

**Specialized Error Classes**:
- `ValidationError`: For data validation failures
  - Additional property: validation_errors list
- `NetworkError`: For network operation failures
  - Additional properties: status_code, response data
:::

## Implementation Requirements

All boundary implementations must:

1. **Never Trust External Data**: Always validate before processing
2. **Use Explicit Types**: Clear input/output types with no implicit `Any`
3. **Handle All Errors**: Properly catch and transform all errors
4. **Log Boundary Crossings**: Enable observability of boundary interactions
5. **Prevent Data Leakage**: Control what information crosses the boundary

## Integration with Patterns

Boundaries integrate with other NERV patterns:

- **Reactive Event Mesh**: Boundaries emit events for boundary crossings
- **Effect System**: Boundary operations declare explicit effects
- **Perspective Shifting**: Different views based on boundary context

## Common Boundary Implementations

Atlas provides several common boundary implementations:

| Implementation          | Purpose                          | Key Features                                       |
|-------------------------|----------------------------------|---------------------------------------------------|
| **APIBoundary**         | HTTP API integration             | Request validation, response parsing, error mapping |
| **FileBoundary**        | File system operations           | Path safety, format validation, error handling     |
| **DatabaseBoundary**    | Database access                  | Schema validation, query safety, result mapping    |
| **UserInputBoundary**   | User interface interactions      | Input validation, sanitization, command parsing    |
| **ModelProviderBoundary**| LLM provider integration        | Content validation, provider-specific adaptations  |