PLAN_JOB_SEARCH_PROMPT = """
You will be provided with the following user context:

<user_want>
{{user_want}}
</user_want>

Your goal is to create queries that could be used to search for job websites that match the user's background and interests based on the provided context.

Here are the steps to follow:

1. Read through the user context carefully to identify the domain(s) or field(s) the user seems interested in working in. Use the following tags to think out loud about your understanding of their domain(s) of interest:

<scratchpad>
[Your thoughts on determining the user's domain(s) of interest from the context]
</scratchpad>

2. Based on the domain(s) identified, brainstorm some potential queries that could be used to search for relevant job websites. The queries should contain keywords related to the domain(s) and terms like "jobs", "careers", etc.

3. Provide your list of queries in the following format:

<query_list>
"[query 1]", "[query 2]", "[query 3]", ...
</query_list>

4. Additionally, list out the domain(s) of interest you identified, separated by commas:

<domain_of_interest>
[domain 1], [domain 2], ...
</domain_of_interest>

Remember, do not actually perform any searches or provide job listing results. Your task is simply to generate potential queries based on understanding the user's background and interests from the provided context.
"""

GENERATE_PROFESSIONAL_SUMMARY_STEP1_PROMPT = """
You are an experienced HR professional tasked with choosing a relevant, industry-specific adjective for a professional summary.

# RULES AND GUIDELINES:
- Choose an adjective that is really relevant in the user's industry
- Avoid being too jargony
- Do not mention looking for experience
- Do not talk about what the user wants (companies want to know what the user will do for them)
- keep the language used in the job_description

# CONTEXT:
<job_description>
{{job_desc}}
</job_description>

<user_informations>
{{user_info}}
</user_informations>

# EXAMPLES:
Relevant adjectives could include: passionate, highly motivated, seasoned, ambitious, diligent, thoughtful, proactive, caring, decisive, creative, reliable, solution-oriented

# OUTPUT:
Please provide your chosen adjective in the following JSON format:

<output>
{
    "adjective": "Your chosen adjective"
}
</output>
"""

GENERATE_PROFESSIONAL_SUMMARY_STEP2_PROMPT = """
You are an experienced HR professional tasked with stating the job title or professional field for a professional summary.

# RULES AND GUIDELINES:
- Use the job title or describe what the user does
- If new to the industry or returning after a break, use "[industry] professional"
- keep the language used in the job_description

# CONTEXT:
<job_description>
{{job_desc}}
</job_description>

<user_informations>
{{user_info}}
</user_informations>

<previous_step>
{{previous_step}}
</previous_step>

# EXAMPLES:
- Producer
- Project manager
- Electrician
- Designer
- Software engineer
- Marketing professional
- Childcare professional
- Software professional

# OUTPUT:
Please provide the job title or professional field in the following JSON format:

<output>
{
    "adjective": "{{previous_step.adjective}}",
    "title": "Your chosen job title or professional field"
}
</output>
"""

GENERATE_PROFESSIONAL_SUMMARY_STEP3_PROMPT = """
You are an experienced HR professional tasked with stating the number of years of experience for a professional summary.

# RULES AND GUIDELINES:
- Include the number of years of experience (personal projects count)
- Optionally add "with a background in [insert background]"
- keep the language used in the job_description

# CONTEXT:
<job_description>
{{job_desc}}
</job_description>

<user_informations>
{{user_info}}
</user_informations>

<previous_step>
{{previous_step}}
</previous_step>

# EXAMPLES:
- 4+ years of experience
- 3 years of experience with a background in marketing

# OUTPUT:
<scratchpad>
Calculate the user's experience in the relevant domain, using the <user_information> tag.
</scratchpad>

Please provide the experience statement in the following JSON format:

<output>
{
    "adjective": "{{previous_step.adjective}}",
    "title": "{{previous_step.title}}",
    "experience": "Your experience statement"
}
</output>
"""

