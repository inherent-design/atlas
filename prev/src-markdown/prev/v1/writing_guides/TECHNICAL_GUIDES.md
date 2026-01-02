# Technical Documentation Writing Guide

This guide provides standards and best practices for creating high-quality technical documentation.

## Documentation Principles

Effective documentation should be:

1. **Educational** - Teach concepts, not just procedures
2. **Multi-perspective** - Cover different implementation approaches where applicable
3. **Practical** - Include concrete examples and implementation details
4. **Visual** - Use diagrams to illustrate complex relationships
5. **Progressive** - Start with fundamentals and build to advanced techniques

## Content Structure

### Guide Organization

Structure guides using this framework:

1. **Introduction** (2-3 paragraphs)
   - Hook the reader with a compelling question or scenario
   - Brief overview of the topic and its importance
   - Preview of implementation approaches

2. **Conceptual Overview** (1-2 pages)
   - Visual diagram of system/component relationships
   - Clear explanation of key concepts
   - Layered approach that separates components

3. **Step-by-Step Implementation** (3-5 pages)
   - Process broken into clear, numbered steps
   - Each step should include both explanation and code
   - Side-by-side comparison of different implementation approaches

4. **Advanced Techniques** (1-2 pages)
   - Build on the basics to show more complex implementations
   - Include practical code examples
   - Explain when and why to use these techniques

5. **Troubleshooting** (0.5-1 page)
   - Address common issues and their solutions
   - Include typical error messages and their meaning
   - Tips for debugging

6. **Conclusion** (1-2 paragraphs)
   - Summarize key points
   - Connect to broader concepts
   - Suggest related topics to explore

### File Naming and Location

- Organize guides in topical subdirectories
- Use numbered prefixes for sequential content: `01-topic-name.md`
- Include a `README.md` in each directory to explain its contents

## Writing Style Guidelines

### Tone and Voice

- Use a friendly, conversational tone
- Address the reader directly with "you" statements
- Include occasional rhetorical questions to engage the reader
- Balance technical accuracy with accessibility
- Use humor sparingly and appropriately

### Paragraphs and Sentences

- Keep paragraphs focused on one main idea (3-5 sentences)
- Vary sentence length but favor clarity over complexity
- Use active voice whenever possible
- Break complex processes into bulleted or numbered lists

### Code Examples

- Include full, working code examples (not just snippets)
- Annotate code with inline comments for key points
- Use consistent formatting and naming conventions
- Place code in appropriate markdown code blocks with language specified

## Visual Elements

### Diagrams

- Use diagrams to visualize systems and relationships
- Maintain a consistent color scheme across all diagrams
- Keep diagrams simple and focused on the main concepts
- Use clear, descriptive labels for nodes and relationships
- Include a brief explanation of the diagram in the text

### Images and Screenshots

- Use screenshots sparingly and only when they add significant value
- Annotate screenshots to highlight important elements
- Ensure images are clear, focused, and appropriately sized
- Include alt text for accessibility

## Technical Accuracy Requirements

### Version Compatibility

- Clearly indicate target versions for all technical content
- Note when a feature is version-specific
- Prefer newer APIs and patterns over deprecated ones

### Code Testing

- All code examples must be tested and functional
- Include import statements for non-obvious classes
- Follow language-specific best practices
- Ensure paths, filenames, and namespaces are consistent

### External Resources

- Link to official documentation when appropriate
- Include references to useful tools and resources
- Use consistent link formatting

## Review Checklist

Before submitting documentation, check that it:

- [ ] Follows the content structure outlined above
- [ ] Uses the correct tone and writing style
- [ ] Includes appropriate diagrams with consistent styling
- [ ] Provides complete, tested code examples
- [ ] Balances different implementation approaches
- [ ] Progresses from basic concepts to advanced techniques
- [ ] Includes troubleshooting information
- [ ] Has been proof-read for accuracy and clarity
- [ ] Uses proper Markdown formatting
- [ ] Contains appropriate links to related documentation

By following these guidelines, you'll create documentation that is consistent, accessible, and valuable to readers of varying experience levels.
