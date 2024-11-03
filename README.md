# Automated Job Search Assistant

An intelligent job search automation tool that helps streamline your job hunting process by automating search, analysis, and document generation while maintaining high quality and personalization.

## How It Works

The system operates in several key stages:

### 1. Job Search Planning
- Analyzes your profile and preferences from `user_context.json` and `user_want.md`
- Generates intelligent search queries based on your target roles and skills
- Uses Serper API to perform web searches for job listings

### 2. Job Scraping & Processing
- Scrapes job listings using a robust multi-tier approach:
  - Basic scraping with rotating user agents
  - ScrapeOps proxy service for protected sites
  - Automatic retry with exponential backoff
- Stores results in SQLite database (`jobs.db`)
- Tracks domain difficulty levels to optimize scraping strategy

### 3. Job Analysis
- Uses LLMs (Claude/GPT) to analyze job descriptions
- Scores relevance against your profile
- Identifies key requirements and pain points
- Filters based on your preferences

### 4. Document Generation
- Creates customized resumes using LaTeX
- Generates tailored cover letters
- Adapts content based on job requirements
- Uses professional templates for consistent formatting

## Prerequisites

1. Python 3.8+
2. Poetry (Python package manager)
3. pdflatex (for PDF generation)
4. Required API keys:
   - Anthropic API key (for Claude models)
   - OpenAI API key (for GPT models)
   - ScrapeOps API key (for web scraping)
   - Serper API key (for search functionality)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Install Poetry if not already installed:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install project dependencies:
```bash
poetry install
```

4. Install pdflatex to convert LaTeX documents to PDF:
   - Follow the installation guide for your operating system at:
   https://gist.github.com/rain1024/98dd5e2c6c8c28f9ea9d

5. Set up environment variables:
Create a `.env` file in the project root:
```
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
SCRAPEOPS_API_KEY=your_scrapeops_key
SERPER_API_KEY=your_serper_key
```

## Configuration

1. Create your user profile:
```bash
cp job_research/user_context_example.json job_research/user_context.json
```
Edit `user_context.json` with your:
- Personal information
- Professional experience
- Education
- Skills
- Projects
- Preferences

2. Define your job preferences:
```bash
cp job_research/user_want_example.md job_research/user_want.md
```
Edit `user_want.md` to specify:
- Desired role types
- Industry preferences
- Must-have requirements
- Deal-breakers

## Usage

### 1. Complete Job Search Workflow
```python
from job_research.main import JobSearchAssistant

# Initialize with your profile
assistant = JobSearchAssistant(
    "user_context.json",
    "user_want.md",
    verbose=True,  # Enable detailed logging
    max_workers=1,  # Number of concurrent workers
    query_limit=5   # Max search results per query
)

# Run full workflow
assistant.run()

# Check API costs
print(f"Total cost: ${assistant.get_cost()}")
```

### 2. Process Specific Time Period
```python
# Process jobs from specific date
assistant.process_descriptions('2024/07/30')
```

### 3. Score Existing Jobs
```python
# Score jobs in database
assistant.score_jobs()
```

### 4. Generate Application Documents
```python
# From database
assistant.create_outputs_from_db(job_id)

# Manual input
assistant.create_outputs_from_params(
    title="Senior Software Engineer",
    company="TechCorp",
    description="Job description..."
)
```

## Database Schema

### jobs table
- id: Primary key
- is_relevant: Boolean indicating job relevance
- url: Job posting URL
- title: Job title
- description: Full job description
- score: Relevance score (0-10)
- is_valid: Validation status
- documents_path: Path to generated documents
- location: Job location
- salary: Salary information
- company: Company name
- date: Processing date

### known_links table
- id: Primary key
- url: Processed URL
- is_job_page: Boolean indicating if URL is job posting
- date: Processing date

## Important Notes

1. **Manual Verification Required**
   - Always review generated documents before submission
   - Verify job details and requirements
   - Customize documents for each application

2. **API Costs**
   - The tool uses various AI models which incur costs
   - Monitor usage through `get_cost()`
   - Adjust query limits to control costs

3. **Rate Limiting**
   - Implements exponential backoff for scraping
   - Respects website rate limits
   - Uses proxy service for protected sites

4. **Document Customization**
   - Generated documents are starting points
   - Review and modify content
   - Ensure all information is accurate

## Credits

Resume and cover letter writing tips inspired by:
- [Resume Writing Tips](https://www.youtube.com/watch?v=7apj4sVvbro)
- [Cover Letter Guide](https://www.youtube.com/watch?v=pmnY5V16GSE)
- [Professional Document Writing](https://www.youtube.com/watch?v=Bip6BXtOQ_I)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
