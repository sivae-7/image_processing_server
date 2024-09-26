import re
import json
import pytesseract
from PIL import Image
import os
from dotenv import load_dotenv
from celery import shared_task

load_dotenv()
voter_data_path = os.getenv('VOTER_DATA_PATH')
missed_voter_pages_path = os.getenv('MISSED_VOTER_PAGES_PATH')
all_voters = []
missed_voter_pages=[]
isValidImage = False

def is_valid_voter(voter):
    voter_id_pattern = r'\d{3,}'

    voter_id = voter.get('VoterID')
    name = voter.get('Name')
    if (voter_id and re.search(voter_id_pattern, voter_id) and name ):
        return any(voter[key] for key in voter)
    return False

def extract_voter_ids(line):
    return [voter_id for voter_id in line.split() if len(voter_id) > 3]

def extract_names(line):
    return [name.strip() for name in line.split("Name") if name.strip()]

def extract_relation_info(relation_text):
    relation_names = [rel.strip() for rel in relation_text.replace("Father Name", "").replace("Husband Name", "").replace("Mother Name", "").replace("Other", "").split("  ") if rel.strip()]
    
    if "Father Name" in relation_text:
        relation_type = "Father"
    elif "Mother Name" in relation_text:
        relation_type = "Mother"
    elif "Husband Name" in relation_text:
        relation_type = "Husband"
    else:
        relation_type = "Other"  
        
    return relation_names, relation_type

def extract_house_numbers(line):
    return [hn.strip() for hn in line.replace("House Number", "").replace("Photo", "").split("  ") if hn.strip()]

def extract_age_gender_info(line):
    return [ag.strip().split("Gender") for ag in line.split("Age") if ag.strip()]

def extract_age_gender_pair(line):
    age_gender_data = line.split("Age")
    age_gender = [ag.strip().split("Gender") for ag in age_gender_data if ag.strip()]


def parse_voter_section(section, part_No, ward_No, constituency_No,constituency_Name, section_Name):
    lines = section.split('\n')
    if len(lines) < 5:
        return []
    
    voter_ids = extract_voter_ids(lines[0])
    names = extract_names(lines[1])
    relation_names, relation_type = extract_relation_info(lines[2])
    house_numbers = extract_house_numbers(lines[3])
    age_gender = extract_age_gender_info(lines[4])

    voters = []

    for i in range(3):  
        age = age_gender[i][0].strip() if i < len(age_gender) and len(age_gender[i]) > 0 else None
        gender = age_gender[i][1].strip() if i < len(age_gender) and len(age_gender[i]) > 1 else None

        voter = {
            "VoterID": voter_ids[i] if i < len(voter_ids) else None,
            "Name": names[i] if i < len(names) else None,
            "RelationType": relation_type,
            "RelationName": relation_names[i] if i < len(relation_names) else None,
            "HouseNumber": house_numbers[i] if i < len(house_numbers) else None,
            "Age": age,
            "Gender": gender,
            "SectionName" : section_Name,
            "WardNo" : ward_No,
            "PartNO" : part_No,
            "constituencyName" : constituency_Name,
            "constituencyNO" : constituency_No
                            }
        if is_valid_voter(voter):
            voters.append(voter)
    
    return voters

def process_header(header):
    header = list(filter(lambda x: x.strip(), (header).split('\n')))
    header_text = ' '.join(header)
    numbers = re.findall(r'\d+', header_text)
    numbers = [int(num) for num in numbers]
    
    return header,header_text, numbers

def process_constituency_name(header):
    text = re.sub(r'Assembly Constituency No and Name\s*|\s*Part No\s*\d+', '', header)
    text = re.sub(r'\d+', '', text)
    return text.strip()

def process_constituency_part(j,firstNumber, firstHeader, header_text):
    partPattern = r'Part\s*no?\s*(\d+)'
    match = re.search(partPattern, header_text,re.IGNORECASE)
    constituency_No = firstNumber
    if match:
        part_No = int(match.group(1))
    else :
        j+1
    constituency_Name = process_constituency_name(firstHeader)
    j=j-1
    return j, constituency_No,part_No, constituency_Name



def process_section_name(text,constituency_No, ward_No, part_No):
    text = re.sub(r'Section No and Name\s*|\s*wd\d*|\s*WARD NO|\s*Ward|\s*WNO\s*\d*', '', text,re.IGNORECASE)
    numbers_to_remove =[int(constituency_No),int(part_No),int(ward_No)]
    numbers_pattern = r'\b(' + '|'.join(map(str, numbers_to_remove)) + r')\b'
    text = re.sub(numbers_pattern, '', text)
    return text.strip()

