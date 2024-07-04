import fitz  # PyMuPDF
import re

class ResumeParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.text_items = []
        self.lines = []
        self.sections = {}
        self.subsections = {}
        self.resume_data = {}

    def clean_text(self, text):
        text = text.replace('\t', ' ')
        text = text.replace('\r', ' ')
        text = text.replace('\xa0', ' ')
        text = text.replace('\xad', ' ')
        return ' '.join(text.split())

    def extract_text_items(self):
        doc = fitz.open(self.pdf_path)
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if block["type"] == 0:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            is_bold = False
                            if span["font"].lower().find('bold') != -1:
                                is_bold = True
                            text_item = {
                                "font": span["font"],
                                "text": self.clean_text(span["text"]),
                                "x": span["bbox"][0],
                                "y": span["bbox"][1],
                                "width": span["bbox"][2] - span["bbox"][0],
                                "font_size": span["size"],
                                "bold": is_bold,
                                "new_line": False
                            }
                            if text_item["text"] != "":
                                self.text_items.append(text_item)

        for i in range(len(self.text_items) - 1):
            if self.text_items[i]["y"] + 1.5 < self.text_items[i + 1]["y"]:
                self.text_items[i]['new_line'] = True


    def group_text_items_into_lines(self):
        avg_char_width = sum(item["width"] for item in self.text_items if not item["bold"] ) / sum(len(item["text"]) for item in self.text_items if not item["bold"])
        current_line = []

        for i, item in enumerate(self.text_items):

            
            current_line.append(item)
            if item['new_line']:
                self.lines.append(current_line)
                current_line = []
            else:
                continue
        self.lines.append(current_line)
        



    def group_lines_into_sections(self):
        """
        The resume parser applies some heuristics to detect a section title. The main heuristic to determine a section title is to check if it fulfills all 3 following conditions:
        1. It is the only text item in the line <- working on
        2. It is bolded
        3. Its letters are all UPPERCASE
        """
        current_section = 'PROFILE'

        for i in range(0, len(self.lines)):

            # if len(line) == 1 and line[0]["bold"] and line[0]["text"].isupper():
            #     current_section = line[0]["text"]

            # Generally first section is the profile section.
            # And since profile doesn't has a headline or the headline is generally the name of the candidate.
            # Hence we have this of condition
            if i == 0:
                self.sections.update({f"{current_section}" : {'text_y':[], 'y': 0, 'bold':False}})
            # In simple words, if a text item is double emphasized to be both bolded and uppercase,
            # it is most likely a section title in a resume. This is generally true for a well formatted resume.
            # There can be exceptions, but it is likely not a good use of bolded and uppercase in those cases.
            if self.lines[i][0]["bold"] and self.lines[i][0]["text"].isupper() and i != 1:
                current_section = self.lines[i][0]["text"] 
                self.sections.update({f"{current_section}" : {'text_y':[], 'y': 0, 'bold': False, "font_size": None,}})
                continue
            if current_section:
                for line in self.lines[i]:
                    self.sections[current_section]['text_y'].append({"text" : line["text"], "y":line["y"], "font_size": line['font_size'], 'bold':line['bold']})
                    self.sections[current_section]['y'] = self.lines[i][0]['y']
                    self.sections[current_section]['bold'] = self.lines[i][0]['bold']



    def contextulize_subsection_items_into_lines(self, lines):
        merged_lines = []
        current_point = []
        for line in lines:
            if line.startswith("●") or line.startswith("-"):  # Assuming bullet points start with these symbols
                if current_point:
                    merged_lines.append(' '.join(current_point))
                current_point = [line[1:].strip()]
            else:
                current_point.append(line)
        if current_point:
            merged_lines.append(' '.join(current_point))

        return merged_lines

    def detect_subsections(self, lines, typical_line_gap):
        subsections = []
        current_subsection = []
        for i, line in enumerate(lines["text_y"]):
            try:
                if i > 0 and (line["y"] - lines["text_y"][i-1]["y"] > typical_line_gap * 2): #or line[0]["bold"]) or line[0]['text'].isupper():
                    if current_subsection:
                        subsections.append(current_subsection)
                    current_subsection = [line["text"]]
                else:
                    current_subsection.append(line["text"])
            except IndexError as e:
                current_subsection.append(line["text"])
                print(e.__str__())
        if current_subsection:
            subsections.append(current_subsection)
        return subsections

    def feature_scoring(self, text, feature_sets):
        score = 0
        try:
            for feature_func, value in feature_sets:
                if feature_func(text):
                    score += value
        except Exception as e:
            print(e.__traceback__())
        return score

    def extract_resume_attributes(self):
        feature_sets = {
            "name": [
                (lambda text: text.istitle(), 4),
                (lambda text: re.match(r'^[a-zA-Z\s\.]+$', text), 3),
                (lambda text: bool(re.match(r'^[A-Z\s]+$', text)), 2),
                (lambda text: '@' in text, -4),
                (lambda text: any(char.isdigit() for char in text), -4),
                (lambda text: ',' in text, -4),
                (lambda text: '/' in text, -4),
                (lambda text: '.' in text, -4)
            ],
            "email": [
                (lambda text: re.match(r'\S+@\S+\.\S+', text), 10)
            ],
            "phone": [
                (lambda text: re.match(r'\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}', text), 10)
            ],
            "location": [
                (lambda text: re.match(r'[A-Z][a-zA-Z\s]+, [A-Z]{2}', text), 10)
            ],
            "url": [
                (lambda text: re.match(r'\S+\.[a-z]+\/\S+', text), 10)
            ],
            "school": [
                (lambda text: any(keyword in text.lower() for keyword in ["college", "university", "school"]), 10)
            ],
            "degree": [
                (lambda text: any(keyword in text.lower() for keyword in ["associate", "bachelor", "master", "phd", "doctorate"]), 10)
            ],
            "gpa": [
                (lambda text: re.match(r'[0-4]\.\d{1,2}', text), 10)
            ],
            "date": [
                (lambda text: re.match(r'(?:19|20)\d{2}', text), 5),
                (lambda text: any(keyword in text.lower() for keyword in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "spring", "summer", "fall", "winter", "present"]), 5)
            ],
            "job_title": [
                (lambda text: any(keyword in text.lower() for keyword in ["analyst", "engineer", "intern", "manager", "director", "consultant", "developer"]), 10)
            ],
            # "company": [
            #     (lambda text: any(not re.search(r'\b(?:analyst|engineer|intern|manager|director|consultant|developer|spring|summer|fall|winter|january|february|march|april|may|june|july|august|september|october|november|december)\b', text.lower())), 10)
            # ],
            "project": [
                (lambda text: not re.search(r'(?:19|20)\d{2}', text), 5)
            ]
        }
        typical_line_gap = sum(self.lines[i+1][0]["y"] - self.lines[i][0]["y"] for i in range(0, len(self.lines)-1)) / (len(self.lines))
        
        for section, lines in self.sections.items():
            section_type = self.identify_section_type(section)
            if section == "PROFILE":
                self.process_section(lines, feature_sets)
            elif section_type in ['summary', 'skills']:
                    subsections = self.detect_subsections(lines, typical_line_gap)
                    self.resume_data.update({section: subsections})

            elif section_type in ['work_experience', 'education', 'projects', 'other']:
                subsections = self.detect_subsections(lines, typical_line_gap)
                subsection_list = [] 
                for subsection in subsections:
                    lines = self.contextulize_subsection_items_into_lines(subsection)
                    attributes = self.process_sub_section([lines[0]], section_type)
                    attributes.update({"description": lines[1:]})
                    subsection_list.append(attributes)
                self.resume_data.update({section_type : subsection_list})


    def identify_section_type(self, section):
        # Identify section type based on section name keywords
        section = section.lower()
        if any(keyword in section for keyword in ["profile", "summary", "objective"]):
            return "summary"
        elif any(keyword in section for keyword in ["experience", "employment", "work"]):
            return "work_experience"
        elif any(keyword in section for keyword in ["education", "academic", "campus"]):
            return "education"
        elif any(keyword in section for keyword in ["project", "projects"]):
            return "projects"
        elif any(keyword in section for keyword in ["skills", "competencies"]):
            return "skills"
        else:
            return "other"
            
    def process_sub_section(self, lines, section_type):
        attributes = {}
        patterns = {
            "work_experience": {
                "company": r"^[A-Za-z\s,]+",
                "job_title": r"\b(?:analyst|engineer|intern|manager|director|consultant|developer)\b",
                "duration": r"(?:\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|spring|summer|fall|winter)\b\s\d{4}\s?-\s?(?:present|(?:\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|spring|summer|fall|winter)\b\s)?\d{4}))",
            },
            "education": {
                "school": r"[A-Za-z\s]+(?:College|University|School)",
                "degree": r"\b(?:Associate|Bachelor|Master|Doctor|PhD)\b",
                "gpa": r"[0-4]\.\d{1,2}",
                "duration": r"(?:\b(?:19|20)\d{2}\b)",
            },
            "projects": {
                "project_title": r"^[A-Za-z\s,]+",
                "duration": r"(?:\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|spring|summer|fall|winter)\b\s\d{4}\s?-\s?(?:present|(?:\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|spring|summer|fall|winter)\b\s)?\d{4}))",
            },
            "summary": {
            "summary_text": r"(Summary|Profile|Objective):?\s*(.*)"
        }
        }

        if section_type in patterns:
            for attribute, pattern in patterns[section_type].items():
                for line in lines:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                            attributes[attribute] = match.group().strip()

        return attributes

    def process_section(self, lines, feature_sets):
        for attribute, features in feature_sets.items():
            highest_score = -float("inf")
            best_match = ""
            for item in lines['text_y']:
                score = self.feature_scoring(item['text'], features)
                if score > highest_score:
                    highest_score = score
                    best_match = item['text']
            if highest_score > 0:
                if attribute in self.resume_data:
                    if isinstance(self.resume_data[attribute], list):
                        self.resume_data[attribute].append(best_match)
                    else:
                        self.resume_data[attribute] = [self.resume_data[attribute], best_match]
                else:
                    self.resume_data[attribute] = best_match      

    def parse(self):
        self.extract_text_items()
        self.group_text_items_into_lines()
        self.group_lines_into_sections()
        # self.group_lines_into_subsections()
        self.extract_resume_attributes()

        return self.resume_data

if __name__ == "__main__":
    parser = ResumeParser("./06resume-amaan.pdf")
    resume_data = parser.parse()
    print(resume_data)
