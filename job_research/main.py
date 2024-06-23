from concurrent.futures import ThreadPoolExecutor
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
from pathlib import Path

class JobSearchAssistant:
    def __init__(self, user_context_file, verbose=False, max_workers = None, skip_domains=[], output_dir = "./output_dir"):
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
        with open(user_context_file, "r") as file:
            self.user_context = json.load(file)
        self.job_search_plan = []
        self.initial_links = []
        self.scraper = Scraper(scrape_api_key)
        self.MAX_WORKERS = max_workers or os.cpu_count() / 2
        self.jobs_descriptions = set()
        self.domain_of_interest = ""
        self.verbose = verbose
        self.skip_domains = skip_domains
        self.output_dir = output_dir

    def verbose_print(self, msg):
        if self.verbose:
            print(msg)

    def url_exists_jobs(self, url):
        self.c.execute("SELECT COUNT(*) FROM jobs WHERE url = ?", (url,))
        count = self.c.fetchone()[0]
        return count > 0

    def add_job(self, job_details):
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
        if not self.url_exists_jobs(id):
            print(f"The id '{id}' does not exist in the database.")
            return

        self.c.execute('''UPDATE jobs SET score = ? WHERE id = ?''', (score, id))
        self.conn.commit()
        print(f"Score for id '{id}' updated to {score}.")

    def update_job(self, url, **kwargs):
        if not self.url_exists_jobs(url):
            print(f"The URL '{url}' does not exist in the database.")
            return

        set_values = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = tuple(kwargs.values())
        
        query = f"UPDATE jobs SET {set_values} WHERE url = ?"
        self.c.execute(query, (*values, url))
        self.conn.commit()

    def url_exists_knowns_links(self, url):
        self.c.execute("SELECT COUNT(*) FROM known_links WHERE url = ?", (url,))
        count = self.c.fetchone()[0]
        return count > 0

    def get_is_job_page(self, url):
        self.c.execute("SELECT is_job_page FROM known_links WHERE url = ?", (url,))
        result = self.c.fetchone()
        if result:
            return bool(result[0])  # Convert integer to boolean
        else:
            return None

    def add_known_link(self, url, is_job_page):
        current_datetime = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        self.c.execute('''INSERT INTO known_links (url, is_job_page, date) VALUES (?, ?, ?)''', (url, is_job_page, current_datetime))
        self.conn.commit()
        print("Link added to the database.")


    def get_jobs_descriptions(self):
        self.c.execute("SELECT url FROM known_links WHERE is_job_page = 1")
        rows = self.c.fetchall()
        lst = [row[0] for row in rows]
        lst.reverse()
        return lst

    def get_jobs_to_score(self):
        self.c.execute("SELECT url, description FROM jobs WHERE is_relevant = 1")
        rows = self.c.fetchall()
        lst = [(row[0], row[1]) for row in rows]
        lst.reverse()
        return lst

    # Create an agent that plans on what and where (which website) to search, given the user's context
    def plan_job_search(self):
        prompt = PLAN_JOB_SEARCH_PROMPT.replace("{{user_context}}", json.dumps(self.user_context))
        response = query_llm(prompt, model="sonet")
        self.domain_of_interest = search_for_tag(response, "domain_of_interest")
        res = search_for_tag(response, "query_list").replace('\n', '')
        query_list = []
        if res:
            query_list = [query.strip(' "') for query in res.split(',')]
            self.verbose_print(f"Extracted Query List: {query_list}")
        else:
            raise ValueError("Could not find <query_list> tag in job search plan")
        self.job_search_plan = query_list
        return query_list

    def next_page_finder(self, url:str) -> str:
        prompt = NEXT_PAGE_FINDER_PROMPT
        prompt_copy = prompt.replace("{{URL}}", url)
        response = query_llm(prompt_copy, "sonet")
        self.verbose_print(response["response"])
        res = search_for_tag(response, "result").strip()
        if res == 'No "next page" link found on this page.' or res == url:
            res = None
        return res

    def is_url_job_description(self, url:str) -> bool:
        if self.url_exists_knowns_links(url):
            self.verbose_print(f"url is in db : {url}")
            val = self.get_is_job_page(url)
            self.verbose_print(f"value : {val}")
            return val
        else:
            self.verbose_print(f"url is not in db. analysing : {url}")
            prompt = IS_URL_JOB_DESCRIPTION_PROMPT
            prompt_copy = prompt.replace("{{URL}}", url)
            response = query_llm(prompt_copy, "haiku")
            self.verbose_print(response["response"])
            res = search_for_tag(response, "answer").replace("\n", "")
            is_job_page = "Job Description" in res
            self.verbose_print(f"adding url in db : {is_job_page}, {url}")
            self.add_known_link(url, is_job_page)
            return is_job_page


    def get_domain_name(self, url):
        domain = urlparse(url).netloc
        domain_parts = domain.split('.')
        domain = '.'.join(domain_parts[-2:]) if len(domain_parts) > 2 else domain
        return domain

    def fix_url(self, link, url_src):
        domain = self.get_domain_name(url_src)
        if domain not in link:
            link = url_src.split(domain)[0] + domain + link
        return link

    def get_links(self, content:str, url_src: str):
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
                response = query_llm(prompt_copy)
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
        response = query_llm(prompt_copy, "haiku")
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
        prompt = prompt.replace("{{USER_CONTEXT}}", json.dumps(self.user_context))
        prompt = prompt.replace("{{JOB_DESCRIPTION}}", job["description"])
        response = query_llm(prompt)
        self.verbose_print(response["response"])
        res = search_for_tag(response, "answer")
        return res == "relevant"

    def score_description(self, desc):
        prompt = JOB_SCORE_PROMPT.replace("{{DOMAIN_OF_COMPETENCE}}", self.domain_of_interest)
        prompt = prompt.replace("{{USER_CONTEXT}}", json.dumps(self.user_context))
        prompt = prompt.replace("{{JOB_DESCRIPTION}}", desc)
        response = query_llm(prompt)
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

    def process_job_description(self, url):
        if not self.url_exists_jobs(url):
            content = self.scraper.retry_with_backoff(url)
            if type(content) == list :
                print("content is list:")
                print(content)
                res = None
            else:
                soup = BeautifulSoup(content, 'html.parser')
                for element in soup(["script", "style"]):
                    element.extract()
                text = soup.get_text()
                res = self.format_text_to_markdown(text)
            if res == None:
                print(f"no info could be extracted from {url}")
                res = {
                    'url' : url,
                    'title' : "No title",
                    'description' : 'No description',
                    "is_relevant" : False
                }
            else:
                res["url"] = url
                res["is_relevant"] = self.is_job_relevant(res)
                self.verbose_print(f'is relevant : {res["is_relevant"]}')
            self.add_job(res)

    def process_descriptions(self):
        jobs = self.get_jobs_descriptions()
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
                res = search_serper(query)
                for result in res:
                    link = result['link']
                    if not any(r['link'] == link for r in all_res):
                        all_res.append(result)
            self.initial_links = all_res
            print(f'Got {len(self.initial_links)} to process')
            self.process_initial_links()
            print('all initial links are processed!')
            #self.process_descriptions()

    def generate_cover_letter(self, job_desc: json) -> bytes:
        # Step 1: Get pain points
        prompt = GET_PAIN_POINTS_PROMPT.replace("{{job_desc}}", json.dumps(job_desc))
        response = query_llm(prompt)
        pain_points = search_for_tag(response, "pain_points")
        job_desc['challengesAndPainPoints'] = pain_points

        # Step 2: Connect with the reader
        prompt = CONNECT_WITH_READER_PROMPT.replace("{{job_desc}}", json.dumps(job_desc))
        prompt = prompt.replace("{{user_info}}", json.dumps(self.user_context))
        response = query_llm(prompt)
        hook = search_for_tag(response, "hook")
        cover_letter['hook'] = hook

        # Step 3: Write cover letter
        prompt = WRITE_COVER_LETTER_PROMPT.replace("{{job_desc}}", json.dumps(job_desc))
        prompt = prompt.replace("{{user_info}}", json.dumps(self.user_context))
        prompt = prompt.replace("{{cover_letter}}", json.dumps(cover_letter))
        response = query_llm(prompt)
        cover_letter = search_for_tag(response, "cover_letter")

        print(json.dumps(cover_letter))
        print("end test")

        # Convert cover letter to PDF (assuming a function convert_to_pdf exists)
        #cover_letter_pdf = convert_to_pdf(cover_letter)
        #return cover_letter_pdf

    def create_resume_cover_letter(self, job_desc: json, dir_name: str):
        # Create the directory
        output_path = Path(self.output_dir) / dir_name
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate resume and cover letter
        resume_content = self.generate_resume(job_desc)
        cover_letter_content = self.generate_cover_letter(job_desc)

        # Save the resume and cover letter as PDF
        resume_file = output_path / "resume.pdf"
        cover_letter_file = output_path / "cover_letter.pdf"

        with open(resume_file, "wb") as f:
            f.write(resume_content)

        with open(cover_letter_file, "wb") as f:
            f.write(cover_letter_content)

    def run(self):
        self.plan_job_search()
        self.apply_job_search_plan()


    def create_outputs_from_db(self, id):
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
        
        # Generate cover letter
        cover_letter = self.generate_cover_letter(job_json)
        
        # Create a directory for outputs
        dir_name = f"job_{id}"
        self.create_resume_cover_letter(job_json, dir_name)
        
        print(f"Outputs created for job {id} in directory {dir_name}")

USER_CONTEXT_FILE = os.path.join(os.path.dirname(__file__), "user_context.json")

assistant = JobSearchAssistant(USER_CONTEXT_FILE, verbose=True, max_workers=1, skip_domains=[])
#assistant.process_descriptions()
assistant.score_jobs()
#assistant.plan_job_search()

