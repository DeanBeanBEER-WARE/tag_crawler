
import requests
from bs4 import BeautifulSoup

def get_headings(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    headings = {}
    for i in range(1, 7):
        tag = f'h{i}'
        headings[tag] = [heading.get_text(strip=True) for heading in soup.find_all(tag)]
    
    return headings

def print_headings_tree(headings, file):
    with open(file, 'w') as f:
        for i in range(1, 7):
            tag = f'h{i}'
            if headings[tag]:
                f.write(f'{tag.upper()}:\n')
                for heading in headings[tag]:
                    f.write(f'  {"  " * (i-1)}- {heading}\n')

if __name__ == "__main__":
    url = input("Enter the URL of the webpage: ")
    headings = get_headings(url)
    output_file = "headings_structure.txt"
    print_headings_tree(headings, output_file)
    print(f"Headings structure saved to {output_file}")