def process_sections(sections, part_No, ward_No, constituency_No, constituency_Name, section_Name):
    all_voters = []
    total_voter_ids =0
    for section in sections:
        if(len(section)>500):
            subSections = re.split(r'\n\s*(?=\w{1,4}\s+\w{1,4}\d{6,9}[\)\.,\s]?\s*)', section)
            if len(subSections)==1:
                subSections = re.split(r'\n\s*(?=\w{1,4}\d{6,9}[\)\.,\s]?\s*)', section)
            for subSection in subSections:
                if(len(subSection)>100 and subSection != subSections[0]):
                    sections.append(subSection)

        pattern = r'^\s*(\d{1,4}|\w{1,4})\s+'
        section = re.sub(pattern, '', section)
        section=  re.sub(r'\n\s*\n', '\n', section)
        voters = parse_voter_section(section, part_No, ward_No, constituency_No,constituency_Name, section_Name)
        if voters:
            all_voters.extend(voters)
        else:
            voter_id_pattern = r'\b\w{1,4}\d{6,9}[\)\.,\s]?\s*'
            if (len(re.findall(voter_id_pattern, section))!=0):
                total_voter_ids= total_voter_ids+len(re.findall(voter_id_pattern, section))
    return all_voters, total_voter_ids

def split_section(cleaned_text):
    sections = re.split(r'\n(?=(\w\s\d{1,4}|\d{1,4})[\)\.,\s]?\s*)', cleaned_text)
    subSections = re.split(r'\n\s*(?=\w{1,4}\s+\w{1,4}\d{6,9}[\)\.,\s]?\s*)', sections[0])
    if(len(subSections)>1):
        sections.append(subSections[1])
    return sections

def process_missed_voters(filename):
    missed_pages = {
    "filename": filename[:-7],
    "PageNumber": filename[-6:-4]
    }
    return missed_pages

def check_valid_image(header):
    normalized_main = header.replace(" ", "").lower()
    normalized_substring = ("Assembly Constituency No and Name").replace(" ", "").lower()
    isValidImage = normalized_substring in normalized_main

@shared_task
def extract_voter_data(folder_path):
    all_voters = []
    missed_voter_pages=[]

    constituency_No, part_No, constituency_Name = 0, 0, ""
    j = 1
    i=1
    try:
        for filename in os.listdir(folder_path):
            print(i)
            i=i+1
            if filename.endswith(".png") or filename.endswith(".jpg"):
                image_path = os.path.join(folder_path, filename)
                image = Image.open(image_path)
                ocr_text = pytesseract.image_to_string(image)
                cleaned_text = re.sub(r'[^\w\s]', '', ocr_text)
                marker = "Electoral roll updated on"
                pos = cleaned_text.find(marker)
                cleaned_text =cleaned_text[:pos].strip()
                sections = split_section(cleaned_text)
                header, header_text, numbers = process_header(sections[0])
                if isValidImage == False:
                    check_valid_image(header_text)
                
                if j==1:
                    j, constituency_No,part_No, constituency_Name = process_constituency_part(j,numbers[0], header[0],header_text)
                if constituency_No in numbers:
                    numbers.remove(constituency_No)

                if part_No in numbers:
                    numbers.remove(part_No)
                ward_No = ""
                if(len(numbers)>1):
                    ward_No = numbers[1]

                section_Name = ""
                if(len(numbers) > 1):
                    section_Name = process_section_name(header[1],constituency_No, ward_No, part_No)
                
                voters, total_voter_ids = process_sections(sections[1:], part_No, ward_No, constituency_No, constituency_Name, section_Name)
                print("Total voters in ",filename[-6:]," ---->",len(voters))
                all_voters.extend(voters)
                total_voters_perImage = len(voters)
                total_voter_ids_perImage = (len(voters)+total_voter_ids)
                if (total_voter_ids_perImage!=total_voters_perImage):
                    missed_voter_pages.append(process_missed_voters(filename))
        print("total voter : ", len(all_voters))
        voters_json = json.dumps(all_voters, indent=4)
        missedVoterPage = json.dumps(missed_voter_pages, indent=4)


        with open(voter_data_path, "w") as file:
            file.write(voters_json)
        with open(missed_voter_pages_path, "w") as file:
            file.write(missedVoterPage)
        return isValidImage    
    except FileNotFoundError:
        print(f"Folder path not found: {folder_path}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    