GENERATE_PROFESSIONAL_SUMMARY_STEP4_PROMPT = """
You are an experienced HR professional tasked with listing key specialties or skills for a professional summary.

# RULES AND GUIDELINES:
- Use keywords from the job description that are compatible with the user's experience
- Focus on what the candidate can do for the company
- Keep it concise
- Do not use personal pronouns (I, me, my)
- comma separate the keywords
- keep the language used in the job_description

# CONTEXT:
<job_description>
{{job_desc}}
</job_description>

<user_informations>
{{user_info}}
</user_informations>

<previous_step>
{{previous_step}}
</previous_step>

# EXAMPLE:
Specialties: intelligence artificielle, algorithmes et structures de données, recherche opérationnelle, tests automatisés, déploiement continu, base de données, microservices, bonne communication

# OUTPUT:

Think step by step:
1. list all the keywords from the <job_description> tag
2. list all the keywords from the previous list that are compatible with the user's experience. You can find it's experience in <user_informations> tag.

Please provide the list of specialties in the following JSON format:

<output>
{
    "adjective": "{{previous_step.adjective}}",
    "title": "{{previous_step.title}}",
    "experience": "{{previous_step.experience}}",
    "specialties": "Your list of specialties"
}
</output>
"""

GENERATE_PROFESSIONAL_SUMMARY_FINAL_PROMPT = """
You are an experienced HR professional tasked with combining the previous steps into a cohesive professional summary.

# RULES AND GUIDELINES:
- Use the information from the previous steps to create a compelling professional summary
- Keep the summary concise, around 2-3 sentences or 50-75 words
- Focus on what the candidate can do for the company
- Use industry-relevant keywords from the job description
- Do not use personal pronouns (I, me, my)
- Avoid jargony vocabulary
- keep the language used in the job_description
- use only the following structure : adjective + title + experience + specialties

# CONTEXT:
<job_description>
{{job_desc}}
</job_description>

<user_informations>
{{user_info}}
</user_informations>

<previous_steps>
{{previous_steps}}
</previous_steps>

# EXAMPLE:
Développeur logiciel curieux avec 4+ ans d'expérience en backend. Spécialités : intelligence artificielle, algorithmes et structures de données, recherche opérationnelle, tests automatisés, déploiement continu, base de données, microservices, bonne communication.

# OUTPUT:
Please provide your professional summary in the following format:

<professional_summary>
Your professional summary goes here, using this structure : adjective + title + experience + specialties includes: specialties. Keep it short and concise, to the point. 
</professional_summary>
"""

LATEX_RESUME_PROMPT = """
You are an experienced HR professional tasked with creating a LaTeX resume based on a given template and user information.

# RULES AND GUIDELINES:
- Use the provided LaTeX template to create the resume
- Fill in the template with the user's information
- Include the generated professional summary
- Ensure the LaTeX code is valid and compilable
- Do not add or remove any LaTeX commands from the template
- Only fill in the designated areas in the template
- Use the langage from the job_description
- Tailor the user experience to the job_description. Include informations that are relevant for the job and could help the user get an interview. Hobbies and so are important to, because it can help the user connect with the recruiter. 
- Each bullet point should follow the following format : "I accomplished X by the measure Y that resulted in Z". For example, "I lowered hospital mortality rate by 10% by education nurses in new protocols which translates to 200 lives saved per year". Use compelling langage and keep the bullet point within 50 words.
- Do not make any information, use only informations from the <user_informations> tag.
- Put relevant metrics and informations for the recruiter in bold.
- Stick to the template as much as possible
- Keep the professional summary as it is, DO NOT MODIFY IT.
- Translate the template and the user_informations if needed.

# CONTEXT:
<job_description>
{{job_desc}}
</job_description>

<user_informations>
{{user_info}}
</user_informations>

<professional_summary>
{{professional_summary}}
</professional_summary>

# TEMPLATE:
<latex_template>
{{latex_template}}
</latex_template>

# OUTPUT:

Think step by step:
1. Read carefully the job description
2. In what language is the job description?
3. Read carefully the latex_template
4. What is the professional summary inside it?
5. Use the the latex_template to create the user's resume in latex. Use the same language as the job description, but keep the professional summary as it is (you can translate it tho).

Please provide the full LaTeX document inside the following format:

<language>
what is the language of job description?
</language>

<professional_summary_template>
Write here the professional summary from the template. It should be exactly the same than <professional_summary> tag. DO NOT CHANGE IT, JUST TRANSLATE IT IF NEEDED.
</professional_summary_template>

<resume_latex>
The complete LaTeX resume goes here. Keep the same language than the job_description. DO NOT MODIFY THE PROFESSIONAL SUMMARY, KEEP IT AS IT IS. TRANSLATE THE TEMPLATE IF NEEDED.
</resume_latex>
"""

