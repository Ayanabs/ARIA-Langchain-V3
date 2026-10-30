from langchain_core.tools import tool
from aria_agent.http.client import make_request, clean_id

@tool
def fetchAllHrQHiEduQualifications() -> list:
    """Retrieves higher education degree qualification type titles from GET /api/hr-q-hiedu-qualifications.
    Database and JSON fields returned per record:
    - id (int) [PRIMARY KEY / FOREIGN KEY]: Qualification type ID.
    - QualificationName (str): Qualification type degree title (e.g. 'BSc' [Bachelor of Science], 'MSc' [Master of Science], 'PhD' [Doctor of Philosophy], 'BTech' [Bachelor of Technology], 'MBA' [Master of Business Administration], 'Diploma' [Diploma qualification]).
    Maps to GET /api/hr-q-hiedu-qualifications."""
    return make_request("/api/hr-q-hiedu-qualifications")
