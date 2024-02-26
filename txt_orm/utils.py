import linecache


def asciify(text: str) -> str:
    new_string = ''
    for char in text:
        char_lower = char.lower()
        if char_lower in 'àâãá':
            new_string += 'a' if char.islower() else 'A'
            continue
        if char_lower == 'ç':
            new_string += 'c' if char.islower() else 'C'
            continue
        if char_lower in 'éê':
            new_string += 'e' if char.islower() else 'E'
            continue
        if char_lower == 'í':
            new_string += 'i' if char.islower() else 'I'
            continue
        if char_lower in 'óõô':
            new_string += 'o' if char.islower() else 'O'
            continue
        if char_lower in 'úü':
            new_string += 'u' if char.islower() else 'U'
            continue

        new_string += char

    return new_string


def count_lines(filename: str):
    line_count = 0
    while linecache.getline(filename, line_count + 1):
        line_count += 1
    return line_count
