#from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import json
from llm import query_llm, search_for_tag
from serper_tool import search_serper
from prompts import *
from scraper import Scraper
from dotenv import load_dotenv
import os
import sqlite3
from urllib.parse import urlparse
import datetime
import numpy as np
import datetime

class JobSearchAssistant:
    """
    Job Search Assistant Module

    This module provides an automated job search and application document generation system.
    It handles the entire workflow from finding jobs to creating application materials.

    Core Features:
    1. Automated Job Search:
       - Uses LLMs to create intelligent search queries
       - Scrapes job postings from various websites
       - Stores results in SQLite database

    2. Job Analysis:
       - Determines job relevance to user's profile
       - Scores job matches
       - Extracts key information (salary, location, etc.)

    3. Document Generation:
       - Creates customized resumes
       - Generates tailored cover letters
       - Outputs both LaTeX and PDF formats

    Database Schema:
    - jobs: Stores job postings and analysis
    - known_links: Tracks processed URLs to avoid duplicates

    Args:
        user_context_file (str): Path to JSON file containing user profile/experience
        user_want_file (str): Path to markdown file describing job search criteria
        verbose (bool): Enable detailed logging output
        max_workers (int): Max concurrent workers for processing
        skip_domains (list): List of domains to exclude from search
        output_dir (str): Directory for generated documents
        query_limit (int): Maximum search results per query
        date (str): Filter date in YYYY/MM/DD format
    """
    def __init__(self, user_context_file, user_want_file, verbose=False, max_workers = None, skip_domains=[], output_dir = "./output_dir", query_limit = 5, date=''):
        self.conn = sqlite3.connect('jobs.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS jobs (
                                id INTEGER PRIMARY KEY,
                                is_relevant INTEGER,
                                url TEXT NOT NULL,
                                title TEXT NOT NULL,
                                description TEXT NOT NULL,
                                score INTEGER,
                                is_valid INTEGER,
                                documents_path TEXT,
                                location TEXT,
                                salary TEXT,
                                company TEXT,
                                date TEXT
                            )''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS known_links (
                        id INTEGER PRIMARY KEY,
                        url TEXT NOT NULL,
                        is_job_page INTEGER,
                        date TEXT
                    )''')
        self.conn.commit()
        load_dotenv()
        scrape_api_key = os.getenv('SCRAPEOPS_API_KEY')
        with open(user_context_file, "r", encoding="utf-8") as file:
            self.user_context = json.load(file)
        with open(user_want_file, "r", encoding="utf-8") as file:
            self.user_want = file.read()
        self.job_search_plan = []
        self.initial_links = []
        self.scraper = Scraper(scrape_api_key)
        self.MAX_WORKERS = max_workers or os.cpu_count() / 2
        self.jobs_descriptions = set()
        self.domain_of_interest = ""
        self.verbose = verbose
        self.skip_domains = skip_domains
        self.output_dir = output_dir
        self.QUERY_LIMIT = query_limit
        if date == '':
            date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y/%m/%d')
        assert len(date) == 10 and date.count('/') == 2
        self.date = date
        self.cost = 0

    def get_cost(self):
        """Return the total cost of LLM API calls made during execution."""
        return self.cost

    def query_llm(self, prompt, model="gpt-4o-mini"):
        """
        Query the LLM with given prompt and model, tracking costs.
        
        Args:
            prompt: The prompt to send to the LLM
            model: The model to use (default: gpt-4o-mini)
            
        Returns:
            dict: The LLM response containing the generated text and metadata
        """
        response = query_llm(prompt, model)
        self.cost += response["cost"]
        return response

    def verbose_print(self, msg):
        """
        Print message if verbose mode is enabled.
        
        Args:
            msg: Message to print
        """
        if self.verbose:
            print(msg)

    def url_exists_jobs(self, url):
        """
        Check if a URL already exists in the jobs table.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if URL exists, False otherwise
        """
        self.c.execute("SELECT COUNT(*) FROM jobs WHERE url = ?", (url,))
        count = self.c.fetchone()[0]
        return count > 0

    def add_job(self, job_details):
        """
        Add a new job posting to the database.
        
        Args:
            job_details: Dictionary containing job information including:
                        url, title, description, salary, location, company,
                        is_relevant, is_valid, documents_path, score
        """
        url = job_details.get('url')
        title = job_details.get('title')
        description = job_details.get('description')
        salary = job_details.get('salary')
        location = job_details.get('location')
        company = job_details.get('company')
        is_relevant = job_details.get('is_relevant')
        is_valid = job_details.get('is_valid')
        documents_path = job_details.get('documents_path')
        score = job_details.get('score')
        datenow = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")

        if not url or not title or not description:
            print("URL, title, and description are required fields.")
            return
        if self.url_exists_jobs(url):
            print(f"The URL '{url}' already exists in the database.")
            return
        self.c.execute('''INSERT INTO jobs (is_relevant, url, title, description, score, is_valid, documents_path, location, salary, company, date) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (is_relevant, url, title, description, score, is_valid, documents_path, location, salary, company, datenow))
        self.conn.commit()
        print("Job added to the database.")

    def update_score(self, id, score):
        """
        Update the score for a job posting in the database.
        
        Args:
            id: The job posting ID
            score: The new score value
        """
        if not self.url_exists_jobs(id):
            print(f"The id '{id}' does not exist in the database.")
            return

        self.c.execute('''UPDATE jobs SET score = ? WHERE id = ?''', (score, id))
        self.conn.commit()
        print(f"Score for id '{id}' updated to {score}.")

    def update_job(self, url, **kwargs):
        """
        Update multiple fields for a job posting in the database.
        
        Args:
            url: The job posting URL
            **kwargs: Field names and values to update
        """
        if not self.url_exists_jobs(url):
            print(f"The URL '{url}' does not exist in the database.")
            return

        set_values = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())
        
        query = f"UPDATE jobs SET {set_values} WHERE url = ?"
        self.c.execute(query, (*values, url))
        self.conn.commit()

    def url_exists_knowns_links(self, url):
        """
        Check if a URL exists in the known_links table.
        
        Args:
            url: The URL to check
            
        Returns:
            bool: True if URL exists, False otherwise
        """
        self.c.execute("SELECT COUNT(*) FROM known_links WHERE url = ?", (url,))
        count = self.c.fetchone()[0]
        return count > 0

    def get_is_job_page(self, url):
        """
        Get the is_job_page status for a URL from known_links table.
        
        Args:
            url: The URL to check
            
        Returns:
            bool|None: True if job page, False if not, None if URL not found
        """
        self.c.execute("SELECT is_job_page FROM known_links WHERE url = ?", (url,))
        result = self.c.fetchone()
        if result:
            return bool(result[0])  # Convert integer to boolean
        else:
            return None

    def add_known_link(self, url, is_job_page):
        """
        Add a new URL to the known_links table.
        
        Args:
            url: The URL to add
            is_job_page: Boolean indicating if URL is a job posting
        """
        current_datetime = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        self.c.execute('''INSERT INTO known_links (url, is_job_page, date) VALUES (?, ?, ?)''', (url, is_job_page, current_datetime))
        self.conn.commit()
        print("Link added to the database.")


    def get_jobs_descriptions(self, date):
        """
        Get all job posting URLs from known_links after given date.
        
        Args:
            date: Date string in YYYY/MM/DD format
            
        Returns:
            list: URLs of job postings
        """
        self.c.execute(f"SELECT url FROM known_links WHERE is_job_page = 1 AND date >= '{date}'")
        rows = self.c.fetchall()
        lst = [row[0] for row in rows]
        lst.reverse()
        return lst

    def get_jobs_to_score(self):
        """
        Get all relevant jobs that need scoring.
        
        Returns:
            list: Tuples of (url, description) for relevant jobs
        """
        self.c.execute("SELECT url, description FROM jobs WHERE is_relevant = 1")
        rows = self.c.fetchall()
        lst = [(row[0], row[1]) for row in rows]
        lst.reverse()
        return lst

    # Create an agent that plans on what and where (which website) to search, given the user's context
    def plan_job_search(self):
        """
        Plan job search strategy based on user context.
        
        Uses LLM to:
        1. Analyze user profile and preferences
        2. Determine domain of interest
        3. Generate relevant search queries
        
        Returns:
            list: Search queries to use for job hunting
        """
        prompt = PLAN_JOB_SEARCH_PROMPT.replace("{{user_context}}", json.dumps(self.user_context))
        response = self.query_llm(prompt, model="gpt-4o-mini")
        self.verbose_print(f"plan job search response : {response}")
        self.domain_of_interest = search_for_tag(response, "domain_of_interest")
        res = search_for_tag(response, "query_list").replace('\n', '')
        query_list = []
        if res:
            query_list = [query.strip(' "') for query in res.split(',')]
            self.verbose_print(f"Extracted Query List: {query_list}")
        else:
            raise ValueError("Could not find <query_list> tag in job search plan. response: {response}")
        self.job_search_plan = query_list
        return query_list

    def next_page_finder(self, url:str) -> str:
        """
        Find the "next page" link on a job listing page.
        
        Args:
            url: URL of current job listing page
            
        Returns:
            str|None: URL of next page if found, None otherwise
        """
        prompt = NEXT_PAGE_FINDER_PROMPT
        prompt_copy = prompt.replace("{{URL}}", url)
        self.verbose_print(f"url scanned: {url}")
        response = self.query_llm(prompt_copy, "sonnet")
        self.verbose_print(response["response"])
        res = search_for_tag(response, "result").strip()
        if res == 'No "next page" link found on this page.' or res == url:
            res = None
        return res

    def is_url_job_description(self, url:str) -> bool:
        """
        Determine if a URL points to a job description page.
        
        Checks database first, then uses LLM to analyze if not found.
        
        Args:
            url: URL to analyze
            
        Returns:
            bool: True if URL is a job description page
        """
        if self.url_exists_knowns_links(url):
            self.verbose_print(f"url is in db : {url}")
            val = self.get_is_job_page(url)
            self.verbose_print(f"value : {val}")
            return val
        else:
            self.verbose_print(f"url is not in db. analysing : {url}")
            prompt = IS_URL_JOB_DESCRIPTION_PROMPT
            prompt_copy = prompt.replace("{{URL}}", url)
            response = self.query_llm(prompt_copy, "haiku")
            self.verbose_print(response["response"])
            res = search_for_tag(response, "answer").replace("\n", "")
            is_job_page = "Job Description" in res
            self.verbose_print(f"adding url in db : {is_job_page}, {url}")
            self.add_known_link(url, is_job_page)
            return is_job_page


    def get_domain_name(self, url):
        """
        Extract the base domain name from a URL.
        
        Args:
            url: Full URL to process
            
        Returns:
            str: Base domain (e.g., 'example.com')
        """
        domain = urlparse(url).netloc
        domain_parts = domain.split('.')
        domain = '.'.join(domain_parts[-2:]) if len(domain_parts) > 2 else domain
        return domain

    def fix_url(self, link, url_src):
        """
        Fix relative URLs by adding domain and protocol if needed.
        
        Args:
            link: URL to fix (may be relative)
            url_src: Source URL to get domain/protocol from
            
        Returns:
            str: Complete URL with domain and protocol
        """
        domain = self.get_domain_name(url_src)
        if domain not in link:
            link = url_src.split(domain)[0] + domain + link
        return link

    def get_links(self, content:str, url_src: str):
        """
        Extract job posting links from HTML content.
        
        Uses LLM to analyze each link and determine if it points to a job posting.
        Stores results in known_links database.
        
        Args:
            content: HTML content to parse
            url_src: Source URL for fixing relative links
            
        Returns:
            list: URLs that were identified as job postings
        """
        parsed = BeautifulSoup(content, "html.parser")
        links = []
        print("scanning links...")
        lst = parsed.find_all('a', href=True)
        nb = len(lst)
        for i, a in enumerate(lst):
            print(f"scanning {i}/{nb}")
            link = a.attrs['href']
            url_fixed = self.fix_url(link, url_src)
            if self.url_exists_knowns_links(url_fixed):
                self.verbose_print(f"url is in db : {url_fixed}")
                val = self.get_is_job_page(url_fixed)
                self.verbose_print(f"value : {val}")
                if (val):
                    links.append(link)
            else:
                element_data = {
                    'attrs': dict(a.attrs)
                }
                json_string = json.dumps(element_data)
                prompt_copy = GET_LINKS_PROMPT.replace("{{json_string}}", json_string)
                response = self.query_llm(prompt_copy)
                self.verbose_print(response["response"])
                res = search_for_tag(response, "answer")
                is_job_page = res == "yes"
                self.add_known_link(url_fixed, is_job_page)
                if (is_job_page):
                    links.append(link)
                print(f"{i}/{nb} scanned")
        return links
    
    def process_url(self, url):
        domain = self.get_domain_name(url)
        if any(skip in domain for skip in self.skip_domains):
            self.verbose_print(f"skipping as it is part of domain {domain} which is to skip : {url}")
            return
        self.verbose_print(f"start processing {url}")
        if self.is_url_job_description(url):
            self.verbose_print(f"end processing {url} : description")
            self.jobs_descriptions.add(url)
            self.process_job_description(url)
        else :
            self.verbose_print(f"end processing {url} : list")
            content = self.scraper.retry_with_backoff(url)
            for link in self.get_links(content, url):
                self.jobs_descriptions.add(link)
            self.verbose_print("searching next page")
            next_page_url = self.next_page_finder(url)
            self.verbose_print("got answer")
            if next_page_url:
                self.verbose_print("next page found")
                self.process_url(next_page_url)

    def process_initial_links(self):
        for result in self.initial_links:
            print(f'currently {len(self.jobs_descriptions)} jobs descriptions found.')
            self.process_url(result['link'])
