---
name: code-simplification
description: Simplifies code for clarity without changing behavior. Use when refactoring working code that is harder to read than it should be, when reviewing unnecessary complexity, /simplify-code (Cursor), /code-simplification (Claude), or $code-simplification (Codex).
disable-model-invocation: true
---

# Code Simplification

Simplify code by reducing complexity while preserving exact behavior. The goal is not fewer lines; it is code that is easier to read, understand, modify, and debug. Every simplification must pass a simple test: "Would a new team member understand this faster than the original?"

## The Five Principles

### 1. Preserve Behavior Exactly

Do not change what the code does, only how it expresses it. All inputs, outputs, side effects, error behavior, and edge cases must remain identical. If you are not sure a simplification preserves behavior, do not make it.

Before every change, ask:

- Does this produce the same output for every input?
- Does this maintain the same error behavior?
- Does this preserve the same side effects and ordering?
- Do all existing tests still pass without modification?

### 2. Respect Intentional Conventions

Study neighboring code to understand deliberate conventions, but do not copy accidental complexity merely because it is common.

Before simplifying:

1. Read `AGENTS.md`, applicable project rules, and relevant Cursor skills
2. Distinguish documented decisions from repeated legacy or hand-rolled patterns
3. Prefer clearer, behavior-preserving project or library abstractions over deficient local precedent
4. Apply the chosen pattern consistently within the task's scope

A repeated pattern proves prevalence, not quality. When the existing convention is weak, establish the better pattern directly rather than preserving complexity for consistency.

### 3. Prefer Clarity Over Cleverness

Explicit code is better than compact code when the compact version requires a mental pause to parse.

```typescript
// UNCLEAR: Dense ternary chain
const label = isNew ? "New" : isUpdated ? "Updated" : isArchived ? "Archived" : "Active";

// CLEAR: Readable control flow
function getStatusLabel(item: Item): string {
  if (item.isNew) return "New";
  if (item.isUpdated) return "Updated";
  if (item.isArchived) return "Archived";
  return "Active";
}
```

```typescript
// UNCLEAR: Transformation logic buried in the call site
const labels = items.map((item) => `${item.name}: ${formatValue(item.value)}`);

// CLEAR: Named transformation
function formatItemLabel(item: Item): string {
  return `${item.name}: ${formatValue(item.value)}`;
}

const labels = items.map(formatItemLabel);
```

### 4. Maintain Balance

Simplification has a failure mode: over-simplification. Watch for these traps:

- **Inlining too aggressively**: removing a helper that gave a concept a name makes the call site harder to read
- **Combining unrelated logic**: two simple functions merged into one complex function is not simpler
- **Removing "unnecessary" abstraction**: some abstractions exist for extensibility or testability, not complexity
- **Optimizing for line count**: fewer lines is not the goal; easier comprehension is

### 5. Scope to What Changed

Default to simplifying recently modified code. Inspect the current diff first. Avoid drive-by refactors of unrelated code unless explicitly asked to broaden scope. Unscoped simplification creates noise in diffs and risks unintended regressions.

## The Simplification Process

### Step 1: Understand Before Touching

Apply Chesterton's Fence: if you see a fence across a road and do not understand why it is there, do not tear it down. First understand the reason, then decide whether the reason still applies.

Before simplifying, answer:

- What is this code's responsibility?
- What calls it? What does it call?
- What are the edge cases and error paths?
- Are there tests that define the expected behavior?
- Why might it have been written this way: performance, platform constraint, or historical reason?
- What does git history or blame reveal about the original context?

Use Cursor's file reading and search tools to inspect code, tests, callers, and project guidance. Use git history when the reason is not evident from current code. If you cannot answer these questions, read more context before editing.

### Step 2: Identify Simplification Opportunities

Scan for these concrete signals:

#### Structural complexity

| Pattern | Signal | Simplification |
|---|---|---|
| Deep nesting (3+ levels) | Hard to follow control flow | Extract conditions into guard clauses or helper functions |
| Long functions (50+ lines) | Multiple responsibilities | Split into focused functions with descriptive names |
| Nested ternaries | Requires mental stack to parse | Replace with if/else chains, switch, or lookup objects |
| Boolean parameter flags | `doThing(true, false, true)` | Replace with options objects or separate functions |
| Repeated conditionals | Same `if` check in multiple places | Extract to a well-named predicate function |

