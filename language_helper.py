import re
from fuzzywuzzy import fuzz
from unicodedata import normalize


def percentage_similarity(text1: str, text2: str) -> float:
    """
    Tính tỷ lệ giống nhau giữa các chuỗi với token-based fuzzy matching.
    """
    try:
        # Chuẩn hóa Unicode và loại bỏ dấu tiếng Việt
        def preprocess_text(text):
            text = normalize('NFC', text.lower().strip())
            text = re.sub(r"[\s:;,.+=`~!@#$%^&*()\[\]{}|\\\"'<>?/]", '', text)  # Loại bỏ ký tự đặc biệt
            return text

        text1 = preprocess_text(text1)
        text2 = preprocess_text(text2)

        # Sử dụng fuzz.token_set_ratio để đo độ tương đồng
        return fuzz.token_set_ratio(text1, text2)
    except Exception as e:
        print(f"Error in percentage_similarity_tokens: {e}")
        return 0.0


def percentage_chinese(text: str) -> float:
    """
    Tính phần trăm ký tự tiếng Trung trong chuỗi đầu vào.
    """
    try:
        text = normalize('NFC', text.strip())
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        total_chars = len(text.replace(" ", ""))
        return round((len(chinese_chars) / total_chars) * 100, 2) if total_chars > 0 else 0.0
    except Exception as e:
        print(f"Error in percentage_chinese: {e}")
        return 0.0

def is_vietnamese_word(word: str) -> bool:
    """
    Kiểm tra xem từ có chứa các ký tự tiếng Việt hợp lệ không.
    """
    try:
        vietnamese_pattern = re.compile(
            r'^[a-zA-Z0-9àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+$',
            re.IGNORECASE
        )
        return bool(vietnamese_pattern.match(word))
    except Exception as e:
        print(f"Error in is_vietnamese_word: {e}")
        return False

def percentage_vietnamese(sentence: str) -> float:
    """
    Tính phần trăm từ tiếng Việt hợp lệ trong một câu.
    """
    try:
        cleaned_sentence = re.sub(r'[^\w\s]', '', normalize('NFC', sentence)).lower()
        words = cleaned_sentence.split()
        if not words:
            return 0.0
        vietnamese_count = sum(1 for word in words if is_vietnamese_word(word))
        return round((vietnamese_count / len(words)) * 100, 2)
    except Exception as e:
        print(f"Error in percentage_vietnamese: {e}")
        return 0.0

def is_number(line: str) -> bool:
    """
    Kiểm tra xem chuỗi có phải là số không (hỗ trợ số nguyên và số thực).
    """
    try:
        stripped_line = line.strip()
        if not stripped_line:
            return False
        float(stripped_line)  # Kiểm tra có thể chuyển thành float
        return True
    except ValueError:
        return False

def is_uppercase(line: str) -> bool:
    """
    Kiểm tra xem chuỗi có được viết hoa hoàn toàn không.
    """
    try:
        stripped_line = line.strip()
        return stripped_line.isupper() and any(c.isalpha() for c in stripped_line)
    except Exception as e:
        print(f"Error in is_uppercase: {e}")
        return False

def clean_sentence(sentence: str) -> str:
    """
    Làm sạch câu bằng cách loại bỏ ký tự không cần thiết, xử lý dấu câu và ký tự đặc biệt.
    """
    try:
        sentence = normalize('NFC', sentence)
        sentence = re.sub(r'\d+', '', sentence)  # Loại bỏ số
        sentence = re.sub(r'\s+', ' ', sentence)  # Loại bỏ khoảng trắng thừa
        sentence = sentence.strip()

        # Sửa lỗi dấu câu
        punctuation_fixes = [
            (r'\s,', ','), (r'\s\.', '.'), (r'\s\?', '?'), (r'\s!', '!'),
            (r"\s'", "'"), (r'\s-', '-'), (r'-\s', '-')
        ]
        for pattern, replacement in punctuation_fixes:
            sentence = re.sub(pattern, replacement, sentence)

        # Xử lý cặp ngoặc không hợp lệ
        if sentence.count('(') != sentence.count(')') or sentence.count('"') % 2 != 0:
            sentence = sentence.replace('(', '').replace(')', '').replace('"', '')

        sentence = sentence.replace("()", "")  # Loại bỏ ngoặc rỗng
        return sentence.strip()
    except Exception as e:
        print(f"Error in clean_sentence: {e}")
        return sentence
