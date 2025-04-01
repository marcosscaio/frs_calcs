def get_age_interval(age):
    if 30 <= age <= 34:
        return "30-34"
    elif 35 <= age <= 39:
        return "35-39"
    elif 40 <= age <= 44:
        return "40-44"
    elif 45 <= age <= 49:
        return "45-49"
    elif 50 <= age <= 54:
        return "50-54"
    elif 55 <= age <= 59:
        return "55-59"
    elif 60 <= age <= 64:
        return "60-64"
    elif 65 <= age <= 69:
        return "65-69"
    elif 70 <= age <= 74:
        return "70-74"
    elif age >= 75:
        return "&ge;75"
    else:
        return None

def get_totChol_interval(chol):
    if chol < 160:
        return "&lt;4.14 mmol/L"
    elif 160 <= chol <= 199:
        return "4.14-5.15 mmol/L"
    elif 200 <= chol <= 239:
        return "5.16-6.19 mmol/L"
    elif 240 <= chol <= 279:
        return "6.20-7.24 mmol/L"
    else:
        return "&ge;7.25 mmol/L"

def get_sysBP_interval(bp):
    if bp < 120:
        return "&lt;120 mmHg"
    elif 120 <= bp <= 129:
        return "120-129 mmHg"
    elif 130 <= bp <= 139:
        return "130-139 mmHg"
    elif 140 <= bp <= 149:
        return "140-149 mmHg"
    elif 150 <= bp <= 159:
        return "150-159 mmHg"
    else:
        return ">=&ge;160 mmHg"

def map_binary(value):
    return "Yes" if int(value) == 1 else "No"