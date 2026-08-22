QUESTION_BANK = {
    "Software Developer": [
        {"question": "What is object-oriented programming and why is it useful?", "reference": "Object-oriented programming organizes software into objects that combine data and behavior. Its main ideas include encapsulation, inheritance, polymorphism and abstraction. It improves code reuse, organization and maintainability.", "keywords": ["object", "encapsulation", "inheritance", "polymorphism", "reuse"]},
        {"question": "What is the difference between a list and a tuple in Python?", "reference": "A list is mutable, so items can be added, removed or changed. A tuple is immutable after creation. Lists are used for changing collections while tuples are useful for fixed data.", "keywords": ["list", "tuple", "mutable", "immutable", "change"]},
        {"question": "How would you debug a program that is giving the wrong output?", "reference": "I would reproduce the issue, read the error or compare actual and expected output, isolate the problematic section, use logging or a debugger, fix the cause, and test the result including edge cases.", "keywords": ["reproduce", "error", "debugger", "test", "output"]},
        {"question": "What is an API?", "reference": "An API, or Application Programming Interface, is a defined way for software systems to communicate. A client sends a request to an endpoint and receives a response, often using HTTP and JSON.", "keywords": ["application", "interface", "request", "response", "HTTP"]},
        {"question": "Why is version control important in a software project?", "reference": "Version control tracks changes to code, lets developers collaborate safely, supports branches and code review, and makes it possible to restore an earlier working version when needed.", "keywords": ["changes", "collaborate", "branch", "restore", "git"]},
    ],
    "Data Analyst": [
        {"question": "What steps would you take to clean a dataset?", "reference": "I would inspect the data, handle missing values, remove duplicates, correct data types and inconsistent formats, identify outliers, validate the cleaned data, and document the decisions.", "keywords": ["missing", "duplicates", "types", "outliers", "validate"]},
        {"question": "What is the difference between correlation and causation?", "reference": "Correlation means two variables move together, while causation means one variable directly produces a change in another. Correlation alone does not prove a causal relationship because other factors may exist.", "keywords": ["relationship", "cause", "variables", "prove", "factor"]},
        {"question": "How do you choose a chart for presenting data?", "reference": "I first consider the question and data type. Bar charts compare categories, line charts show trends over time, scatter plots show relationships, and I keep labels and scales clear for the audience.", "keywords": ["bar", "line", "trend", "categories", "audience"]},
        {"question": "What is a KPI?", "reference": "A Key Performance Indicator is a measurable value that shows progress toward a business objective. A useful KPI is relevant to a goal, clearly defined, measurable and reviewed regularly.", "keywords": ["key performance indicator", "measure", "goal", "business", "progress"]},
        {"question": "How would you explain a complex analysis to a non-technical manager?", "reference": "I would start with the business question and main insight, use simple language and clear visuals, explain the impact and recommendation, and keep technical detail available only if requested.", "keywords": ["business", "simple", "visual", "insight", "recommendation"]},
    ],
    "HR Executive": [
        {"question": "How would you handle a conflict between two employees?", "reference": "I would listen to each employee privately and fairly, collect facts, encourage respectful communication, help them identify a solution, document the outcome, and follow up to ensure the conflict is resolved.", "keywords": ["listen", "fair", "facts", "solution", "follow up"]},
        {"question": "What makes an effective recruitment process?", "reference": "An effective process starts with a clear job description, fair sourcing and screening, structured interviews using job-related criteria, timely communication, reference checks and a respectful candidate experience.", "keywords": ["job description", "fair", "interview", "criteria", "candidate"]},
        {"question": "How can employee engagement be improved?", "reference": "Engagement can improve through clear goals, recognition, growth opportunities, supportive managers, regular feedback, fair policies and listening to employee concerns through surveys or conversations.", "keywords": ["recognition", "growth", "feedback", "manager", "goals"]},
        {"question": "Why is confidentiality important in HR?", "reference": "HR handles sensitive personal, performance and company information. Confidentiality builds employee trust, protects privacy, supports fairness and helps the organization meet its legal and ethical responsibilities.", "keywords": ["sensitive", "privacy", "trust", "legal", "ethical"]},
        {"question": "How would you give constructive feedback to an employee?", "reference": "I would give feedback privately and promptly, describe specific observable behavior and its impact, listen to the employee, agree on practical improvement steps, offer support and set a follow-up date.", "keywords": ["specific", "behavior", "impact", "improvement", "follow-up"]},
    ],
}


def get_roles():
    return list(QUESTION_BANK.keys())


def get_questions(role: str):
    return QUESTION_BANK.get(role, [])
