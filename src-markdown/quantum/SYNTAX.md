# Quantum Language Syntax Specification

This document defines the formal syntax for Quantum, an LLM-optimized knowledge representation language designed for maximum semantic density with minimal token usage.

## Core Notation Elements

### 1. Entity Definition and Reference

```
@entity{id}    # Define an entity with optional identifier
#id           # Reference a previously defined entity
```

Example:
```
@concept{knowledge_graph}:p{type:"representation"}
#knowledge_graph->@concept{node}:p{role:"atomic_unit"}
```

### 2. Relationship Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `->` | Directed relationship | `@source->@target` |
| `<-` | Reverse relationship | `@target<-@source` |
| `<->` | Bidirectional relationship | `@concept1<->@concept2` |
| `--` | Undirected association | `@concept1--@concept2` |
| `==>` | Strong implication/causation | `@cause==>@effect` |
| `~>` | Probabilistic/weak relationship | `@input~>@possible_outcome` |

Relationships can be chained: `@a->@b->@c`

### 3. Property Assignment

```
:p{key:value}                       # Single property
:p{key1:value1,key2:value2}         # Multiple properties
:t{tag1,tag2,tag3}                  # Tag assignment
```

Example:
```
@concept:p{importance:"high",domain:"core"}:t{foundational,critical}
```

### 4. Inheritance

```
@child^parent                  # Basic inheritance
@child^parent1+parent2         # Multiple inheritance
@child^parent\exception        # Inheritance with exception
```

Example:
```
@specialized_method^general_method:p{context:"specific"}
@hybrid^approach1+approach2:p{purpose:"integration"}
```

### 5. Contextual Boundaries

```
[context]{content}             # Scope content to context
[context1+context2]{content}   # Multiple context scoping
[*]{global_content}            # Global context
[!context]{exclusion}          # Explicitly not in context
```

Example:
```
[technical]{@concept:p{definition:"technical explanation"}}
[business+strategy]{@concept:p{value:"business impact"}}
```

### 6. Shorthand Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `+` | Include/add | `base+extension` |
| `-` | Exclude/remove | `set-subset` |
| `?` | Query/condition | `condition?result:alternative` |
| `!` | Negation/inverse | `!condition` |
| `*` | Wildcard/any | `pattern*suffix` |
| `&` | Logical AND | `condition1&condition2` |
| `\|` | Logical OR | `option1\|option2` |

### 7. Templating

```
t(template_name){arg1,arg2}    # Template with arguments
d(pattern){replacement}        # Define pattern replacement
m{pattern}                     # Match pattern
```

Example:
```
@t{system}[input->processing->output]
t(system){data,algorithm,result}
```

### 8. Quantum Partitioning

#### Basic Quantum Definition
```
q{boundary}[content]          # Define quantum with boundary
q1><q2                        # Relationship between quanta
q{boundary}:w{5}[content]     # Weighted quantum
```

#### Quantum Dimensions
```
q:coherence{level}[content]   # Boundary based on internal consistency
q:complexity{level}[content]  # Boundary based on information density
q:purpose{intent}[content]    # Boundary based on functional intent
```

#### Adaptive Boundaries
```
q:context{situation}[content] # Context-specific boundary
q:perspective{view}[content]  # Perspective-specific boundary
q:temporal{stage}[content]    # Time-dependent boundary
```

Example:
```
q{core_concepts}[@principle1,@principle2,@principle3]
q{applications}[@app1,@app2]
q{core_concepts}><q{applications}:p{relationship:"implements"}
q:coherence{high}[@core_algorithm,@essential_functions]
q:purpose{learning}[@concept,@examples,@exercises]
q:context{implementation}[@components,@interfaces]
```

### 9. Perspective Markers

#### Basic Perspective Definition
```
@p:view[content]               # Content from specific perspective
@p:view1->view2[transition]    # Transition between perspectives
```

#### Perspective Types
```
@p:domain{type}[content]       # Domain-specific perspective (technical, user, etc.)
@p:scale{level}[content]       # Scale perspective (micro, macro, etc.)
@p:cognitive{style}[content]   # Cognitive style (analytical, synthetic, etc.)
```

#### Perspective Operations
```
@p:blend{view1+view2}[content] # Combined perspectives
@p:focus{area}[content]        # Attention-focused perspective
@p:adapt{context}[content]     # Context-adapted perspective
```

Example:
```
@p:technical[@system:p{architecture:"detailed"}]
@p:user[@system:p{interface:"simplified"}]
@p:scale{macro}[@architecture:p{overview:"system-wide"}]
@p:blend{developer+user}[@interface:p{design:"balanced"}]
```

### 10. Temporal Annotations

#### Basic Versioning
```
t:v1[content]                   # Content from version
t:delta{v1->v2}[changes]        # Changes between versions
t:history{v1,v2,v3}             # Historical sequence
```