NEXT_PAGE_FINDER_PROMPT = """
You will be searching a webpage that lists job postings to find the link to the next page of job listings, if such a link exists on the page.

Here is the URL of the webpage you need to search:
<url>
{{URL}}
</url>

Please follow these steps:
1. Load the webpage at the provided URL.
2. Scan the page for any links or buttons that indicate they lead to the next page of job listings. Common labels for such links include "Next", "Next Page", "Page 2", "→", etc.
3. If you find a "next page" link, extract the URL it points to. If there are multiple possible "next page" links, choose the one that appears to be the main one based on its location and prominence on the page.
4. If no "next page" link is found after a thorough search, make note of that.

Important note : do not create url, do not modify them.

Please provide your output in the following format:
<result>
If a "next page" link was found:
[URL of the next page]

If no "next page" link was found:
No "next page" link found on this page.
</result>
"""

IS_URL_JOB_DESCRIPTION_PROMPT = """
You are an experienced HR professional tasked with determining whether a given webpage URL is a job description page or a job listing page. There are two main categories of job-related pages:
1. Job description pages: These pages describe a specific job, including requirements, company information, and other details.
2. Job listing pages: These pages list multiple job openings and typically include links to individual job description pages.

Here is the URL to analyze:
<url>
{{URL}}
</url>

Please carefully review the content of the webpage at the provided URL. Look for indicators that suggest whether the page is a job description or a job listing. 

<scratchpad>
Use this space to think through your analysis of the page. Consider factors such as:
- Does the page focus on a single job or multiple job openings?
- Are there links to individual job descriptions or application forms?
- Is the content primarily a detailed description of a specific role, or a list of available positions?
</scratchpad>

Based on your analysis, determine whether the provided URL is a job description page or a job listing page. Provide your final answer inside <answer> tags, using the following format:

<answer>
[Job Description/Job Listing]
</answer>
"""

