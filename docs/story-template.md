# User Story Template

## Story Title: [Brief, descriptive title]

### User Story
As a [type of user], I want [goal/desire] so that [benefit/value].

### Business Value
[Explanation of why this story matters to the user and business]

### Acceptance Criteria
- [ ] **Given** [initial context], **When** [action taken], **Then** [expected outcome]
- [ ] **Given** [context], **When** [action], **Then** [outcome]
- [ ] [Additional criteria as bullet points]

### Technical Notes
- [Implementation details for developers]
- [Architecture decisions]
- [Dependencies or constraints]

### Definition of Done
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing (minimum 80% coverage)
- [ ] Integration tests cover main paths
- [ ] API documentation updated (if applicable)
- [ ] Error handling implemented
- [ ] Performance requirements met
- [ ] Security considerations addressed
- [ ] Code review completed
- [ ] Manual testing completed
- [ ] Deployment tested in staging environment

---

# Acceptance Criteria Writing Guidelines

## Format: Given-When-Then
Use the Gherkin format for clear, testable criteria:
- **Given**: The initial state or context
- **When**: The action or event that triggers the behavior
- **Then**: The expected outcome or result

## Example:
- [ ] **Given** a user has a portfolio with USD stocks, **When** they view the portfolio dashboard, **Then** the total value is displayed in NOK using current exchange rates

## Best Practices

### 1. Be Specific and Measurable
❌ "The system should be fast"
✅ "API responses should return within 200ms for 95% of requests"

### 2. Focus on User-Facing Behavior
❌ "Database query should use proper indexes"
✅ "Portfolio loading should complete within 2 seconds"

### 3. Include Edge Cases
- Empty states (no data)
- Error conditions
- Boundary values (minimum/maximum)
- Invalid inputs

### 4. Security Considerations
- Authentication requirements
- Authorization checks
- Input validation
- Data protection

### 5. Performance Requirements
- Response time expectations
- Concurrent user limits
- Data volume handling

## Story Sizing Guidelines

### Small (1-2 points)
- Single API endpoint
- Simple CRUD operations
- Minor UI changes
- Bug fixes

### Medium (3-5 points)
- Multiple related endpoints
- Complex business logic
- New UI components
- Integration with external APIs

### Large (8+ points)
- Major features spanning multiple components
- New architectural patterns
- Complex integrations
- Should be broken down into smaller stories

## Example Story Categories

### Backend API Stories
- Focus on data operations
- Include API documentation requirements
- Specify request/response formats
- Include error handling scenarios

### Frontend UI Stories
- Include mockups or wireframes
- Specify responsive behavior
- Include accessibility requirements
- Define user interaction flows

### Integration Stories
- Third-party API integrations
- Service-to-service communication
- Data synchronization
- Error recovery scenarios

### Infrastructure Stories
- Deployment pipeline changes
- Monitoring and alerting
- Performance optimization
- Security enhancements