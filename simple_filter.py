from language_helper import (
    percentage_chinese, percentage_similarity, percentage_vietnamese,
    is_number, clean_sentence, is_uppercase
)

def only_text(data):
    results = [[]]
    for entry in data:
        results = entry.get("result", {})
        lines = results.get("lines", [])
        for line in lines:
            text = line.get("text", "").strip() # basic config
            if not text:
                continue
            results[0].append(text)
    return results

def simple(data):
    res = [[], [], []]
    for entry in data:
        results = entry.get("result", {})
        lines = results.get("lines", [])
        for index, line in enumerate(lines):
            text = line.get("text", "").strip() # basic config
            box = line.get("boundingPolygon", [])
            if not text:
                continue
            res[0].append(entry.get("page_index", ""))
            res[1].append(box)
            res[2].append(text)
    return res

def simple_chinese(data):
    res = [[], [], []]
    for entry in data:
        results = entry.get("result", {})
        lines = results.get("lines", [])
        for index, line in enumerate(lines):
            text = line.get("text", "")
            if percentage_chinese(text) < 70:
                continue
            box = line.get("boundingPolygon", [])
            if not text:
                continue
            res[0].append(entry.get("page_index", ""))
            res[1].append(box)
            res[2].append(text)
    return res

def only_phien_am(data, med = "inf", leng = "inf", threshold = 2):
    res = [[]]
    for entry in data:
        results = entry.get("result", {})
        lines = results.get("lines", [])
        is_phien_am = False
        for index, line in enumerate(lines):
            text = line.get("text", "")
            if not text:
                continue
            if not is_phien_am and percentage_similarity(text, "phien am") > 70:
                is_phien_am = True
            elif is_phien_am and percentage_vietnamese(text) > 70:
                if percentage_similarity(text, "dich nghia") > 70:
                    return res
                elif percentage_similarity(text, "dich tho") > 70:
                    return res
                elif len(text.split()) > med: # loại bỏ phần chữ thừa, thường là chú thích
                    return res
                elif med != float("inf") and len(text.split()) / med > threshold:
                    return res
                elif leng != float("inf") and len(text.split()) > leng:
                    return res
                else:
                    res[0].append(text)
    return res