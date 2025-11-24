# Comprehensive Prompt Engineering Guide for Factory Droid

## Table of Contents
1. [Understanding Droid's Prompt Processing](#understanding-droids-prompt-processing)
2. [Core Prompting Principles](#core-prompting-principles)
3. [Prompt Patterns and Templates](#prompt-patterns-and-templates)
4. [Domain-Specific Prompts](#domain-specific-prompts)
5. [Advanced Prompting Techniques](#advanced-prompting-techniques)
6. [Common Prompting Mistakes](#common-prompting-mistakes)
7. [Real-World Examples and Case Studies](#real-world-examples-and-case-studies)
8. [Debugging and Refining Prompts](#debugging-and-refining-prompts)

## Understanding Droid's Prompt Processing

### How Droid Interprets Your Requests

Factory Droid processes prompts differently from typical AI assistants. Here's what happens internally:

1. **Intent Recognition**: Droid identifies whether you want to create, modify, analyze, or debug
2. **Context Analysis**: It scans your codebase to understand the existing structure and patterns
3. **Task Decomposition**: Complex requests are broken down into manageable steps
4. **Resource Identification**: Droid identifies which files, tools, and dependencies are needed
5. **Execution Planning**: A sequence of operations is planned before any code is written

### The Three Layers of Understanding

**Layer 1: Immediate Intent**
```
You: "Fix the login bug"
Droid understands: User wants to resolve an authentication issue
```

**Layer 2: Context Recognition**
```
Droid scans: Uses what database (MongoDB)? Authentication method (JWT)? Frontend framework (React)?
```

**Layer 3: Comprehensive Action**
```
Droid plans: 1) Find login files, 2) Identify the bug, 3) Fix authentication, 4) Test, 5) Verify
```

## Core Prompting Principles

### 1. Be Explicit and Specific

**Vague Prompt**:
```
Add authentication
```

**Specific Prompt**:
```
Add JWT-based authentication with these requirements:
- User registration with email verification
- Login with email/password
- Password reset functionality
- Protected routes requiring authentication
- Session timeout after 30 minutes
```

### 2. Provide Context Upfront

**Without Context**:
```
Fix the form validation
```

**With Context**:
```
Fix the registration form validation in src/components/RegistrationForm.tsx.
Currently, users can submit with empty fields. The form should:
- Require valid email format
- Require password with at least 8 characters
- Show inline error messages
- Prevent submission until all fields are valid
```

### 3. Reference Existing Patterns

**Good Example**:
```
Create a settings page similar to the profile page structure in src/pages/Profile.tsx.
Use the same layout, tabs design, and form validation patterns.
Include fields for notifications, privacy, and account preferences.
```

### 4. Define Success Criteria

**Excellent Example**:
```
Implement file upload functionality for user avatars:
- Support JPEG, PNG formats up to 5MB
- Show upload progress bar
- Display preview before final upload
- Store in S3 bucket with proper permissions
- Update user profile immediately after upload
Test by uploading a profile picture and verify it appears on the user profile
```

## Prompt Patterns and Templates

### Pattern 1: The Feature Development Template

```bash
# [Feature Name] Implementation

## Requirements
- [Specific requirement 1]
- [Specific requirement 2]
- [Specific requirement 3]

## Technical Details
- [Technology/framework to use]
- [Database changes needed]
- [API endpoints required]

## Similar Existing Pattern
- Reference: [file or feature with similar implementation]
- Follow the patterns used in [specific file]

## Verification Steps
- [How to test/verify the implementation]
- [Expected behavior]
- [Edge cases to consider]
```

**Example Usage**:
```
Add comment system implementation:

Requirements:
- Users can comment on posts
- Comments support replies (nested to 2 levels)
- Real-time updates when new comments are added
- Markdown support in comments
- Comment deletion by original author or post owner

Technical Details:
- Use WebSocket for real-time updates
- Store in PostgreSQL with nested set model
- Create API endpoints: POST /posts/:id/comments, DELETE /comments/:id
- Frontend components: CommentList, CommentForm, CommentItem

Similar Existing Pattern:
- Reference the reply system in src/features/replies/
- Follow the same real-time patterns used in chat implementation

Verification Steps:
- Test adding a comment to a post
- Verify real-time update in other browser sessions
- Test nested replies functionality
- Verify markdown rendering with tables and headers
```

### Pattern 2: The Bug Fix Template

```bash
# Bug Fix Request

## Error Description
[Describe the error and when it occurs]

## Error Details
- Error message: [exact error message]
- File location: [where error occurs]
- Steps to reproduce: [clear reproduction steps]

## Expected Behavior
[What should happen instead]

## Context
- [Recent changes that might have caused this]
- [Similar working functionality elsewhere]
```

**Example Usage**:
```
Fix profile image upload bug:

Error Description:
Users report that profile image uploads fail intermittently with "File too large" error, even for small images.

Error Details:
- Error message: "Error: ENOENT: no such file or directory, open '/tmp/uploads/undefined'"
- File location: src/services/imageUpload.js line 47
- Steps to reproduce:
  1. Go to profile settings
  2. Click "Change profile picture"
  3. Select any image file
  4. Click upload

Expected Behavior:
Image should upload successfully and appear on user profile immediately.

Context:
- The upload was working before the recent deployment
- Similar file upload in posts feature/src/posts/Upload.tsx works fine
```

### Pattern 3: The Refactoring Template

```bash
# Refactoring Request

## Current Situation
[Describe the current code structure and why it needs refactoring]

## Refactoring Goals
- [Specific improvement 1]
- [Specific improvement 2]

## Constraints
- [What must not change - API contracts, UI behavior, etc.]

## Implementation Approach
- [Preferred refactoring strategy]
```

**Example Usage**:
```
Refactor payment processing module:

Current Situation:
Payment processing logic is scattered across multiple files with duplicated validation code and mixed error handling approaches.

Refactoring Goals:
- Extract all payment logic into a single PaymentService class
- Create unified error handling for payment failures
- Implement proper logging for audit trails
- Make the payment module testable with mocks

Constraints:
- Must maintain all existing API endpoints
- Cannot change payment provider integration
- Frontend payment form must work identically

Implementation Approach:
- Create src/services/PaymentService.ts
- Use dependency injection for payment provider
- Implement decorator pattern for payment steps
- Add comprehensive unit tests
```

## Domain-Specific Prompts

### Frontend Development Prompts

**Component Creation**:
```bash
Create a reusable DataTable component with these features:
- Sortable columns by clicking headers
- Pagination controls with page size selection
- Row selection with bulk actions
- Responsive design for mobile
- Loading states and error handling
Use TypeScript interfaces for props and follow accessibility standards
```

**State Management**:
```bash
Set up Redux store for user management:
- Define actions for CRUD operations on users
- Create reducers with optimistic updates
- Add selectors for filtered user lists
- Include error handling in async thunks
- Use RTK Query for API calls
```

### Backend Development Prompts

**API Development**:
```bash
Create RESTful API endpoints for inventory management:
- GET /api/inventory (list with pagination and filtering)
- POST /api/inventory (create with validation)
- PUT /api/inventory/:id (update with optimistic concurrency)
- DELETE /api/inventory/:id (soft delete)
Implement OpenAPI documentation and input validation with express-validator
```

**Database Operations**:
```bash
Optimize the order processing database queries:
- Add indexes to frequently queried columns
- Implement connection pooling for high traffic
- Use transactions for multi-table operations
- Add query logging for performance monitoring
- Create database migration scripts for all changes
```

### Full-Stack Integration Prompts

**CRUD Feature**:
```bash
Implement complete project management feature:
Frontend: Create ProjectCard components with drag-and-drop status updates
Backend: Add project endpoints with team member assignments
Database: Design schema with proper relationships and indexes
Real-time: Use WebSockets for live project status updates
Testing: Include e2e tests for full workflow
```

## Advanced Prompting Techniques

### 1. Multi-Phase Development

Break complex features into phases:

```bash
Phase 1: Create the basic blog post CRUD functionality
- Backend endpoints for posts
- Basic listing and detail pages
- Simple markdown preview

Phase 2: Add advanced features
- Rich text editor
- Image uploads and galleries
- Tag system and categories

Phase 3: Implement user interactions
- Comments and replies
- Like/bookmark functionality
- User subscriptions and notifications
```

### 2. Constraint-Based Prompts

Guiding Droid with technical constraints:

```bash
Add social sharing buttons to blog posts with these constraints:
- Must not use external tracking libraries
- Should work without JavaScript (progressive enhancement)
- Must pass WCAG 2.1 accessibility tests
- Should bundle to less than 15KB additional code
- Use only native browser APIs where possible
```

### 3. Code Style Prompts

Ensuring consistency with existing code:

```bash
Create the new analytics dashboard following these patterns:
- Use the same color scheme as src/styles/theme.ts
- Follow the component structure used in src/components/Dashboard/
- Import patterns from src/utils/api.ts for API calls
- Error handling should match src/hooks/useDataFetcher.ts
- TypeScript types should use our custom utility types
```

### 4. Performance-Oriented Prompts

Optimization-focused requests:

```bash
Optimize the photo gallery component:
- Implement virtual scrolling for large image lists
- Add lazy loading with intersection observer
- Use web workers for image compression
- Implement progressive image loading with blur-up
- Cache rendered components with React.memo
- Debounce search input with 300ms delay
```

## Common Prompting Mistakes

### Mistake 1: Too Vague

❌ Bad:
```
Make it faster
```

✅ Good:
```
Optimize the dashboard loading time:
- Implement data caching with TTL of 5 minutes
- Add skeleton loading states during data fetch
- Use React.memo for expensive render components
- Reduce bundle size by code splitting the charts library
```

### Mistake 2: Missing Context

❌ Bad:
```
Fix the login error
```

✅ Good:
```
Fix the authentication timeout error on the login page.
Users get logged out after 5 minutes instead of the configured 30 minutes.
The JWT token expiration is set correctly in the backend,
but the frontend refresh token logic seems to be failing. 
Check src/auth/useAuth.ts and src/services/tokenRefresh.ts
```

### Mistake 3: Ignoring Existing Patterns

❌ Bad:
```
Add a new dashboard
```

✅ Good:
```
Create analytics dashboard following the admin dashboard pattern:
- Use the same sidebar navigation from src/components/Sidebar.tsx
- Follow the card grid layout from src/pages/Admin.tsx
- Implement similar data loading patterns as src/hooks/useDashboard.ts
- Use the same chart components from src/components/Charts/
```

### Mistake 4: No Success Criteria

❌ Bad:
```
Implement search functionality
```

✅ Good:
```
Implement smart search for products:
- Search by name, description, and SKU
- Fuzzy matching with typo tolerance
- Real-time search results as user types (300ms debounce)
- Highlight matched terms in results
- Show search history and suggestions
- Performance: results should load under 200ms
```

## Real-World Examples and Case Studies

### Case Study 1: E-commerce Checkout Flow

**Initial Weak Prompt**:
```
Add checkout to my store
```

**Optimized Effective Prompt**:
```
Implement complete e-commerce checkout flow:

Frontend Requirements:
- Multi-step checkout: Shipping → Payment → Review → Confirmation
- Address validation with postal code lookup
- Stripe Elements for secure payment processing
- Order summary with tax calculation
- Mobile-responsive design with progress indicator

Backend Requirements:
- Create order endpoint with inventory checking
- Integrate Stripe payment processing
- Implement webhook handling for payment confirmation
- Add order status tracking system
- Email notifications for order confirmation and shipping

Database Changes:
- Orders table with proper indexing
- Order items with foreign key relationships
- Payment transaction logging
- Customer address book functionality

Success Verification:
- Test complete checkout with test card numbers
- Verify inventory changes after successful payment
- Confirm email notifications are sent
- Check order appears in user order history
- Test error handling for declined payments

Follow existing patterns in:
- src/components/Checkout/ (similar to cart component structure)
- src/api/payments/ (use existing Stripe integration pattern)
```

### Case Study 2: Real-time Collaboration Feature

**Effective Prompt with Context**:
```
Build real-time document collaboration similar to Google Docs:

Technical Requirements:
- Use WebSockets for real-time synchronization
- Implement operational transformation (OT) for concurrent editing
- Store document versions with change tracking
- Add user presence indicators (cursors and selections)
- Support document sharing with permission levels

Frontend Implementation:
- Create Editor component based on TipTap library (already in package.json)
- Real-time cursor position sharing
- Change tracking with visual indicators
- User avatars showing who's editing
- Offline mode with sync when reconnected

Backend Implementation:
- WebSocket server handling document operations
- Redis for managing document state and user sessions
- Database schema following our existing models in src/models/
- REST API for document management fallback

Constraints and Considerations:
- Must handle 1000+ concurrent users per document
- Network latency up to 500ms should not cause conflicts
- Implement rate limiting to prevent abuse
- Support undo/redo functionality across sessions
- Ensure data consistency even with network interruptions

Testing Strategy:
- Load testing with simulated concurrent edits
- Network interruption recovery testing
- Permission boundary testing
- Cross-browser compatibility verification

Reference our existing real-time features in:
- src/features/chat/ (WebSocket patterns)
- src/utils/operationalTransform/ (existing OT utilities)
```

### Case Study 3: Refactoring Legacy Code

**Strategic Refactoring Prompt**:
```
Refactor the user authentication system from callbacks to async/await:

Current State Analysis:
- Authentication uses callback patterns from 2018
- Nested callback hell creates maintenance issues
- Error handling is inconsistent across files
- Testing is difficult due to callback complexity

Refactoring Goals:
- Convert all auth functions to async/await
- Implement consistent error handling with proper HTTP status codes
- Add comprehensive unit tests with mocking
- Maintain complete backward compatibility
- Improve type safety with TypeScript

Detailed Requirements:
1. Update src/auth/callbacks.js → src/auth/async.js
2. Migrate database calls to use promise-based PostgreSQL driver
3. Add proper error boundaries in authentication middleware
4. Update all dependent routes to work with async functions
5. Add integration tests for the complete authentication flow

Constraints:
- Cannot break existing client applications
- JWT token format must remain identical
- API response structure must stay the same
- Must maintain session management approach

Verification Steps:
- Run existing test suite (should all pass)
- Manually test login flow in staging environment
- Verify token refresh still works correctly
- Check that error responses are properly formatted
- Monitor for performance regressions in authentication

Files to modify (high priority):
- src/middleware/auth.js
- src/routes/auth.js
- src/services/userService.js
- tests/auth/*.js
```

## Debugging and Refining Prompts

### When Droid Doesn't Understand

**Symptom**: Droid provides incorrect or incomplete implementation

**Debugging Steps**:

1. **Add More Specific Context**:
   ```
   I need help with the payment integration. The error occurs in src/components/PaymentForm.tsx at line 23.
   The Stripe integration should follow the pattern used in src/components/DonationForm.tsx
   ```

2. **Provide Examples**:
   ```
   Create a data table similar to the UserList component. Look at how it handles:
   - Pagination in src/components/UserList.tsx lines 45-67
   - Column sorting in lines 89-112
   - Row selection in lines 134-156
   ```

3. **Break Down the Request**:
   ```
   Let's approach this in smaller steps:
   1. First create the basic component structure
   2. Then add the data loading functionality
   3. Finally implement the filtering and sorting
   ```

### Iterative Refinement Process

**Round 1 - Initial Request**:
```
Add user profiles
```

**Droid Response**: Creates basic profile page

**Round 2 - Refinement**:
```
Great start! Now enhance the profile page with:
- Social media links that open in new tabs
- Profile picture upload with cropping
- Skills/tags with autocomplete
- Activity timeline showing recent actions
```

**Round 3 - Final Polish**:
```
Perfect! Now add these finishing touches:
- Implement lazy loading for the activity timeline
- Add privacy controls for profile visibility
- Create profile sharing functionality
- Add export profile to PDF feature
```

### Using the Review Process Effectively

When Droid shows you code changes, use this checklist:

1. **Functionality Verification**
   - Does it implement all requested features?
   - Are edge cases handled properly?
   - Does it follow the specified constraints?

2. **Code Quality Check**
   - Is the code readable and maintainable?
   - Does it follow project coding standards?
   - Are variable names descriptive?

3. **Integration Review**
   - Does it integrate properly with existing code?
   - Are imports correctly structured?
   - Does it maintain backward compatibility?

4. **Performance Considerations**
   - Are there obvious performance bottlenecks?
   - Are database queries optimized?
   - Is memory usage reasonable?

### Feedback Templates for Better Results

**Positive Reinforcement**:
```
Great implementation! The component works perfectly.
Can you now add loading states that match the pattern in src/components/LoadingSpinner.tsx?
```

**Constructive Feedback**:
```
The API endpoint works well, but I need a few adjustments:
1. Add response caching with 5-minute TTL
2. Implement rate limiting: max 100 requests per minute
3. Add proper error logging with request IDs
4. Include response time monitoring
```

**Course Correction**:
```
I think I wasn't clear enough in my previous request. 
Instead of creating a new component, let's modify the existing UserCard.tsx to:
- Add hover effects similar to ProductCard.tsx
- Include action buttons matching our design system
- Implement the card grid layout from Dashboard.tsx
```

## Advanced Prompt Strategies

### Context Injection

Provide rich context with file contents:

```bash
Here's the current authentication code (see attached src/auth/current.ts). 
I need to migrate it to use OAuth2 with GitHub, following this architecture:
1. Redirect to GitHub for authentication
2. Handle callback with access code
3. Exchange code for access token
4. Fetch user profile from GitHub API
5. Create/update user in our database

The current token validation logic can be reused for JWT generation.
Maintain the same session management approach used in src/middleware/session.ts
```

### Comparative Prompts

Ask Droid to compare approaches:

```bash
I need to implement file uploads. Compare these approaches:

Approach A: Direct upload to S3 with signed URLs
Approach B: Upload through Node.js server then to S3
Approach C: Use a service like Cloudinary

Consider:
- Security implications
- Cost efficiency
- Performance impact
- Scalability for 1M+ files
- Implementation complexity

Recommend the best approach for our use case and implement it.
```

### Educational Prompts

Ask for explanations along with implementation:

```bash
Create an authentication middleware that validates JWT tokens.
As you implement, please explain:
1. How JWT token structure works
2. What each security check prevents
3. Why we verify the signature before the payload
4. How token refresh attacks are prevented
5. Best practices for token storage and transmission

Add detailed comments explaining each security measure.
```

## Conclusion: Mastering Droid Prompt Engineering

Effective prompt engineering for Factory Droid is about treating the AI as a highly capable but explicit team member. The key principles are:

1. **Specificity Over Ambiguity**: Clear, detailed requests yield accurate implementations
2. **Context Richness**: Provide Droid with the same context you'd give a human developer
3. **Pattern Awareness**: Reference existing code patterns and conventions
4. **Iterative Refinement**: Start basic, enhance incrementally
5. **Success Definition**: Clearly define what "done" looks like

By mastering these prompt engineering techniques, you'll unlock Droid's full potential as an autonomous development partner, dramatically accelerating your full-stack development workflow.

The best Droid prompts read like clear technical specifications—they describe what to build, how it should work, constraints to consider, and how to verify success. Treat each prompt as a mini-specification document, and Droid will repay you with consistently high-quality, contextually-aware implementations.
