import argparse
import textwrap

def parse_srt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    parsed_subtitles = []
    buffer = []
    
    for line in lines:
        if line.strip().isdigit():
            if buffer:
                parsed_subtitles.append(' '.join(buffer).strip())
                buffer = []
            parsed_subtitles.append(line.strip())
        elif '-->' in line:
            parsed_subtitles.append(line.strip())
        else:
            buffer.append(line.strip())
    
    if buffer:
        parsed_subtitles.append(' '.join(buffer).strip())
    
    return parsed_subtitles

def process_subtitle(text):
    if len(text) > 50:
        wrapped = textwrap.wrap(text, width=50, max_lines=2)
        return '\n'.join(wrapped)
    return text

def process_srt(parsed_subtitles):
    processed = []
    for i in range(0, len(parsed_subtitles), 3):
        processed.append(parsed_subtitles[i])
        processed.append(parsed_subtitles[i+1])
        processed.append(process_subtitle(parsed_subtitles[i+2]))
    return processed

def write_output(output_path, processed_subtitles):
    with open(output_path, 'w', encoding='utf-8') as file:
        for i, line in enumerate(processed_subtitles):
            if line.strip().isdigit() and i > 0:
                file.write('\n')
            file.write(line + '\n')

def main():
    parser = argparse.ArgumentParser(description="Process .srt file and format subtitles.")
    parser.add_argument("input", help="Path to the input .srt file")
    parser.add_argument("output", help="Path to save the processed .srt file")
    
    args = parser.parse_args()
    
    parsed_subtitles = parse_srt(args.input)
    processed_subtitles = process_srt(parsed_subtitles)
    write_output(args.output, processed_subtitles)

if __name__ == "__main__":
    main()
