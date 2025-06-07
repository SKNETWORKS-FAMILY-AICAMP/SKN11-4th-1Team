from django import template



register = template.Library()



@register.filter(name='split')
def split(value, arg):
    """
    문자열을 구분자로 나누어 리스트로 반환
    사용법: {{ string|split:"," }}
    """
    if value:
        return value.split(arg)
    return []

@register.filter(name='trim')
def trim(value):
    """
    문자열의 앞뒤 공백 제거
    사용법: {{ string|trim }}
    """
    if value:
        return value.strip()
    return value