#### Evolution Patterns
```
t:pattern{expansion}[content]   # Growth through addition
t:pattern{refinement}[content]  # Increased precision
t:pattern{restructuring}[content] # Organization change
t:pattern{obsolescence}[content] # Outdated knowledge
```

#### Temporal Dynamics
```
t:velocity{rate}[content]       # Change speed marker
t:lifespan{duration}[content]   # Expected validity period
t:trajectory{direction}[path]   # Evolution direction
```

#### Temporal Navigation
```
t:timeline[marker1,marker2]     # Sequential reference points
t:milestone{name}[criteria]     # Significant temporal point
t:projection{confidence}[state] # Predicted future state
```

Example:
```
@concept:t:v1[initial_definition]
@concept:t:v2[evolved_definition]
@concept:t:pattern{refinement}[precision_improvements]
@concept:t:velocity{stable}[core_principles]
@concept:t:trajectory{expansion}[future_development]
```

### 11. Graph Structure Notation

```
@node{id}                    # Define graph node
#id1->#id2                   # Edge between nodes
(#id1,#id2)->#id3            # Multiple sources
#id1->(#id2,#id3)            # Multiple targets
path{#id1->#id2->#id3}       # Defined path
```

Example:
```
@node{start}:p{type:"entry"}
@node{process}:p{type:"transformation"}
@node{end}:p{type:"output"}
path{#start->#process->#end}:p{name:"main_flow"}
```

## Grammar Definition

### Tokens

```
ENTITY      ::= '@' IDENTIFIER ['{' ID_VALUE '}']
REFERENCE   ::= '#' IDENTIFIER
PROPERTY    ::= ':p{' PROP_LIST '}'
TAG         ::= ':t{' TAG_LIST '}'
INHERITANCE ::= '^' PARENT_LIST
CONTEXT     ::= '[' CONTEXT_LIST ']{' CONTENT '}'
QUANTUM     ::= 'q' [':' QUANTUM_TYPE] '{' BOUNDARY '}' [':' ATTRIBUTES] '[' CONTENT ']'
PERSPECTIVE ::= '@p' [':' PERSPECTIVE_TYPE] ['{' PERSPECTIVE_PARAMS '}'] '[' CONTENT ']'
TEMPORAL    ::= 't' [':' TEMPORAL_TYPE] ['{' TEMPORAL_PARAMS '}'] '[' CONTENT ']'
```

### Production Rules

```
expression        ::= entity | relationship | property_assignment | context_block | quantum_block | 
                      perspective_block | temporal_block
entity            ::= ENTITY [PROPERTY] [TAG] [INHERITANCE]
relationship      ::= source RELATION_OP target [PROPERTY]
source            ::= entity | REFERENCE | '(' entity_list ')'
target            ::= entity | REFERENCE | '(' entity_list ')'
property_assignment ::= entity PROPERTY
context_block     ::= CONTEXT
quantum_block     ::= QUANTUM
perspective_block ::= PERSPECTIVE
temporal_block    ::= TEMPORAL
quantum_type      ::= 'coherence' | 'complexity' | 'purpose' | 'context' | 'perspective' | 'temporal'
perspective_type  ::= 'domain' | 'scale' | 'cognitive' | 'blend' | 'focus' | 'adapt'
temporal_type     ::= 'pattern' | 'velocity' | 'lifespan' | 'trajectory' | 'milestone' | 'projection'
```

## Syntax Validation Rules

1. Every reference (`#id`) must have a corresponding definition (`@entity{id}`)
2. Inheritance sources (`^parent`) must be defined before use
3. Context identifiers in `[context]` must be defined as entities
4. Quantum boundaries must reference valid contextual domains
5. Template arguments must match template parameter count
6. Path definitions must reference existing nodes
7. Properties must use valid key formats (alphanumeric with underscores)
8. Nested structures must have balanced delimiters

## Compression Directives

Special directives that control compression behavior:

```
$compress{ratio:high}         # Set compression ratio
$preserve{critical_paths}     # Mark elements for preservation
$optimize{token_count}        # Optimization target
$format{dense|readable}       # Output format preference
```

## Syntax Highlighting Recommendations

For improved readability in documentation:

- Entities (`@concept`) - Blue
- References (`#id`) - Cyan
- Relationships (`->`, `<->`) - Red
- Properties (`:p{...}`) - Green
- Inheritance (`^parent`) - Purple
- Contexts (`[context]`) - Yellow
- Quantum markers (`q{...}`) - Magenta
- Perspective markers (`@p:...`) - Teal
- Temporal annotations (`t:...`) - Orange

## Version Notes

This syntax specification is for Quantum v1.0. The language is designed to be extensible with backward compatibility.