#            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
#                futures = [executor.submit(self.process_url, result['link']) for result in self.initial_links]
#                for future in futures:
#                    future.result()
    
    def format_text_to_markdown(self, text):
        prompt = MARKDOWN_FORMATTER_PROMPT
        prompt_copy = prompt.replace("{{RAW_JOB_DESCRIPTION}}", text)
        response = self.query_llm(prompt_copy, "haiku")
        self.verbose_print(response["response"])
        desc = search_for_tag(response, "formatted_job_description")
        title = search_for_tag(response, "job_title")
        salary = search_for_tag(response, "salary")
        location = search_for_tag(response, "location")
        company = search_for_tag(response, "company")
        if "None" in (desc, title) :
            return None
        res = {
            "description": desc,
            "title": title,
            "salary": salary,
            "location": location,
            "company": company
        }
        return res

    def is_job_relevant(self, job:dict) -> bool:
        prompt = JOB_RELEVANCE_PROMPT.replace("{{DOMAIN_OF_INTEREST}}", self.domain_of_interest)
        prompt = prompt.replace("{{USER_WANT}}", json.dumps(self.user_want))
        prompt = prompt.replace("{{USER_CONTEXT}}", json.dumps(self.user_context))
        prompt = prompt.replace("{{JOB_DESCRIPTION}}", job["description"])
        # vote to determine if job is relevant
        all_res = []
        models = ["sonnet", "sonnet", "sonnet", "gpt-4o-mini", "gpt-4o-mini", "gpt-4o-mini"]
        for model in models:
            response = self.query_llm(prompt, model=model)
            self.verbose_print(response["response"])
            res = search_for_tag(response, "answer")
            all_res.append(1 if res == "relevant" else 0)
        mean = np.mean(all_res)
        self.verbose_print(f"VOTE : mean: {mean}, lst: {all_res}")
        return mean >= 0.5
        

    def score_description(self, desc):
        prompt = JOB_SCORE_PROMPT.replace("{{DOMAIN_OF_COMPETENCE}}", self.domain_of_interest)
        prompt = prompt.replace("{{USER_CONTEXT}}", json.dumps(self.user_context))
        prompt = prompt.replace("{{JOB_DESCRIPTION}}", desc)
        response = self.query_llm(prompt)
        self.verbose_print(response["response"])
        res = search_for_tag(response, "answer")
        return res

    def score_jobs(self):
        jobs = self.get_jobs_to_score()
        l = len(jobs)
        print(f"will process {l} jobs descriptions to score")
        for i, (id, desc) in enumerate(jobs):
            self.verbose_print(f'{i}/{l}')
            score = self.score_description(desc)
            self.update_score(id, score)