GET_LINKS_PROMPT = """
<Instructions>
You're an expert in web scrapping, in the job searching domain.
There are two main categories of job-related pages:
1. Job description pages: These pages describe a specific job, including requirements, company information, and other details.
2. Job listing pages: These pages list multiple job openings and typically include links to individual job description pages.
Your task is to determine whether the "href" attribute in a given JSON dump of HTML "a" element attributes likely links to a job description page or not.

Here is the JSON dump of the "a" element attributes:
<json_dump>
{{json_string}}
</json_dump>

Some things to consider:
- Look for keywords in the "href" URL that may indicate a job description page, like "job", "jobs", "career", etc. 
- Check if there are job-related query parameters in the URL like "jk" which often indicates a job key.
- See if the URL structure and path looks like it would be for a specific job (e.g. job description) (e.g. "/job/123456/" or "/viewjob.html?id=abc123") vs a job listing page (that contains research queries).
- Be cautious of URLs that look like search result pages, job listing pages.

<Examples>
{"attrs": {"data-gnav-element-name": "About", "class": ["icl-GlobalFooter-link"], "href": "https://ca.indeed.com/about"}} : <answer>no<answer>
{"attrs": {"data-testid": "relatedQuery", "href": "/q-machine-learning-l-montr%c3%a9al,-qc-jobs.html", "class": ["jobsearch-RelatedQueries-queryItem", "css-bmc2da", "eu4oa1w0"]}} : <answer>no<answer>
{"attrs": {"id": "job_6156853c8bd089f7", "data-mobtk": "1htomgp8pip8p83q", "data-jk": "6156853c8bd089f7", "data-hiring-event": "false", "data-hide-spinner": "true", "role": "button", "aria-label": "full details of Research Scientist, Computer Vision - Embodied AI (FAIR) | Chercheur en vision artificielle, IA incarn\\xc3\\xa9e (FAIR)", "class": ["jcs-JobTitle", "css-jspxzf", "eu4oa1w0"], "href": "/rc/clk?jk=6156853c8bd089f7&bb=cbRRkUImU_5DE74Jx4Ucc1wg84F_uOcnC1EMXMz6BlzGEyyAKkWBMKvbvbGjD-GRApbjgMgGKzN46yffoM73Usm3VlKBAFts8BcMMmA_LvPQUnmqLrXYlw%3D%3D&xkcb=SoBz67M3B4lM8ExSQB0GbzkdCdPP&fccid=ba07516c418dda52&vjs=3"}} : <answer>yes<answer>
{"attrs": {"class": ["col", "pt-2", "pb-3"], "href": "/job/205080-titleist-golfer-insights-research-analyst/", "title": "View details for this job"}} : <answer>yes<answer>
{"attrs": {"href": "/jobs-in-karnataka/bengaluru/"}} : <answer>no<answer>
</Examples>

Write your reasoning to find out if this link does or does not go to a job description page inside <reasoning> tags.
Then provide the answer in the <answer> tag.

Based on analyzing the "href" attribute and URL structure, do you believe this "a" element most likely links to a job details page? Provide your reasoning and then give a yes or no answer inside <answer> tags.
</Instructions>
"""

MARKDOWN_FORMATTER_PROMPT = """
Here is the raw text for a job description scraped from a website:

<raw_job_description>
{{RAW_JOB_DESCRIPTION}}
</raw_job_description>

Please carefully read through the text above and extract all the relevant information you can find about the job, such as:

- Job title 
- Company name
- Location
- Salary
- Job type (e.g. full-time, part-time, contract)
- Benefits
- Job description and responsibilities 
- Required qualifications, skills, experience and education
- Company description

Once you have gathered all the pertinent details, please organize and format the information into a clean, readable job description using markdown formatting. 

A few important notes:
- DO NOT make up or add any information about the job that is not explicitly stated in the raw text. 
- Keep the original job title exactly as it appears in the raw text, even if it is not properly capitalized or formatted.
- Use headers, bullet points, and other markdown elements to clearly structure the various sections of the job description.

Please output the final formatted job description inside <formatted_job_description> tags. It must be human readable, so no tags inside it.
Please also provide the job title inside <job_title> tags, the salary inside <salary> tags, the location inside <location> tags and the company inside <company> tags. Do not put theses tags in the <formatted_job_description> tags, put them outside, even if it means that you have to duplicate some information.

ERROR HANDLING :
If the raw text provided does not contain any information about a job description, or is empty, just answer "None" for all the tags.
If the job description looks like there is only a salary comparison between multiple similiar professions, or it talks a lot about different salaries but nothing about what you really have to do, it means it is just a job salary comparison and there was an error before. Please also answer "None" in all the tags.
This is an example of what a salary comparison might look like :
<example_salary_comparison>
## Top Companies for Machine Learning Engineers in Montréal, QC
- Intact: $145,611 per year (7 salaries reported)
- Workday: $128,200 per year (9 salaries reported)
- Wilfrid Laurier University: $118,853 per year (5 salaries reported)
- Kinaxis: $115,630 per year (7 salaries reported)
- RBC: $96,451 per year (5 salaries reported)

## Highest Paying Cities for Machine Learning Engineers near Montréal, QC
- Toronto, ON: $123,466 per year (38 salaries reported)
- Markham, ON: $119,542 per year (6 salaries reported)
- Waterloo, ON: $118,853 per year (5 salaries reported)
- Vancouver, BC: $118,276 per year (25 salaries reported)
- Kelowna, BC: $114,204 per year (15 salaries reported)
- Edmonton, AB: $110,630 per year (7 salaries reported)
- Montréal, QC: $105,458 per year (9 salaries reported)
- Ottawa, ON: $97,680 per year (5 salaries reported)
- Burnaby, BC: $90,474 per year (23 salaries reported)
</example_salary_comparison>
"""

