from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from typing import List, Tuple, Set, Dict
import re


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    i: int = 0
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        if i <= 0 or i >= 13:
            i += 1
            continue

        interpreter.process_page(page)
        i += 1

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text


def tsplit(string, delimiters):
    """Behaves str.split but supports multiple delimiters."""

    delimiters = tuple(delimiters)
    stack = [string,]

    for delimiter in delimiters:
        for i, substring in enumerate(stack):
            substack = substring.split(delimiter)
            stack.pop(i)
            for j, _substring in enumerate(substack):
                stack.insert(i+j, _substring)

    return stack

def get_categories(text: str) -> List[Tuple[str, str]]:
    cat_reg_pat: str = r'\s+(((?!\s{3,}|FL\s|PM\s|ACS\s|PA\s|ID\s|FADAA\s|FPL\s|FTRI\s|LLC\s|NW\s|DL:\s|DB:\s|II:\s|SS\s|SOC:|DCF\s|TTY:\s)[A-Z\-\s&:]){2,})\s{2,}'
    
    cat_regex = re.compile(cat_reg_pat)

    return cat_regex.findall(text) 


def get_paragraphs(section_list: List[List[str]]) -> List[List[str]]:
    filt_section_list: List[List[str]] = []
    
    for i in range(len(section_list)):
        filt_section_list.append([])
        for section in section_list[i]:
            sec: str = section.strip()
            if sec == '' or sec.startswith('(') or '\x0c(' in sec or len(sec.split('\n')) <= 2:
                continue    
            filt_section_list[i].append(sec)
    
    return filt_section_list


def match_on_pattern(text: str, pattern: str, index: int = 0) -> Tuple[str, str]:
    regex = re.compile(pattern)
    match_list = regex.findall(text)
    match: str

    if len(match_list) == 0:
        return (text, '')
    
    if pattern == '([A-Za-z0-9\._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})':
        match = match_list[index]
    else:
        match = match_list[index][0]

    upd_text: str = text.replace(match, ' ')

    return upd_text, match.strip().replace('\n', ' ').replace(',', '.')


def get_section_info(section: str) -> List[str]:
    # sect_pattern = re.compile(r'^((([A-Z][a-z.,!?()\'\\-]+|of|for|and)\s+)+(?=([A-Z][a-z.!?()\'\\-]+\s+)))([\w\s\-.,:!?()\'\\]+?)((Fax:\s+|Helpline:\s+|[Ee]mail:\s+)|([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\s+)|(\d{3}-\d{3}-\d{4}\s+)|(\d{1,5}\s(\w.|[\w\s,]+)\s((\w*\s){1,2}[\s\w]*,\s){1,2}\w{1,4}\s\d{5}\s+))+([\w\s\-.,:!?()\'\\]+)')

    title_pattern: str = r"^((([A-Z][a-z.,!?()\'’\\-]+|of|for|and)\s+)+)(?=([A-Z][a-z.!?()\'\\-]+\s+))" 
    address_info_pattern: str = r"(\d{1,5}\s(\w.|[\w\s,]+)\s((\w*\s){1,2}[\s\w]*,\s){1,2}\w{1,4}\s\d{5})+"
    phone_pattern: str = r"((\d{3}-\d{3}-\d{4})+)"
    email_pattern: str = r"([A-Za-z0-9\._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"


    section, title = match_on_pattern(section, title_pattern)
    section, address = match_on_pattern(section, address_info_pattern)
    section, phone = match_on_pattern(section, phone_pattern)
    section, email = match_on_pattern(section, email_pattern)

    print(f'title: {title}\naddress: {address}\nphone: {phone}\nemail: {email}\ndescription: {section}\n\n')

    return [title, address, phone, email, section.strip().replace('\n', ' ').replace(',', '.')]


def get_pdf_info():
    text: str = convert_pdf_to_txt('service2019.pdf')
    categories: List[str] = [cat[0] for cat in get_categories(text)]
    new_text: str = tsplit(text, categories)
    section_list: List[List[str]] = [txt.split('\n \n') for txt in new_text]
    section_list.pop(0)
    
    filt_section_list: List[List[str]] = get_paragraphs(section_list)

    categories = [cat.replace('\n', ' ') for cat in categories]

    fp = open('service_parsed.csv', 'w')
    fp.write('title, category, address, phone, email, description,\n')

    for i in range(len(filt_section_list)):
        for section in filt_section_list[i]:
            res_lis: List[str] = get_section_info(section)
            fp.write(f"{res_lis[0]}, {categories[i]}, {res_lis[1]}, {res_lis[2]}, {res_lis[3]}, {res_lis[4]},\n")


if __name__ == '__main__':
    get_pdf_info()