#            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
#                futures = [executor.submit(self.process_job_description, url) for url in self.jobs_descriptions]
#                for future in futures:
#                    future.result()
        print(f"{l} jobs descriptions succesfully processed.")       

    def _extract_job_content(self, content):
        """Extract clean text content from HTML, removing scripts and styles"""
        if isinstance(content, list):
            self.verbose_print("Content is list, cannot process")
            return None
            
        soup = BeautifulSoup(content, 'html.parser')
        for element in soup(["script", "style"]):
            element.extract()
        return soup.get_text()

    def _create_empty_job_result(self, url):
        """Create a default job result when extraction fails"""
        return {
            'url': url,
            'title': "No title",
            'description': 'No description',
            "is_relevant": False
        }

    def process_job_description(self, url):
        """
        Process a job posting URL to extract and analyze its content.
        
        Steps:
        1. Check if job already exists in database
        2. Fetch and clean HTML content
        3. Extract job details and format as markdown
        4. Determine job relevance
        5. Save to database
        """
        if self.url_exists_jobs(url):
            self.verbose_print(f"Job already exists: {url}")
            return

        # Fetch and process content
        content = self.scraper.retry_with_backoff(url)
        text = self._extract_job_content(content)
        
        if text is None:
            res = self._create_empty_job_result(url)
        else:
            res = self.format_text_to_markdown(text)
            if res is None:
                res = self._create_empty_job_result(url)
            else:
                res["url"] = url
                res["is_relevant"] = self.is_job_relevant(res)
                self.verbose_print(f'Job relevance: {res["is_relevant"]}')
        
        self.add_job(res)

    def process_descriptions(self, date):
        jobs = self.get_jobs_descriptions(date)
        l = len(jobs)
        print(f"will process {l} jobs descriptions")
        for i, url in enumerate(jobs):
            self.verbose_print(f'{i}/{l}')
            self.process_job_description(url)