JOB_RELEVANCE_PROMPT = """
You will be acting as an experienced HR professional specializing in the following domains:

<DOMAIN_OF_INTEREST>
{{DOMAIN_OF_INTEREST}}
</DOMAIN_OF_INTEREST>

Your task is to determine whether a given job is a good fit for the user based on their personal and professional experiences, as well as the job description provided.

This is the user description in markdown (including who he is, what he is looking for, and it's full CV):

<USER_WANT>
{{USER_WANT}}
</USER_WANT>


<USER_CONTEXT>
{{USER_CONTEXT}}
</USER_CONTEXT>

The job description will be provided in markdown format, similar to what you might find on job search websites like Indeed:

<JOB_DESCRIPTION>
{{JOB_DESCRIPTION}}
</JOB_DESCRIPTION>

To determine the relevance of the job, use <thinking> tags to compare the day-to-day responsibilities of the job with what the user is looking for. Also, compare the experiences and qualifications required for the job with the user's existing experiences and qualifications.

<thinking>
Think step by step, following this structure :
1: summarize what the job is about, including this informations : 
- what are the core missions?
- what are the key skills the candidate must have?
- how much experience in the key skills the candidate must have?
2. Now based on the user description, answer this questions :
- What do you think are the core missions the user is looking for?
3. Now using this informations, answer this questions :
- does the core missions align with what the user want?
- does the user have sufficient experience in the key skills?
- if no, is there any skills that the user have that can be transfered to any key skills?
- is the job aiming for a profil like the user? For example, if the post is looking for a senior developper (10+ years of experience in the domain), and the user is a junior (2 to 4 years of experience in the domain), the recruiter are not looking for the profil of the user. So it is not a good fit, unless the experience is EXACTLY what the user have been doing.
3. Based on thoose answers and elements, can you answer :
- if yes or no the user could want to have this job,
- and if the recruiter could considerate seriously the user profile as the one to work for this job?
</thinking>

If necessary, use <scratchpad> tags to calculate the user's experience in a specific domain.

<scratchpad>
Calculate the user's experience in the relevant domain, if needed.
</scratchpad>

Based on your analysis, provide your final answer inside <answer> tags, using only "relevant" or "not relevant". Do not include any additional information inside the <answer> tags.

Keep in mind that job postings often ask for a little more experience than what is actually necessary. 
Focus primarily on the first few requirements listed, as they are typically the most important ones.

If you are unsure about the relevance of the job, err on the side of caution and answer "not relevant". 

Be strict in the selection of jobs that are relevant : if there is an evident lack of information about the job and it only talks about money for example, it is not relevant.

Same way, focus more on what the user want to do rather than what he can do. What he can do is a precondition to determine if the job is relevant or not, but what the user want to do is crucial to determine if the job is relevant or not.

Provide your final answer in the following format:

<answer>relevant</answer>
OR
<answer>not relevant</answer>
"""

