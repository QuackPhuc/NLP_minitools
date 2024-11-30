import re
from difflib import SequenceMatcher

def percentage_similarity(text1, text2):
    try:
        text1 = text1.lower().strip("\n").strip(" ").strip("\t").strip(":;,.+=`~!@#$%^&*()_[]\{\}|\\;\"'<>?/")
        text2 = text2.lower().strip("\n").strip(" ").strip("\t").strip(":;,.+=`~!@#$%^&*()_[]\{\}|\\;\"'<>?/")
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio() * 100
    except ZeroDivisionError:
        return 0

def percentage_chinese(text):
    try:
        pattern = r"[，。o，,。,,.,;]"
        text = text.strip("\n").strip(" ").strip("\t").strip(":;,.+=`~!@#$%^&*()_[]\{\}|\\;\"'<>?/")
        text = re.sub(pattern, "", text)
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        total_chars = len(text)
        return (len(chinese_chars) / total_chars * 100) if total_chars > 0 else 0
    except ZeroDivisionError:
        return 0

def is_vietnamese_word(word: str) -> bool:

    try:
        vietnamese_pattern = re.compile(
                r'^[a-zA-Z0-9àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđAĂÂÁẮẤÀẰẦẢẲẨÃẴẪẠẶẬĐEÊÉẾÈỀẺỂẼỄẸỆIÍÌỈĨỊOÔƠÓỐỚÒỒỜỎỔỞÕỖỠỌỘỢUƯÚỨÙỪỦỬŨỮỤỰYÝỲỶỸỴAĂÂÁẮẤÀẰẦẢẲẨÃẴẪẠẶẬĐEÊÉẾÈỀẺỂẼỄẸỆIÍÌỈĨỊOÔƠÓỐỚÒỒỜỎỔỞÕỖỠỌỘỢUƯÚỨÙỪỦỬŨỮỤỰYÝỲỶỸỴAĂÂÁẮẤÀẰẦẢẲẨÃẴẪẠẶẬĐEÊÉẾÈỀẺỂẼỄẸỆIÍÌỈĨỊOÔƠÓỐỚÒỒỜỎỔỞÕỖỠỌỘỢUƯÚỨÙỪỦỬŨỮỤỰYÝỲỶỸỴAĂÂÁẮẤÀẰẦẢẲẨÃẴẪẠẶẬĐEÊÉẾÈỀẺỂẼỄẸỆIÍÌỈĨỊOÔƠÓỐỚÒỒỜỎỔỞÕỖỠỌỘỢUƯÚỨÙỪỦỬŨỮỤỰYÝỲỶỸỴAĂÂÁẮẤÀẰẦẢẲẨÃẴẪẠẶẬĐEÊÉẾÈỀẺỂẼỄẸỆIÍÌỈĨỊOÔƠÓỐỚÒỒỜỎỔỞÕỖỠỌỘỢUƯÚỨÙỪỦỬŨỮỤỰYÝỲỶỸỴAĂÂÁẮẤÀẰẦẢẲẨÃẴẪẠẶẬĐEÊÉẾÈỀẺỂẼỄẸỆIÍÌỈĨỊOÔƠÓỐỚÒỒỜỎỔỞÕỖỠỌỘỢUƯÚỨÙỪỦỬŨỮỤỰYÝỲỶỸỴ]+$', re.IGNORECASE
            )
        return bool(vietnamese_pattern.match(word))
    except re.error:
        return False

def percentage_vietnamese(sentence: str) -> float:
    try:
        # Loại bỏ ký tự đặc biệt, giữ lại từ
        cleaned_sentence = re.sub(r'[^\w\s]', '', sentence).lower()
        print(cleaned_sentence)
        words = cleaned_sentence.split()
        if not words:
            return 0.0
        # Đếm số từ chứa ký tự tiếng Việt
        vietnamese_count = sum(1 for word in words if is_vietnamese_word(word))
        # Tính tỷ lệ phần trăm
        percentage = (vietnamese_count / len(words)) * 100
        
        return percentage
    except ZeroDivisionError:
        return 0.0

def is_number(line: str) -> bool:
    try:
        # Loại bỏ khoảng trắng và kiểm tra nếu rỗng
        stripped_line = line.strip()
        if not stripped_line:
            return False
        # Chuyển chuỗi thành số (int hoặc float)
        float(stripped_line)
        return True
    except ValueError:
        return False

def is_uppercase(line: str) -> bool:
    try:
        # Loại bỏ khoảng trắng đầu và cuối dòng
        stripped_line = line.strip()
        
        # Kiểm tra xem chuỗi có ký tự chữ và tất cả đều viết hoa
        return stripped_line.isupper()
    except AttributeError:
        return False

import re

def clean_sentence(sentence):
    """
    Clean the input sentence by:
    - Removing numbers
    - Removing extra spaces
    - Correcting misplaced punctuation
    - Removing special characters likely to appear due to OCR errors
    - Removing invalid patterns like ([only one character]) or ([only one number])
    """
    # Replace ª with a space
    sentence = sentence.replace(" ª ", " ")

    # Remove numbers
    sentence = re.sub(r'\d+', '', sentence)

    # Replace multiple spaces with a single space
    sentence = re.sub(r'\s+', ' ', sentence)

    # Remove special characters often misrecognized by OCR

    # Fix misplaced punctuation
    sentence = sentence.replace(" ,", ",")  # Fix spaces before comma
    sentence = sentence.replace(" .", ".")  # Fix spaces before period
    sentence = sentence.replace(" ?", "?")  # Fix spaces before question mark
    sentence = sentence.replace(" !", "!")  # Fix spaces before exclamation mark
    sentence = sentence.replace(" '", "'")  # Fix spaces before apostrophe
    sentence = sentence.replace(" -", "-")  # Fix spaces before dash
    sentence = sentence.replace("- ", "-")  # Fix spaces after dash

    # Remove ([only one character]) or ([only one number])
    sentence = re.sub(r'\(\s?[a-zA-Z0-9]\s?\)', '', sentence)

    # Check if the sentence contains mismatched parentheses or quotes
    if (sentence.count('(') != sentence.count(')')) or (sentence.count('"') % 2 != 0):
        sentence = sentence.replace('(', '').replace(')', '').replace('"', '')
    
    sentence = sentence.replace("()", "")  # Fix double spaces

    # Trim spaces at the beginning and end
    sentence = sentence.strip()

    return sentence


a = "(kỳ kỳ) (1)"
print(clean_sentence(a))