#            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
#                futures = [executor.submit(self.process_job_description, url) for url in self.jobs_descriptions]
#                for future in futures:
#                    future.result()
        print(f"{l} jobs descriptions succesfully processed.")

    def apply_job_search_plan(self):
        if self.job_search_plan:
            all_res = []
            for query in self.job_search_plan:
                res = search_serper(query, self.QUERY_LIMIT)
                for result in res:
                    link = result['link']
                    if not any(r['link'] == link for r in all_res):
                        all_res.append(result)
            self.initial_links = all_res
            print(f'Got {len(self.initial_links)} to process')
            self.process_initial_links()
            print('all initial links are processed!')
            self.process_descriptions(self.date)

    def _identify_pain_points(self, job_desc: dict) -> str:
        """
        Extract key challenges and pain points from the job description.
        
        Uses LLM to analyze job description and identify:
        - Key business challenges
        - Technical pain points
        - Critical needs
        
        Args:
            job_desc: Dictionary containing job details
            
        Returns:
            str: Formatted list of identified pain points
        """
        prompt = GET_PAIN_POINTS_PROMPT.replace("{{job_desc}}", json.dumps(job_desc))
        response = self.query_llm(prompt, model="sonnet")
        return search_for_tag(response, "pain_points")

    def _generate_hook(self, job_desc: dict) -> str:
        """
        Create an engaging opening hook for the cover letter.
        
        Uses LLM to generate a personalized opening that:
        - Connects with the reader
        - Shows understanding of company needs
        - Highlights relevant experience
        
        Args:
            job_desc: Dictionary containing job details
            
        Returns:
            str: Opening paragraph for cover letter
        """
        prompt = CONNECT_WITH_READER_PROMPT.replace("{{job_desc}}", json.dumps(job_desc))
        prompt = prompt.replace("{{user_info}}", json.dumps(self.user_context))
        response = self.query_llm(prompt, model="sonnet")
        hook = search_for_tag(response, "hook")
        self.verbose_print(f"Hook length: {len(hook.split(' '))} words")
        return hook

    def _generate_body(self, job_desc: dict, cover_letter: dict) -> dict:
        """
        Generate the main content of the cover letter.
        
        Creates a structured cover letter with:
        - Professional background
        - Relevant achievements
        - Skills alignment
        - Cultural fit
        
        Args:
            job_desc: Dictionary containing job details
            cover_letter: Initial cover letter structure with hook
            
        Returns:
            dict: Complete cover letter content
        """
        prompt = WRITE_COVER_LETTER_PROMPT.replace("{{job_desc}}", json.dumps(job_desc))
        prompt = prompt.replace("{{user_info}}", json.dumps(self.user_context))
        prompt = prompt.replace("{{cover_letter}}", json.dumps(cover_letter))
        response = self.query_llm(prompt, model="sonnet")
        return json.loads(search_for_tag(response, "cover_letter"), strict=False)

    def _generate_latex(self, cover_letter: dict, output_path: str) -> str:
        """
        Convert cover letter content to LaTeX format and save to file.
        
        Steps:
        1. Load LaTeX template
        2. Format content for LaTeX
        3. Generate complete document
        4. Save to file
        
        Args:
            cover_letter: Dictionary with letter content
            output_path: Directory to save output
            
        Returns:
            str: Path to generated LaTeX file
        """
        prompt = LATEX_COVER_LETTER_PROMPT.replace("{{cover_letter}}", json.dumps(cover_letter))
        prompt = prompt.replace("{{user_info}}", json.dumps(self.user_context))
        
        template_path = os.path.join(os.path.dirname(__file__), "cover_template.tex")
        with open(template_path, "r", encoding="utf-8") as f:
            cover_latex_template = f.read()
        
        prompt = prompt.replace("{{latex_template}}", cover_latex_template)
        response = self.query_llm(prompt)
        cl_tex = search_for_tag(response, "cover_latex")
        
        cover_letter_tex_path = os.path.join(output_path, "cover_letter.tex")
        with open(cover_letter_tex_path, "w", encoding="utf-8") as f:
            f.write(cl_tex)
            
        return cover_letter_tex_path

    def _cleanup_latex_files(self, output_path: str):
        """
        Remove LaTeX auxiliary files after PDF generation.
        
        Removes common LaTeX temporary files:
        - .aux (auxiliary data)
        - .log (compilation log)
        - .out (hyperref data)
        
        Args:
            output_path: Directory containing LaTeX files
        """
        for ext in [".aux", ".log", ".out"]:
            aux_file = os.path.join(output_path, f"cover_letter{ext}")
            if os.path.exists(aux_file):
                os.remove(aux_file)

    def generate_cover_letter(self, job_desc: dict, output_path: str) -> str:
        """
        Generate a customized cover letter for a job application.
        
        Steps:
        1. Identify pain points from job description
        2. Generate engaging hook
        3. Create full cover letter content
        4. Convert to LaTeX and PDF
        
        Args:
            job_desc: Dictionary containing job details
            output_path: Directory to save output files
            
        Returns:
            Path to generated PDF file
        """
        # Extract pain points
        pain_points = self._identify_pain_points(job_desc)
        job_desc['challengesAndPainPoints'] = pain_points
        
        # Generate hook and initial structure
        hook = self._generate_hook(job_desc)
        cover_letter = {'hook': hook}
        
        # Generate full content
        cover_letter = self._generate_body(job_desc, cover_letter)
        self.verbose_print(f"Body length: {len(cover_letter['body'].split(' '))} words")
        
        # Convert to LaTeX and PDF
        tex_path = self._generate_latex(cover_letter, output_path)
        os.system(f"pdflatex -output-directory={output_path} {tex_path}")
        self._cleanup_latex_files(output_path)
        
        return os.path.join(output_path, "cover_letter.pdf")

    def _generate_summary_step(self, step_num: int, job_desc: dict, previous_result: dict = None) -> dict:
        """
        Generate a single step of the professional summary using LLM.
        
        Multi-step process to build resume summary:
        1. Professional adjectives
        2. Job title/field
        3. Experience statement
        4. Specialties
        
        Args:
            step_num: Current step number (1-4)
            job_desc: Dictionary containing job details
            previous_result: Results from previous steps
            
        Returns:
            dict: Generated content for current step
        """
        prompt_var = f"GENERATE_PROFESSIONAL_SUMMARY_STEP{step_num}_PROMPT"
        prompt = globals()[prompt_var].replace("{{job_desc}}", json.dumps(job_desc))
        prompt = prompt.replace("{{user_info}}", json.dumps(self.user_context))
        
        if previous_result:
            prompt = prompt.replace("{{previous_step}}", json.dumps(previous_result))
            
        response = self.query_llm(prompt, model="sonnet")
        result = json.loads(search_for_tag(response, "output"))
        self.verbose_print(f"Step {step_num} result: {json.dumps(result)}")
        return result

    def _save_professional_summary(self, summary: str, output_path: str):
        """
        Save the generated professional summary to a file.
        
        Args:
            summary: Generated professional summary text
            output_path: Directory to save output file
            
        Creates:
            professional_summary.txt in output directory
        """
        summary_file_path = os.path.join(output_path, "professional_summary.txt")
        with open(summary_file_path, "w", encoding="utf-8") as f:
            f.write(summary)

    def generate_resume(self, job_desc: dict, output_path: str):
        """
        Generate a professional resume summary through a multi-step LLM process.
        
        Steps:
        1. Generate professional adjectives
        2. Generate job title/field
        3. Generate experience statement
        4. Generate specialties
        5. Combine into final summary
        """
        # Generate each component
        step1_result = self._generate_summary_step(1, job_desc)
        step2_result = self._generate_summary_step(2, job_desc, step1_result)
        step3_result = self._generate_summary_step(3, job_desc, step2_result)
        step4_result = self._generate_summary_step(4, job_desc, step3_result)

        # Generate final summary
        prompt = GENERATE_PROFESSIONAL_SUMMARY_FINAL_PROMPT.replace("{{job_desc}}", json.dumps(job_desc))
        prompt = prompt.replace("{{user_info}}", json.dumps(self.user_context))
        prompt = prompt.replace("{{previous_steps}}", json.dumps(step4_result))
        response = self.query_llm(prompt, model="sonnet")
        professional_summary = search_for_tag(response, "professional_summary")
        
        self.verbose_print(f"Generated professional summary:\n{professional_summary}")
        self._save_professional_summary(professional_summary, output_path)

    def generate_resume_latex(self, professional_summary: str, job_desc: dict, output_path: str) -> str:
        """
        Generate LaTeX resume from professional summary and job details.
        
        Steps:
        1. Load resume template
        2. Format content for LaTeX
        3. Generate complete document
        4. Compile to PDF
        5. Clean up auxiliary files
        
        Args:
            professional_summary: Generated summary text
            job_desc: Dictionary containing job details
            output_path: Directory to save output
            
        Returns:
            str: Path to generated PDF file
        """
        prompt = LATEX_RESUME_PROMPT.replace("{{professional_summary}}", professional_summary)
        prompt = prompt.replace("{{user_info}}", json.dumps(self.user_context))
        prompt = prompt.replace("{{job_desc}}", json.dumps(job_desc))
        with open(os.path.join(os.path.dirname(__file__), "resume_template.tex"), "r", encoding="utf-8") as f:
            resume_latex_template = f.read()
        resume_latex_template = resume_latex_template.replace("{{professional_summary}}", professional_summary)
        prompt = prompt.replace("{{latex_template}}", resume_latex_template)
        response = self.query_llm(prompt)
        resume_tex = search_for_tag(response, "resume_latex")

        # Save LaTeX file
        resume_tex_path = os.path.join(output_path, "resume.tex")
        with open(resume_tex_path, "w", encoding="utf-8") as f:
            f.write(resume_tex)

        # Convert LaTeX to PDF
        os.system(f"pdflatex -output-directory={output_path} {resume_tex_path}")

        # Clean up auxiliary files
        for ext in [".aux", ".log", ".out"]:
            aux_file = os.path.join(output_path, f"resume{ext}")
            if os.path.exists(aux_file):
                os.remove(aux_file)

        return os.path.join(output_path, "resume.pdf")

    def create_resume_cover_letter(self, job_desc: dict, dir_name: str) -> str:
        """
        Create complete application package with resume and cover letter.
        
        Steps:
        1. Create output directory
        2. Generate resume content
        3. Generate cover letter
        4. Create PDF versions
        
        Args:
            job_desc: Dictionary containing job details
            dir_name: Name for output directory
            
        Returns:
            str: Path to output directory containing documents
        """
        # Create the directory
        output_path = os.path.join(self.output_dir, dir_name)
        os.makedirs(output_path, exist_ok=True)

        # Generate resume and cover letter
        resume_content = self.generate_resume(job_desc, output_path)
        cover_letter_content = self.generate_cover_letter(job_desc, output_path)

        # Save the resume and cover letter as PDF
        resume_file = os.path.join(output_path, "resume.pdf")
        cover_letter_file = os.path.join(output_path, "cover_letter.pdf")
        return output_path

    def run(self):
        self.plan_job_search()
        self.apply_job_search_plan()


    def create_outputs_from_db(self, id: int):
        """
        Generate application documents from database job entry.
        
        Steps:
        1. Fetch job details from database
        2. Create output directory
        3. Generate resume and cover letter
        
        Args:
            id: Database ID of job posting
        """
        # Fetch job details from the database
        self.c.execute("SELECT * FROM jobs WHERE id = ?", (id,))
        job = self.c.fetchone()
        
        if job is None:
            print(f"No job found with id {id}")
            return
        
        # Create a JSON object with all job information
        job_json = {
            "id": job[0],
            "is_relevant": bool(job[1]),
            "url": job[2],
            "title": job[3],
            "description": job[4],
            "score": job[5],
            "is_valid": bool(job[6]),
            "documents_path": job[7],
            "location": job[8],
            "salary": job[9],
            "company": job[10],
            "date": job[11]
        }
        # Create a directory for outputs
        dir_name = f"{id}_{job_json['title']}_{job_json['company']}"
        dir_name = dir_name.replace(' ', '_')
        
        self.create_resume_cover_letter(job_json, dir_name)
        
        print(f"Outputs created for job {id} in directory {dir_name}")

    def create_outputs_from_params(self, title: str, company: str, description: str) -> str:
        """
        Generate application documents from manual input.
        
        Steps:
        1. Create job details dictionary
        2. Generate documents in named directory
        3. Open output directory
        
        Args:
            title: Job title
            company: Company name
            description: Job description text
            
        Returns:
            str: Path to output directory
        """
        # Create a JSON object with the provided information
        job_json = {
            "title": title,
            "company": company,
            "description": description
        }
        
        # Create a directory for outputs
        dir_name = f"{title}_{company}"
        dir_name = dir_name.replace(' ', '_')
        
        output_path = self.create_resume_cover_letter(job_json, dir_name)
        
        print(f"Outputs created for job '{title}' at '{company}' in directory {dir_name}")
        
        print(f"Opening file explorer at: {output_path}")
        os.startfile(output_path)
        return output_path

USER_CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "user_context.json")
USER_WANT_FILE = os.path.join(os.path.dirname(__file__), "user_want.md")

assistant = JobSearchAssistant(USER_CONTEXT_FILE, USER_WANT_FILE, verbose=True, max_workers=1, skip_domains=[], date='2024/07/30')
if __name__ == "__main__":
    try:
        # Example 1: Complete job search workflow
        # Searches for jobs, processes descriptions, and scores matches
        # assistant.run()

        # Example 2: Process specific job descriptions
        # Process job postings from a certain date
        # assistant.process_descriptions('2024/07/30')

        # Example 3: Score existing jobs
        # Score jobs already in database against user profile
        # assistant.score_jobs()

        # Example 4: Generate application documents
        # Create resume and cover letter for a specific job
        # assistant.create_outputs_from_db(227)

        # Example 5: Generate documents from manual input
        # assistant.create_outputs_from_params(
        #     title="Senior Software Engineer",
        #     company="TechCorp",
        #     description="Looking for an experienced developer..."
        # )

        # Run your chosen example here:
        assistant.process_descriptions('2024/07/30')
    finally:
        print(f"Total API cost: {assistant.get_cost()} $USD")