#### Naming and readability

| Pattern | Signal | Simplification |
|---|---|---|
| Generic names | `data`, `result`, `temp`, `val`, `item` | Rename to describe the content: `userProfile`, `validationErrors` |
| Abbreviated names | `usr`, `cfg`, `btn`, `evt` | Use full words unless the abbreviation is universal (`id`, `url`, `api`) |
| Misleading names | Function named `get` that also mutates state | Rename to reflect actual behavior |
| Comments explaining "what" | `// increment counter` above `count++` | Delete the comment; the code is clear enough |
| Comments explaining "why" | `// Retry because the API is flaky under load` | Keep these; they carry intent the code cannot express |

#### Redundancy

| Pattern | Signal | Simplification |
|---|---|---|
| Duplicated logic | Same 5+ lines in multiple places | Extract to a shared function |
| Dead code | Unreachable branches, unused variables, commented-out blocks | Remove after confirming it is truly dead |
| Unnecessary abstractions | Wrapper that adds no value | Inline the wrapper and call the underlying function directly |
| Over-engineered patterns | Factory-for-a-factory, strategy-with-one-strategy | Replace with the simple direct approach |
| Redundant type assertions | Casting to a type that is already inferred | Remove the assertion |

#### Existing project and library abstractions

Before hand-rolling related parsing, validation, normalization, transformation, defaults, or error handling, inspect existing project modules, dependencies, and generated clients for an abstraction that already composes those concerns.

Prefer an existing abstraction when it:

- Covers the required behavior
- Preserves existing semantics and errors, directly or through a narrow boundary adapter
- Is already an accepted project dependency
- Replaces multiple coordinated checks or transformations

For example, do not make an order service duplicate product lookup and availability rules already owned by a product service:

```typescript
// UNCLEAR: OrderService reimplements ProductService behavior
class OrderService {
  async createOrder(productId: string, quantity: number): Promise<Order> {
    const product = await this.productRepository.findById(productId);
    if (!product || !product.isAvailable) {
      throw new ProductUnavailableError(productId);
    }
    return this.orders.create({ productId, quantity, unitPrice: product.price });
  }
}

// CLEAR: ProductService owns product availability behavior
class OrderService {
  async createOrder(productId: string, quantity: number): Promise<Order> {
    const product = await this.products.getAvailableProduct(productId);
    return this.orders.create({ productId, quantity, unitPrice: product.price });
  }
}
```

The same principle applies to libraries: prefer an existing schema library over coordinated manual required-field checks, timestamp parsing, nullable-field handling, transformations, and one-of validation. Keep bespoke logic when it represents domain policy rather than structural mechanics, such as an enum mapping that intentionally preserves unknown provider values.

Abstraction-first does not mean replacing intentional behavior, obscuring a simple operation, or adding a dependency for trivial code.

### Step 3: Apply Changes Incrementally

Make one conceptual simplification at a time. Verify after each change.

For each simplification:

1. Make the change
2. Run the narrowest relevant tests or static checks
3. If checks pass, continue to the next simplification
4. If checks fail, revert that change and reconsider

Submit refactoring changes separately from feature or bug-fix changes. A pull request that refactors and adds a feature contains two efforts; split them.

Avoid batching multiple simplifications into a single untested change. If something breaks, you need to know which simplification caused it.

**The Rule of 500:** If a refactoring would touch more than 500 lines, invest in automation such as codemods or AST transforms rather than making the changes by hand. Manual edits at that scale are error-prone and exhausting to review.

### Step 4: Verify the Result

After all simplifications, compare before and after:

- Is the simplified version genuinely easier to understand?
- Did you introduce any new patterns inconsistent with the codebase?
- Is the diff clean and reviewable?
- Would a teammate approve this change as a net improvement?

If the simplified version is harder to understand or review, revert it. Not every simplification attempt succeeds.

## Language-Specific Guidance

### TypeScript / JavaScript

```typescript
// SIMPLIFY: Unnecessary local variable
// Before
function getUser(id: string): Promise<User> {
  const userPromise = userService.findById(id);
  return userPromise;
}

// After
function getUser(id: string): Promise<User> {
  return userService.findById(id);
}
```