#todo améliorer les examples en montrant le cv, l'envie, la description du job, comment réfléchir et quel score donner
JOB_SCORE_PROMPT = """
You are an experience HR.
Your goal is to score the fitting of a job for the user based on what he wants to do, his experiences, and the job description.

## RULES AND GUIDELINES
- to determine the relevance of the job, use <thinking> tags to reflect on the following subjects :
    - compare the day-to-day responsibilites of the job with what the user wants to do.
    - compare the expeted skills and experiences with what the user already have. If you see a transposable fit, mention it.
- score between 0 and 10. 0 is not compatible at all, 10 is the perfect fit
- do not be afraid to give extreme answers.

here is a more detailled approach to the <thinking> tags :
<thinking>
Think step by step, following this structure :
1: summarize what the job is about, including this informations : 
- what are the core missions?
- what are the key skills the candidate must have?
- how much experience in the key skills the candidate must have?
2. Now based on the user description, answer this questions :
- What do you think are the core missions the user is looking for?
3. Now using this informations, answer this questions :
- does the core missions align with what the user want?
- does the user have sufficient experience in the key skills?
- if no, is there any skills that the user have that can be transfered to any key skills?
- is the job aiming for a profil like the user? For example, if the post is looking for a senior developper (10+ years of experience in the domain), and the user is a junior (2 to 4 years of experience in the domain), the recruiter are not looking for the profil of the user. So it is not a good fit, unless the experience is EXACTLY what the user have been doing.
3. Based on thoose answers and elements, can you answer :
- how much the user could want to have this job,
- and how much the recruiter could considerate seriously the user profile as the one to work for this job?
</thinking>

If necessary, use <scratchpad> tags to calculate the user's experience in a specific domain.

<scratchpad>
Calculate the user's experience in the relevant domain, if needed.
</scratchpad>

## CONTEXT

This is the user description in markdown (including who he is, what he is looking for, and it's full CV):

<USER_CONTEXT>
{{USER_CONTEXT}}
</USER_CONTEXT>

The job description will be provided in markdown format, similar to what you might find on job search websites like Indeed:

<JOB_DESCRIPTION>
{{JOB_DESCRIPTION}}
</JOB_DESCRIPTION>

## ANSWER EXAMPLES

Based on your analysis, provide your final answer inside <answer> tags, using only the score. Do not include any additional information inside the <answer> tags.
<ANSWER_EXAMPLE1>
<thinking>

<thinking>
<answer>0</answer>
</ANSWER_EXAMPLE1>

"""

JOB_SCORE_PROMPT2 = """
You will be acting as an experienced HR professional specializing in the following domains:

<DOMAIN_OF_COMPETENCE>
{{DOMAIN_OF_COMPETENCE}}
</DOMAIN_OF_COMPETENCE>

Your task is to score (from 0 to 10) the fitting of a job for the user based on their personal and professional experiences, as well as the job description provided.
0 is really bad, the user won't like it, or is not suited at all to do this job.
10 is perfect, exactly what the user want, and he match perfectly or exceed the requirements for the job.
Do not be afraid to give a 0 or a 10.

This is the user description in markdown (including who he is, what he is looking for, and it's full CV):

<USER_CONTEXT>
{{USER_CONTEXT}}
</USER_CONTEXT>

The job description will be provided in markdown format, similar to what you might find on job search websites like Indeed:

<JOB_DESCRIPTION>
{{JOB_DESCRIPTION}}
</JOB_DESCRIPTION>

To determine the relevance of the job, use <thinking> tags to compare the day-to-day responsibilities of the job with what the user is looking for. Also, compare the experiences and qualifications required for the job with the user's existing experiences and qualifications.

<thinking>
Think step by step, following this structure :
1: summarize what the job is about, including this informations : 
- what are the core missions?
- what are the key skills the candidate must have?
- how much experience in the key skills the candidate must have?
2. Now based on the user description, answer this questions :
- What do you think are the core missions the user is looking for?
3. Now using this informations, answer this questions :
- does the core missions align with what the user want?
- does the user have sufficient experience in the key skills?
- if no, is there any skills that the user have that can be transfered to any key skills?
- is the job aiming for a profil like the user? For example, if the post is looking for a senior developper (10+ years of experience in the domain), and the user is a junior (2 to 4 years of experience in the domain), the recruiter are not looking for the profil of the user. So it is not a good fit, unless the experience is EXACTLY what the user have been doing.
3. Based on thoose answers and elements, can you answer :
- how much the user could want to have this job,
- and how much the recruiter could considerate seriously the user profile as the one to work for this job?
</thinking>

If necessary, use <scratchpad> tags to calculate the user's experience in a specific domain.

<scratchpad>
Calculate the user's experience in the relevant domain, if needed.
</scratchpad>

Based on your analysis, provide your final answer inside <answer> tags, using only the score. Do not include any additional information inside the <answer> tags.
<ANSWER_EXAMPLES>
<answer>0</answer>
<answer>10</answer>
<answer>8</answer>
<answer>2</answer>
</ANSWER_EXAMPLES>


Keep in mind that job postings often ask for a little more experience than what is actually necessary. 
Focus primarily on the first few requirements listed, as they are typically the most important ones.

if what you have for a job description looks like it is not a job description at all, don't hesitate to answer 0. It is possible that there is some errors and you are not given a job description, so that's why I give you this specific instruction.

Same way, focus more on what the user want to do rather than what he can do.
Note : experience and job location are PREREQUISITES, they were filtered before, so you don't have to use them in your evaluation. Of course the job match the location, because all the jobs that don't have already been filtered out. So don't take this parameters into account.

Here is some examples of how to provide your final answer. Please follow the format:
<ANSWER_EXAMPLES>
<answer>0</answer>
<answer>10</answer>
<answer>8</answer>
<answer>2</answer>
</ANSWER_EXAMPLES>
"""

