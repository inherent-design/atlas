# Apify Actors MCP Integration

## Overview

The Apify Actors MCP integration provides access to a platform for cloud-based web scraping, data extraction, and automation capabilities. This integration allows Atlas to utilize Apify's ecosystem of ready-made solutions (actors) for various web automation tasks.

## Available Actors

The following Apify actors are configured and available for use:

### 1. Website Content Crawler (`apify/website-content-crawler`)

**Description**: Crawls websites and extracts content from pages in structured form.

**Capabilities**:
- Deep website crawling with configurable depth
- Content extraction in structured JSON format
- Support for pagination and dynamic content
- Handling of JavaScript-rendered websites

**When to Use**:
- For comprehensive website data extraction
- When needing to extract structured content from multiple pages
- For creating searchable knowledge bases from web content
- When building a mirror or archive of website content

**Usage Example**:
```
// Extract content from a blog with automatic discovery of related pages
{
  "startUrls": [{"url": "https://example.com/blog"}],
  "maxCrawlDepth": 3,
  "maxCrawlPages": 100
}
```

### 2. Instagram Scraper (`apify/instagram-scraper`)

**Description**: Extracts data from Instagram profiles, posts, and hashtags.

**Capabilities**:
- Collection of profile information (followers, following, bio)
- Extraction of post data (images, captions, likes, comments)
- Support for hashtag exploration
- Collection of comments and engagement metrics

**When to Use**:
- For social media research and analysis
- When tracking Instagram influencers or competitors
- For content discovery based on hashtags
- When collecting visual content for inspiration or research

**Usage Example**:
```
// Extract recent posts from a profile
{
  "usernames": ["natgeo"],
  "resultsLimit": 50,
  "includeComments": true
}
```

### 3. Instagram Reel Scraper (`apify/instagram-reel-scraper`)

**Description**: Specialized in extracting Instagram Reels content.

**Capabilities**:
- Extraction of Reels videos and metadata
- Collection of engagement metrics specific to Reels
- Support for trending Reels discovery
- Audio and caption extraction

**When to Use**:
- For short-form video content analysis
- When researching viral content and trends
- For competitor analysis in video content
- When collecting video inspiration or references

**Usage Example**:
```
// Extract trending Reels with specific hashtag
{
  "hashtags": ["travel"],
  "resultsLimit": 30
}
```

### 4. Google Maps Extractor (`compass/google-maps-extractor`)

**Description**: Extracts business data from Google Maps.

**Capabilities**:
- Business information extraction (name, address, contact details)
- Collection of reviews and ratings
- Support for geographic searches
- Category-based business discovery

**When to Use**:
- For local business research
- When compiling business directories
- For competitor analysis by location
- When planning location-based strategies

**Usage Example**:
```
// Extract restaurants in a specific area
{
  "searchTerms": ["restaurants"],
  "locationQuery": "Cambridge, MA",
  "maxResults": 50,
  "includeReviews": true
}
```

### 5. Reddit Scraper Lite (`trudax/reddit-scraper-lite`)

**Description**: Extracts posts and comments from Reddit.

**Capabilities**:
- Subreddit content extraction
- Post and comment collection
- Support for sorting by popularity or recency
- Text and media content extraction

**When to Use**:
- For community sentiment analysis
- When researching specific topics or interests
- For content discovery in specialized communities
- When collecting user feedback or opinions

**Usage Example**:
```
// Extract top posts from subreddit
{
  "subreddits": ["datascience"],
  "sort": "top",
  "timeFrame": "month",
  "maxItems": 50
}
```

### 6. YouTube Scraper (`streamers/youtube-scraper`)

**Description**: Extracts videos, channels, and metadata from YouTube.

**Capabilities**:
- Channel information extraction
- Video metadata collection (title, views, likes)
- Support for comment extraction
- Search results collection

**When to Use**:
- For video content research
- When analyzing YouTube creators or competitors
- For content discovery based on topics
- When collecting educational or reference material

**Usage Example**:
```
// Extract videos from a channel
{
  "channels": ["TED"],
  "maxResults": 30,
  "includeComments": true
}
```

## Integration with Atlas Framework

### Trimodal Approach

- **Bottom-Up**: Execute specific data extraction tasks with precise actor configuration
- **Top-Down**: Design comprehensive data collection strategies across multiple platforms
- **Holistic**: Integrate data from various sources for complete understanding of topics

### Knowledge Graph Application

Actors operations can be represented in the knowledge graph as:

- **Entities**: Data sources, platforms, content types, and extracted information
- **Relationships**: Platform connections, content relationships, and cross-platform patterns
- **Properties**: Engagement metrics, timestamps, and contextual attributes

## Decision Framework for Actor Selection

When multiple actors could address a task, use this decision framework:

1. **Content Type Priority**:
   - Text content → Website Content Crawler
   - Images → Instagram Scraper
   - Short videos → Instagram Reel Scraper
   - Location data → Google Maps Extractor
   - Discussion threads → Reddit Scraper
   - Long-form video → YouTube Scraper

2. **Platform Specificity**:
   - When targeting a specific platform, choose the specialized actor
   - When platform-agnostic, choose the most feature-rich actor for the content type

3. **Depth vs. Breadth**:
   - For deep analysis of limited sources → Platform-specific actors
   - For broad overview across many sources → Website Content Crawler

4. **Resource Efficiency**:
   - Consider execution time and processing requirements
   - For large-scale tasks, use more efficient specialized actors

## Best Practices

1. **Ethical Scraping**: Respect website terms of service, rate limits, and privacy considerations
2. **Query Precision**: Design specific, targeted queries to minimize unnecessary data collection
3. **Error Handling**: Implement proper handling for rate limits, blocked requests, and content changes
4. **Data Validation**: Verify the quality and consistency of extracted data
5. **Incremental Collection**: For large datasets, use incremental approaches rather than single large jobs
6. **Privacy Protection**: Handle personally identifiable information (PII) with appropriate safeguards
7. **Caching Strategy**: Implement intelligent caching to reduce redundant data collection