```typescript
// SIMPLIFY: Verbose conditional assignment
// Before
let displayName: string;
if (user.nickname) {
  displayName = user.nickname;
} else {
  displayName = user.fullName;
}

// After
const displayName = user.nickname || user.fullName;
```

```typescript
// SIMPLIFY: Manual array building
// Before
const activeUsers: User[] = [];
for (const user of users) {
  if (user.isActive) {
    activeUsers.push(user);
  }
}

// After
const activeUsers = users.filter((user) => user.isActive);
```

```typescript
// SIMPLIFY: Redundant boolean return
// Before
function isValid(input: string): boolean {
  if (input.length > 0 && input.length < 100) {
    return true;
  }
  return false;
}

// After
function isValid(input: string): boolean {
  return input.length > 0 && input.length < 100;
}
```

### Python

```python
# SIMPLIFY: Verbose dictionary building
# Before
result = {}
for item in items:
    result[item.id] = item.name

# After
result = {item.id: item.name for item in items}
```

```python
# SIMPLIFY: Nested conditionals with early return
# Before
def process(data):
    if data is not None:
        if data.is_valid():
            if data.has_permission():
                return do_work(data)
            else:
                raise PermissionError("No permission")
        else:
            raise ValueError("Invalid data")
    else:
        raise TypeError("Data is None")

# After
def process(data):
    if data is None:
        raise TypeError("Data is None")
    if not data.is_valid():
        raise ValueError("Invalid data")
    if not data.has_permission():
        raise PermissionError("No permission")
    return do_work(data)
```

### React / JSX

```tsx
// SIMPLIFY: Verbose conditional rendering
// Before
function UserBadge({ user }: Props) {
  if (user.isAdmin) {
    return <Badge variant="admin">Admin</Badge>;
  } else {
    return <Badge variant="default">User</Badge>;
  }
}

// After
function UserBadge({ user }: Props) {
  const variant = user.isAdmin ? "admin" : "default";
  const label = user.isAdmin ? "Admin" : "User";
  return <Badge variant={variant}>{label}</Badge>;
}
```

For prop drilling through intermediate components, consider whether context or composition solves the problem better. This is a judgment call; flag it rather than auto-refactoring.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's working, no need to touch it" | Working code that is hard to read will be hard to fix when it breaks. Simplifying now saves time on every future change. |
| "Fewer lines is always simpler" | A one-line nested ternary is not simpler than a five-line if/else. Simplicity is about comprehension speed, not line count. |
| "I'll just quickly simplify this unrelated code too" | Unscoped simplification creates noisy diffs and risks regressions in code you did not intend to change. Stay focused. |
| "The types make it self-documenting" | Types document structure, not intent. A well-named function explains why better than a type signature explains what. |
| "This abstraction might be useful later" | Do not preserve speculative abstractions. If it is not used now, it is complexity without value. Remove it and re-add when needed. |
| "The original author must have had a reason" | Maybe. Check git blame and apply Chesterton's Fence. Accumulated complexity often has no reason; it is the residue of iteration under pressure. |
| "I'll refactor while adding this feature" | Separate refactoring from feature work. Mixed changes are harder to review, revert, and understand in history. |

## Red Flags

- Simplification that requires modifying tests to pass; you likely changed behavior
- Simplified code that is longer and harder to follow than the original
- Renaming things to match personal preferences rather than project conventions
- Removing error handling because it makes the code cleaner
- Simplifying code you do not fully understand
- Batching many simplifications into one large, hard-to-review commit
- Refactoring code outside the scope of the current task without being asked

## Verification

After completing a simplification pass, verify:

- [ ] All existing tests pass without modification
- [ ] Build succeeds with no new warnings
- [ ] Linter and formatter pass with no style regressions
- [ ] Each simplification is a reviewable, incremental change
- [ ] The diff is clean with no unrelated changes mixed in
- [ ] Simplified code follows project conventions
- [ ] No error handling was removed or weakened
- [ ] No dead code was left behind, including unused imports and unreachable branches
- [ ] The result is a net improvement a teammate or review agent would approve