GET_PAIN_POINTS_PROMPT = """
You are an experienced HR professional tasked with identifying the pain points and the biggest challenges someone in this position would face day-to-day, in the following job description:

<job_desc>
{{job_desc}}
</job_desc>

Please carefully read through the job description and identify the key pain points and the biggest challenges someone in this position would face day-to-day, in the following job description that the company is trying to address with this role. Provide your output in the following format:

<pain_points>
[List of pain points]
</pain_points>
"""

CONNECT_WITH_READER_PROMPT = """
Roleplay as the user. You are applying for a new job.
Write an attention-grabbing hook for your cover letter that highlights your experience and qualifications in a way that shows you empathize and can successfully take on the challenges and pain points of the {{job_title}} role
Consider incorporating specific examples of how you've tackled these challenges and pain points in your past work, and explore creative ways to express your enthusiasm for the opportunity. Keep your hook within 100 words.

<user_informations>
{{user_info}}
</user_informations>

<job_description>
{{job_desc}}
</job_description>

# OUTPUT

Please provide your hook in the following format :

<hook>
Write your hook there.
</hook>
"""

WRITE_COVER_LETTER_PROMPT = """
You are an experienced HR professional tasked with writing a cover letter for a job description.

# RULES AND GUIDELINES:
- respond in json format
- extend the current cover letter
- do not rewrite the hook, just extend the cover letter in the 'body' property of the json object
- keep the content of the body property under 250 words
- use the resume of the user to write the body of the cover letter as if you were the user
- spin ONE of your experiences to show that you can deal with this challenge
- DO NOT MAKE ANY INFORMATION


# CONTEXT

<job_description>
{{job_desc}}
</job_description>

<user_informations>
{{user_info}}
</user_informations>

<current_cover_letter>
{{cover_letter}}
</current_cover_letter>

# OUTPUT

Please respond in the following format :

<cover_letter>
a json object based on the current_cover_letter, in wich you added a 'body' property that is the rest of the cover letter, generated using the rules and guidelines.
</cover_letter>
"""

LATEX_COVER_LETTER_PROMPT = """
You are an experienced HR professional tasked with writing a cover letter for a job description.

# RULES
- use the template to write the cover letter in LaTeX
- use do not make any information
- generate a valide latex file
- use the data given in CONTEXT to fill up the template

# CONTEXT
<user_informations>
{{user_info}}
</user_informations>

<cover_letter>
{{cover_letter}}
</cover_letter>

# TEMPLATE

<latex_template>
{{latex_template}}
<latex_template>

# OUTPUT

Please provide the full LaTeX document inside the following format :
<cover_latex>
the cover letter in latex using the template goes here
</cover_latex>

"""
